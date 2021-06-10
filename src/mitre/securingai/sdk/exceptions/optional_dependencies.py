# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""Exceptions for optional dependencies"""

from .base import BaseOptionalDependencyError


class ARTDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "art" package."""


class CryptographyDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "cryptography" package."""


class PrefectDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "prefect" package."""


class TensorflowDependencyError(BaseOptionalDependencyError):
    """Method/function depends on the "tensorflow" package."""
