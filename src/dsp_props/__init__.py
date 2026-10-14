"""dsp-props: property-based testing for digital signal processing code."""

from . import core, generators, relations
from .api import (
    PropertyViolation,
    Report,
    StreamingSpec,
    TransformSpec,
    stateful,
    streaming,
    transform,
    verify,
)

__version__ = "0.0.1"

__all__ = [
    "core",
    "generators",
    "relations",
    "transform",
    "streaming",
    "stateful",
    "StreamingSpec",
    "verify",
    "Report",
    "TransformSpec",
    "PropertyViolation",
]
