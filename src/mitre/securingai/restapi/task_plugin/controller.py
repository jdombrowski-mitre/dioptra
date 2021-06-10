# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""The module defining the task plugin endpoints."""

import uuid
from typing import List, Optional

import structlog
from flask import current_app, jsonify
from flask.wrappers import Response
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.utils import as_api_parser

from .errors import TaskPluginDoesNotExistError, TaskPluginUploadError
from .model import TaskPlugin, TaskPluginUploadForm, TaskPluginUploadFormData
from .schema import TaskPluginSchema, TaskPluginUploadSchema
from .service import TaskPluginService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace(
    "TaskPlugin",
    description="Task plugin registry operations",
)


@api.route("/")
class TaskPluginResource(Resource):
    """Shows a list of all task plugins, and lets you POST to upload new ones."""

    @inject
    def __init__(self, *args, task_plugin_service: TaskPluginService, **kwargs) -> None:
        self._task_plugin_service = task_plugin_service
        super().__init__(*args, **kwargs)

    @responds(schema=TaskPluginSchema(many=True), api=api)
    def get(self) -> List[TaskPlugin]:
        """Gets a list of all registered task plugins."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="taskPlugin", request_type="GET"
        )
        log.info("Request received")
        return self._task_plugin_service.get_all(
            bucket=current_app.config["AI_PLUGINS_BUCKET"], log=log
        )

    @api.expect(as_api_parser(api, TaskPluginUploadSchema))
    @accepts(TaskPluginUploadSchema, api=api)
    @responds(schema=TaskPluginSchema, api=api)
    def post(self) -> TaskPlugin:
        """Registers a new task plugin uploaded via the task plugin upload form."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="taskPlugin", request_type="POST"
        )
        task_plugin_upload_form: TaskPluginUploadForm = TaskPluginUploadForm()

        log.info("Request received")

        if not task_plugin_upload_form.validate_on_submit():
            log.error("Form validation failed")
            raise TaskPluginUploadError

        log.info("Form validation successful")
        task_plugin_upload_form_data: TaskPluginUploadFormData = (
            self._task_plugin_service.extract_data_from_form(
                task_plugin_upload_form=task_plugin_upload_form, log=log
            )
        )
        return self._task_plugin_service.create(
            task_plugin_upload_form_data=task_plugin_upload_form_data,
            bucket=current_app.config["AI_PLUGINS_BUCKET"],
            log=log,
        )


@api.route("/securingai_builtins")
class TaskPluginBuiltinsCollectionResource(Resource):
    """Shows a list of all builtin task plugins."""

    @inject
    def __init__(self, *args, task_plugin_service: TaskPluginService, **kwargs) -> None:
        self._task_plugin_service = task_plugin_service
        super().__init__(*args, **kwargs)

    @responds(schema=TaskPluginSchema(many=True), api=api)
    def get(self) -> List[TaskPlugin]:
        """Gets a list of all available builtin task plugins."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginBuiltinCollection",
            request_type="GET",
        )
        log.info("Request received")
        return self._task_plugin_service.get_all_in_collection(
            collection="securingai_builtins",
            bucket=current_app.config["AI_PLUGINS_BUCKET"],
            log=log,
        )


@api.route("/securingai_builtins/<string:taskPluginName>")
@api.param(
    "taskPluginName",
    "A unique string identifying a task plugin package within securingai_builtins "
    "collection.",
)
class TaskPluginBuiltinCollectionNameResource(Resource):
    """Shows a single builtin task plugin package."""

    @inject
    def __init__(self, *args, task_plugin_service: TaskPluginService, **kwargs) -> None:
        self._task_plugin_service = task_plugin_service
        super().__init__(*args, **kwargs)

    @responds(schema=TaskPluginSchema, api=api)
    def get(self, taskPluginName: str) -> TaskPlugin:
        """Gets a builtin task plugin by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginBuiltinCollectionName",
            request_type="GET",
        )
        log.info("Request received")

        task_plugin: Optional[
            TaskPlugin
        ] = self._task_plugin_service.get_by_name_in_collection(
            collection="securingai_builtins",
            task_plugin_name=taskPluginName,
            bucket=current_app.config["AI_PLUGINS_BUCKET"],
            log=log,
        )

        if task_plugin is None:
            log.error(
                "TaskPlugin not found",
                task_plugin_name=taskPluginName,
                collection="securingai_builtins",
            )
            raise TaskPluginDoesNotExistError

        return task_plugin


@api.route("/securingai_custom")
class TaskPluginCustomCollectionResource(Resource):
    """Shows a list of all custom task plugins."""

    @inject
    def __init__(self, *args, task_plugin_service: TaskPluginService, **kwargs) -> None:
        self._task_plugin_service = task_plugin_service
        super().__init__(*args, **kwargs)

    @responds(schema=TaskPluginSchema(many=True), api=api)
    def get(self) -> List[TaskPlugin]:
        """Gets a list of all registered custom task plugins."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginCustomCollection",
            request_type="GET",
        )
        log.info("Request received")
        return self._task_plugin_service.get_all_in_collection(
            collection="securingai_custom",
            bucket=current_app.config["AI_PLUGINS_BUCKET"],
            log=log,
        )


@api.route("/securingai_custom/<string:taskPluginName>")
@api.param(
    "taskPluginName",
    "A unique string identifying a task plugin package within securingai_custom "
    "collection.",
)
class TaskPluginCustomCollectionNameResource(Resource):
    """Shows a single custom task plugin package and lets you delete it."""

    @inject
    def __init__(self, *args, task_plugin_service: TaskPluginService, **kwargs) -> None:
        self._task_plugin_service = task_plugin_service
        super().__init__(*args, **kwargs)

    @responds(schema=TaskPluginSchema, api=api)
    def get(self, taskPluginName: str) -> TaskPlugin:
        """Gets a custom task plugin by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginCustomCollectionName",
            request_type="GET",
        )
        log.info("Request received")

        task_plugin: Optional[
            TaskPlugin
        ] = self._task_plugin_service.get_by_name_in_collection(
            collection="securingai_custom",
            task_plugin_name=taskPluginName,
            bucket=current_app.config["AI_PLUGINS_BUCKET"],
            log=log,
        )

        if task_plugin is None:
            log.error(
                "TaskPlugin not found",
                task_plugin_name=taskPluginName,
                collection="securingai_custom",
            )
            raise TaskPluginDoesNotExistError

        return task_plugin

    def delete(self, taskPluginName: str) -> Response:
        """Deletes a custom task plugin by its unique name."""
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="taskPluginCustomCollectionName",
            task_plugin_name=taskPluginName,
            request_type="DELETE",
        )
        log.info("Request received")

        task_plugins: List[TaskPlugin] = self._task_plugin_service.delete(
            collection="securingai_custom",
            task_plugin_name=taskPluginName,
            bucket=current_app.config["AI_PLUGINS_BUCKET"],
            log=log,
        )
        name: List[str] = [x.task_plugin_name for x in task_plugins]

        return jsonify(  # type: ignore
            dict(status="Success", collection="securingai_custom", taskPluginName=name)
        )
