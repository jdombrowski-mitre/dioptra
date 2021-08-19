# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
import os
import shutil
from pathlib import Path

import mlflow
import tensorflow as tf
import yaml

TARGET_FILES = set(["conda.yaml", "MLmodel", "keras_module.txt", "save_format.txt"])


def migrate_s3(root_dir):
    shutil.copytree(src=str(root_dir / "old"), dst=str(root_dir / "new"))
    migration_dir = str(root_dir / "new")
    model_paths = _extract_model_paths(migration_dir)
    _update_model_h5_files(model_paths)


def _extract_model_paths(s3_path):
    model_paths = []
    s3_artifact_path = s3_path + "/mlflow-tracking/artifacts/"
    for dirname, dirnames, filenames in os.walk(s3_artifact_path):
        for subdirname in dirnames:
            path = os.path.join(dirname, subdirname)
            if "model" == path[-5:]:
                model_paths.append(path)
    return model_paths


def _update_model_h5_files(model_paths):
    for model_path in model_paths:
        model_mlfile_contents_updated = ""
        is_tensorflow = False
        with open(model_path + "/MLmodel", "r") as model_mlfile:
            model_mlfile_contents = model_mlfile.read()
            is_tensorflow = "tensorflow_core" in model_mlfile_contents

        if is_tensorflow and os.path.isfile(model_path + "/data/model.h5"):
            model = tf.keras.models.load_model(model_path + "/data/model.h5")

            shutil.rmtree(model_path)

            mlflow.keras.save_model(model, model_path)


def _dump_yaml_file(obj, filepath):
    with open(filepath, "w") as f:
        yaml.dump(data=obj, stream=f, Dumper=yaml.Dumper)


def _load_yaml_file(filepath):
    with open(filepath, "r") as f:
        data = yaml.load(f, Loader=yaml.Loader)

    return data


def _find_files(root_dir, target_filenames):
    filepaths = {}

    for dirpath, _, filenames in os.walk(root_dir):
        captured_filenames = [x for x in filenames if x in target_filenames]

        for filename in captured_filenames:
            filepaths[filename] = Path(dirpath) / filename

    return filepaths


def _update_save_format(filepath):
    with open(filepath, "wt") as f:
        f.write("h5")


def _update_keras_module(filepath):
    with open(filepath, "wt") as f:
        f.write("tensorflow.keras")


def _update_mlmodel_yaml(filepath):
    mlmodel_yaml = _load_yaml_file(filepath)
    mlmodel_yaml["flavors"]["keras"]["keras_module"] = "tensorflow.keras"
    mlmodel_yaml["flavors"]["keras"]["keras_version"] = "2.4.0"
    mlmodel_yaml["flavors"]["python_function"]["python_version"] = "3.9"
    _dump_yaml_file(mlmodel_yaml, filepath)


def _update_conda_yaml(filepath):
    conda_yaml = _load_yaml_file(filepath)
    dependencies = conda_yaml["dependencies"]

    dependencies_new = []
    for dep in dependencies:
        if isinstance(dep, str) and "python" in dep:
            dependencies_new.append("python=3.9")

        elif isinstance(dep, dict):
            dependencies_new.append(
                {
                    "pip": [
                        "tensorflow==2.4.1" if "tensorflow" in x else x
                        for x in dep["pip"]
                    ]
                }
            )

        else:
            dependencies_new.append(dep)

    conda_yaml["dependencies"] = dependencies_new

    _dump_yaml_file(conda_yaml, filepath)
