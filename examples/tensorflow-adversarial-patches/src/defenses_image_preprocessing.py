# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

import mlflow
import numpy as np
import pandas as pd
import scipy.stats
import structlog
from prefect import task
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.exceptions import (
    ARTDependencyError,
    TensorflowDependencyError,
)
from mitre.securingai.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from art.defences.preprocessor import (
        GaussianAugmentation,
        JpegCompression,
        SpatialSmoothing,
    )
    from art.estimators.classification import KerasClassifier

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="art",
    )


try:
    from tensorflow.keras.preprocessing.image import ImageDataGenerator, save_img

except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="tensorflow",
    )

DEFENSE_LIST = {
    "spatial_smoothing": SpatialSmoothing,
    "jpeg_compression": JpegCompression,
    "gaussian_augmentation": GaussianAugmentation,
}


def get_optimizer(optimizer, learning_rate):
    optimizer_collection = {
        "rmsprop": RMSprop(learning_rate),
        "adam": Adam(learning_rate),
        "adagrad": Adagrad(learning_rate),
        "sgd": SGD(learning_rate),
    }

    return optimizer_collection.get(optimizer)


# Load model from registry and apply imagenet_preprocessing if needed.
def wrap_keras_classifier(model, clip_values, imagenet_preprocessing):
    keras_model = load_model_in_registry(model=model)
    if imagenet_preprocessing:
        mean_b = 103.939
        mean_g = 116.779
        mean_r = 123.680
        return KerasClassifier(
            model=keras_model,
            clip_values=clip_values,
            preprocessing=([mean_b, mean_g, mean_r], 1),
        )
    else:
        return KerasClassifier(model=keras_model, clip_values=clip_values)


def init_defense(clip_values, def_type, **kwargs):

    defense = DEFENSE_LIST[def_type](
        clip_values=clip_values,
        **kwargs,
    )

    return defense


def save_def_batch(def_batch, def_data_dir, y, clean_filenames, class_names_list):
    for batch_image_num, def_image in enumerate(def_batch):
        out_label = class_names_list[y[batch_image_num]]
        def_image_path = (
            def_data_dir
            / f"{out_label}"
            / f"def_{clean_filenames[batch_image_num].name}"
        )

        if not def_image_path.parent.exists():
            def_image_path.parent.mkdir(parents=True)

        save_img(path=str(def_image_path), x=def_image)


def evaluate_distance_metrics(
    clean_filenames, distance_metrics_, clean_batch, def_batch
):
    LOGGER.debug("evaluate image perturbations using distance metrics")
    distance_metrics_["image"].extend([x.name for x in clean_filenames])
    distance_metrics_["label"].extend([x.parent for x in clean_filenames])
    for metric_name, metric in DISTANCE_METRICS:
        distance_metrics_[metric_name].extend(metric(clean_batch, def_batch))


def log_distance_metrics(distance_metrics_):
    distance_metrics_ = distance_metrics_.copy()
    del distance_metrics_["image"]
    del distance_metrics_["label"]
    for metric_name, metric_values_list in distance_metrics_.items():
        metric_values = np.array(metric_values_list)
        mlflow.log_metric(key=f"{metric_name}_mean", value=metric_values.mean())
        mlflow.log_metric(key=f"{metric_name}_median", value=np.median(metric_values))
        mlflow.log_metric(key=f"{metric_name}_stdev", value=metric_values.std())
        mlflow.log_metric(
            key=f"{metric_name}_iqr", value=scipy.stats.iqr(metric_values)
        )
        mlflow.log_metric(key=f"{metric_name}_min", value=metric_values.min())
        mlflow.log_metric(key=f"{metric_name}_max", value=metric_values.max())
        LOGGER.info("logged distance-based metric", metric_name=metric_name)


@task
@require_package("art", exc_type=ARTDependencyError)
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def create_defended_dataset(
    data_dir: str,
    def_data_dir: Union[str, Path],
    image_size: Tuple[int, int, int],
    distance_metrics_list: Optional[List[Tuple[str, Callable[..., np.ndarray]]]] = None,
    batch_size: int = 32,
    label_mode: str = "categorical",
    def_type: str = "spatial_smoothing",
    **kwargs,
) -> pd.DataFrame:
    distance_metrics_list = distance_metrics_list or []
    color_mode: str = "rgb" if image_size[2] == 3 else "grayscale"
    rescale: float = 1.0 if image_size[2] == 3 else 1.0 / 255
    clip_values: Tuple[float, float] = (0, 255) if image_size[2] == 3 else (0, 1.0)
    target_size: Tuple[int, int] = image_size[:2]
    def_data_dir = Path(def_data_dir)

    defense = init_defense(
        clip_values=clip_values,
        def_type=def_type,
        **kwargs,
    )

    data_generator: ImageDataGenerator = ImageDataGenerator(rescale=rescale)

    data_flow = data_generator.flow_from_directory(
        directory=data_dir,
        target_size=target_size,
        color_mode=color_mode,
        class_mode=label_mode,
        batch_size=batch_size,
        shuffle=False,
    )
    n_classes = len(data_flow.class_indices)
    num_images = data_flow.n
    img_filenames = [Path(x) for x in data_flow.filenames]
    class_names_list = sorted(data_flow.class_indices, key=data_flow.class_indices.get)

    distance_metrics_: Dict[str, List[List[float]]] = {"image": [], "label": []}
    for metric_name, _ in distance_metrics_list:
        distance_metrics_[metric_name] = []

    LOGGER.info(
        "Generate defended images",
        defense=def_type,
        num_batches=num_images // batch_size,
    )

    for batch_num, (x, y) in enumerate(data_flow):
        if batch_num >= num_images // batch_size:
            break

        clean_filenames = img_filenames[
            batch_num * batch_size : (batch_num + 1) * batch_size  # noqa: E203
        ]

        LOGGER.info(
            "Generate defended image batch",
            defense=def_type,
            batch_num=batch_num,
        )

        y_int = np.argmax(y, axis=1)
        adv_batch_defend, _ = defense(x)

        _save_def_batch(
            adv_batch_defend, def_data_dir, y_int, clean_filenames, class_names_list
        )

        _evaluate_distance_metrics(
            clean_filenames=clean_filenames,
            distance_metrics_=distance_metrics_,
            clean_batch=x,
            adv_batch=adv_batch_defend,
            distance_metrics_list=distance_metrics_list,
        )

    LOGGER.info("Defended image generation complete", defense=def_type)
    _log_distance_metrics(distance_metrics_)

    return pd.DataFrame(distance_metrics_)


def init_defense(clip_values, def_type, **kwargs):
    defense = DEFENSE_LIST[def_type](
        clip_values=clip_values,
        **kwargs,
    )
    return defense


def _save_def_batch(
    adv_batch, def_data_dir, y, clean_filenames, class_names_list
) -> None:
    for batch_image_num, adv_image in enumerate(adv_batch):
        out_label = class_names_list[y[batch_image_num]]
        adv_image_path = (
            def_data_dir
            / f"{out_label}"
            / f"def_{clean_filenames[batch_image_num].name}"
        )

        if not adv_image_path.parent.exists():
            adv_image_path.parent.mkdir(parents=True)

        save_img(path=str(adv_image_path), x=adv_image)


def _evaluate_distance_metrics(
    clean_filenames, distance_metrics_, clean_batch, adv_batch, distance_metrics_list
) -> None:
    LOGGER.debug("evaluate image perturbations using distance metrics")
    distance_metrics_["image"].extend([x.name for x in clean_filenames])
    distance_metrics_["label"].extend([x.parent for x in clean_filenames])
    for metric_name, metric in distance_metrics_list:
        distance_metrics_[metric_name].extend(metric(clean_batch, adv_batch))


def _log_distance_metrics(distance_metrics_: Dict[str, List[List[float]]]) -> None:
    distance_metrics_ = distance_metrics_.copy()
    del distance_metrics_["image"]
    del distance_metrics_["label"]
    for metric_name, metric_values_list in distance_metrics_.items():
        metric_values = np.array(metric_values_list)
        mlflow.log_metric(key=f"{metric_name}_mean", value=metric_values.mean())
        mlflow.log_metric(key=f"{metric_name}_median", value=np.median(metric_values))
        mlflow.log_metric(key=f"{metric_name}_stdev", value=metric_values.std())
        mlflow.log_metric(
            key=f"{metric_name}_iqr", value=scipy.stats.iqr(metric_values)
        )
        mlflow.log_metric(key=f"{metric_name}_min", value=metric_values.min())
        mlflow.log_metric(key=f"{metric_name}_max", value=metric_values.max())
        LOGGER.info("logged distance-based metric", metric_name=metric_name)
