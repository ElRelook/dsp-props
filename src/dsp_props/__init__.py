"""dsp-props: property-based testing for digital signal processing code."""

from . import core, generators, relations
from .api import PropertyViolation, Report, TransformSpec, transform, verify

__version__ = "0.0.1"

__all__ = [
    "core",
    "generators",
    "relations",
    "transform",
    "verify",
    "Report",
    "TransformSpec",
    "PropertyViolation",
]
