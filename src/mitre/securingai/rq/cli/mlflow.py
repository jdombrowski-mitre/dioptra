#!/usr/bin/env python
# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import os

from mlflow.cli import cli as mlflow_cli

from mitre.securingai.sdk.utilities.logging import (
    attach_stdout_stream_handler,
    configure_structlog,
    set_logging_level,
)

if __name__ == "__main__":
    attach_stdout_stream_handler(
        True if os.getenv("AI_MLFLOW_RUN_LOG_AS_JSON") else False,
    )
    set_logging_level(os.getenv("AI_MLFLOW_RUN_LOG_LEVEL", default="INFO"))
    configure_structlog()
    mlflow_cli()
