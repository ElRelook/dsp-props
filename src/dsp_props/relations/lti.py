"""Relations for linear time-invariant filters (zero initial state).

Tolerances here are relative to the norm of the *input* signals, which is
what filter error models such as ``IIRTolerance`` bound.
"""

from __future__ import annotations

import numpy as np
from hypothesis import strategies as st

from ..core.tolerance import assert_close, norm
from ..generators import lengths, signal_pairs, signals
from .base import Relation

REAL_COEFFS = [1.0, -1.0, 2.0, 0.5, -0.75, 3.0]


@st.composite
def _signal(draw, max_n):
    n = draw(lengths(max_n))
    return draw(signals(n))


class LTILinearity(Relation):
    """f(a x + b y) = a f(x) + b f(y)."""

    name = "linearity"

    def inputs(self, spec):
        c = st.sampled_from(REAL_COEFFS)
        return st.tuples(signal_pairs(spec.max_n), c, c)

    def check(self, spec, inputs):
        (x, y), a, b = inputs
        f = spec.func
        expected = a * np.asarray(f(x)) + b * np.asarray(f(y))
        assert_close(f(a * x + b * y), expected, spec.tolerance,
                     ref_norm=abs(a) * norm(x) + abs(b) * norm(y), what=self.name)


class TimeInvariance(Relation):
    """Delaying the input by s samples delays the output by s samples (zero state)."""

    name = "time invariance"

    def inputs(self, spec):
        return st.tuples(_signal(spec.max_n), st.integers(1, 32))

    def check(self, spec, inputs):
        x, s = inputs
        y = np.asarray(spec.func(x))
        yd = np.asarray(spec.func(np.concatenate([np.zeros(s), x])))
        expected = np.concatenate([np.zeros(s), y])
        assert_close(yd, expected, spec.tolerance, ref_norm=norm(x), what=f"{self.name} (delay {s})")


class Causality(Relation):
    """Changing x[k:] leaves y[:k] unchanged."""

    name = "causality"

    def applies(self, spec):
        return spec.causal

    @staticmethod
    @st.composite
    def _case(draw, max_n):
        n = draw(lengths(max_n).filter(lambda m: m >= 2))
        x = draw(signals(n))
        k = draw(st.integers(1, n - 1))
        bump = draw(st.sampled_from([1.0, -1e3, 1e-3]))
        return x, k, bump

    def inputs(self, spec):
        return self._case(spec.max_n)

    def check(self, spec, inputs):
        x, k, bump = inputs
        x2 = x.copy()
        x2[k:] += bump * (1 + np.arange(len(x) - k))
        y1 = np.asarray(spec.func(x))[:k]
        y2 = np.asarray(spec.func(x2))[:k]
        assert_close(y2, y1, spec.tolerance, ref_norm=norm(x) + norm(x2), what=f"{self.name} (k={k})")


LTI_RELATIONS = [LTILinearity(), TimeInvariance(), Causality()]
