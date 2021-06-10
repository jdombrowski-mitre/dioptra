# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import importlib
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, cast

import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.sdk.exceptions.base import BaseOptionalDependencyError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

Exc = Type[BaseOptionalDependencyError]
Function = Callable[..., Any]
T = TypeVar("T", bound=Function)


def require_package(
    name: str,
    exc_message: Optional[str] = None,
    exc_type: Exc = BaseOptionalDependencyError,
) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        error_msg: str = f'The package "{name}" is required to use {func.__name__}'
        exc: BaseOptionalDependencyError = (
            exc_type(exc_message) if exc_message else exc_type(error_msg)
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                importlib.import_module(name=name)

            except ModuleNotFoundError:
                LOGGER.exception(error_msg, args=args, kwargs=kwargs)
                raise exc

            return func(*args, **kwargs)

        return cast(T, wrapper)

    return decorator
