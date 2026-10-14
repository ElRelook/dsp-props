"""Declarative API: describe an operator once, check every applicable relation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from hypothesis import HealthCheck, given, settings
from hypothesis.errors import HypothesisException

from .core.tolerance import FFTTolerance, ToleranceModel
from .relations import TRANSFORM_RELATIONS


@dataclass
class TransformSpec:
    func: Callable
    inverse: Optional[Callable] = None
    kind: str = "dft"
    linear: bool = True
    parseval: bool = False
    parseval_scale: Callable[[int], float] = lambda n: n
    real_input_hermitian: bool = False
    real_input_only: bool = False
    tolerance: ToleranceModel = field(default_factory=FFTTolerance)
    max_n: int = 512

    @property
    def relations(self):
        return [r for r in TRANSFORM_RELATIONS if r.applies(self)]


def transform(inverse=None, *, kind="dft", linear=True, parseval=False, parseval_scale=None,
              real_input_hermitian=False, real_input_only=False, tolerance=None, max_n=512):
    """Declare a function as a transform; ``dp.verify`` then checks it.

    ``kind="dft"`` enables the shift and convolution theorems; use
    ``kind="generic"`` for transforms that are only linear/invertible.
    """

    def decorate(func):
        func.__dsp_props__ = TransformSpec(
            func=func,
            inverse=inverse,
            kind=kind,
            linear=linear,
            parseval=parseval,
            parseval_scale=parseval_scale or (lambda n: n),
            real_input_hermitian=real_input_hermitian,
            real_input_only=real_input_only,
            tolerance=tolerance or FFTTolerance(),
            max_n=max_n,
        )
        return func

    return decorate


@dataclass
class Failure:
    relation: str
    error: BaseException

    def __str__(self):
        return f"{self.relation}: {self.error}"


@dataclass
class Report:
    func_name: str
    checked: list
    failures: list

    @property
    def ok(self):
        return not self.failures

    def __str__(self):
        lines = [f"dsp-props report for {self.func_name}"]
        for name in self.checked:
            bad = [f for f in self.failures if f.relation == name]
            lines.append(f"  {'FAIL' if bad else 'ok  '} {name}")
            for f in bad:
                lines.append(f"       {str(f.error).splitlines()[0]}")
        return "\n".join(lines)


class PropertyViolation(AssertionError):
    def __init__(self, report: Report):
        super().__init__(str(report))
        self.report = report


def _hypothesis_test(rel, spec, max_examples, derandomize):
    @settings(max_examples=max_examples, deadline=None, database=None,
              derandomize=derandomize, suppress_health_check=list(HealthCheck),
              print_blob=False)
    @given(rel.inputs(spec))
    def run(inputs):
        rel.check(spec, inputs)

    return run


def verify(func, *, max_examples=200, raise_on_failure=True, derandomize=False) -> Report:
    """Run every relation declared for ``func`` and return a report."""
    spec = getattr(func, "__dsp_props__", None)
    if spec is None:
        raise TypeError(f"{func!r} has no dsp-props declaration (use @dp.transform)")
    failures, checked = [], []
    for rel in spec.relations:
        checked.append(rel.name)
        try:
            _hypothesis_test(rel, spec, max_examples, derandomize)()
        except HypothesisException:
            raise  # misuse of the framework, not a property violation
        except Exception as exc:  # noqa: BLE001 - every failure is reported
            failures.append(Failure(rel.name, exc))
    report = Report(getattr(func, "__name__", repr(func)), checked, failures)
    if failures and raise_on_failure:
        raise PropertyViolation(report)
    return report
