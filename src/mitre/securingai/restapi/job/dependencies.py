# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""Binding configurations to shared services using dependency injection."""

import os
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from boto3.session import Session
from botocore.client import BaseClient
from flask_injector import request
from injector import Binder, Module, provider
from redis import Redis

from mitre.securingai.restapi.shared.rq.service import RQService


@dataclass
class RQServiceConfiguration(object):
    redis: Redis
    run_mlflow: str


class RQServiceModule(Module):
    @request
    @provider
    def provide_rq_service_module(
        self, configuration: RQServiceConfiguration
    ) -> RQService:
        return RQService(redis=configuration.redis, run_mlflow=configuration.run_mlflow)


def _bind_rq_service_configuration(binder: Binder):
    redis_conn: Redis = Redis.from_url(os.getenv("RQ_REDIS_URI", "redis://"))
    run_mlflow: str = "mitre.securingai.rq.tasks.run_mlflow_task"

    configuration: RQServiceConfiguration = RQServiceConfiguration(
        redis=redis_conn,
        run_mlflow=run_mlflow,
    )

    binder.bind(RQServiceConfiguration, to=configuration, scope=request)


def _bind_s3_service_configuration(binder: Binder) -> None:
    s3_endpoint_url: Optional[str] = os.getenv("MLFLOW_S3_ENDPOINT_URL")

    s3_session: Session = Session()
    s3_client: BaseClient = s3_session.client("s3", endpoint_url=s3_endpoint_url)

    binder.bind(Session, to=s3_session, scope=request)
    binder.bind(BaseClient, to=s3_client, scope=request)


def bind_dependencies(binder: Binder) -> None:
    """Binds interfaces to implementations within the main application.

    Args:
        binder: A :py:class:`~injector.Binder` object.
    """
    _bind_rq_service_configuration(binder)
    _bind_s3_service_configuration(binder)


def register_providers(modules: List[Callable[..., Any]]) -> None:
    """Registers type providers within the main application.

    Args:
        modules: A list of callables used for configuring the dependency injection
            environment.
    """
    modules.append(RQServiceModule)
