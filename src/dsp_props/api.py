"""Declarative API: describe an operator once, check every applicable relation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from hypothesis import HealthCheck, given, settings
from hypothesis.errors import HypothesisException

from .core.tolerance import FFTTolerance, ToleranceModel
from .relations import STREAMING_RELATIONS, TRANSFORM_RELATIONS


KINDS = ("dft", "rdft", "generic")


def hermitian_extend(half, n):
    """Full length-``n`` DFT from the ``n // 2 + 1`` bins of a real-input DFT."""
    half = np.asarray(half)
    full = np.empty(n, dtype=np.result_type(half.dtype, np.complex64))
    m = n // 2 + 1
    full[:m] = half[:m]
    if n > m:
        full[m:] = np.conj(half[1 : n - m + 1][::-1])
    return full


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
    inverse_takes_length: bool = False
    tolerance: ToleranceModel = field(default_factory=FFTTolerance)
    max_n: int = 512

    @property
    def relations(self):
        return [r for r in TRANSFORM_RELATIONS if r.applies(self)]

    @property
    def is_fourier(self):
        return self.kind in ("dft", "rdft")

    def full(self, x):
        """The transform of ``x`` as a full spectrum (rdft outputs are Hermitian-extended)."""
        y = np.asarray(self.func(x))
        if self.kind == "rdft":
            n = len(x)
            if y.shape != (n // 2 + 1,):
                raise AssertionError(f"rdft output has shape {y.shape}, expected ({n // 2 + 1},) for N={n}")
            return hermitian_extend(y, n)
        return y

    def invert(self, X, n):
        return np.asarray(self.inverse(X, n) if self.inverse_takes_length else self.inverse(X))


@dataclass
class StreamingSpec:
    make: Callable
    tolerance: ToleranceModel = field(default_factory=lambda: FFTTolerance(c=1000.0))
    max_n: int = 512

    @property
    def relations(self):
        return [r for r in STREAMING_RELATIONS if r.applies(self)]


def streaming(*, tolerance=None, max_n=512):
    """Declare a block processor: a class (or factory) whose instances have ``process(block)``.

    ``dp.verify`` then checks that any split into blocks, including empty
    blocks and single samples, gives the same output as one call.
    """

    def decorate(make):
        make.__dsp_props__ = StreamingSpec(make=make, tolerance=tolerance or FFTTolerance(c=1000.0),
                                           max_n=max_n)
        return make

    return decorate


class _StatefulProcessor:
    def __init__(self, func, init_state):
        self.func = func
        self.state = init_state() if callable(init_state) else np.array(init_state, copy=True)

    def process(self, block):
        y, self.state = self.func(block, self.state)
        return y


def stateful(func, init_state, **kwargs):
    """Wrap ``func(block, state) -> (out, state)`` (e.g. lfilter with zi) as a streaming operator."""
    return streaming(**kwargs)(lambda: _StatefulProcessor(func, init_state))


def transform(inverse=None, *, kind="dft", linear=True, parseval=False, parseval_scale=None,
              real_input_hermitian=False, real_input_only=None, inverse_takes_length=None,
              tolerance=None, max_n=512):
    """Declare a function as a transform; ``dp.verify`` then checks it.

    ``kind="dft"``: complex DFT (shift and convolution theorems apply).
    ``kind="rdft"``: real-input DFT returning ``N // 2 + 1`` bins, like
    ``numpy.fft.rfft``; its inverse is called as ``inverse(X, N)``.
    ``kind="generic"``: any linear transform (DCT, wavelets, STFT...): only
    linearity, Parseval and inversibility are checked.
    """
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
    if real_input_only is None:
        real_input_only = kind == "rdft"
    if inverse_takes_length is None:
        inverse_takes_length = kind == "rdft"

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
            inverse_takes_length=inverse_takes_length,
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
        raise TypeError(f"{func!r} has no dsp-props declaration (use @dp.transform or @dp.streaming)")
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
