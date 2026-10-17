"""Error model for recursive (IIR) filters.

Rounding errors injected at each step of y[n] = sum b x - sum a y are
filtered by 1/A(z), so they are amplified by the gain of the recursion.
Each step rounds the products b_k x[n-k] and a_k y[n-k], so the injected
error is about eps * (p + q + 1) * (|b| * |x| + |a - 1| * |y|), and it is then
filtered by 1/A(z). With h_A the impulse response of 1/A(z), h_BA that of
B(z)/A(z) (so ||y||_2 <= ||h_BA||_1 ||x||_2) and p, q the filter orders:

    ||y_hat - y||_2 <= c * eps * (p + q + 1) * ||h_A||_1
                       * (||b||_1 + (||a||_1 - 1) * ||h_BA||_1) * ||x||_2

The second term matters: with clustered poles near the unit circle the
state grows far larger than the input and dominates the rounding.

Poles close to the unit circle make ||h||_1 large: the tolerance then grows
as the filter becomes ill-conditioned, instead of producing false alarms.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .tolerance import ToleranceModel


def pole_radius(a):
    """Largest pole modulus of 1/A(z) (0 for a pure FIR filter)."""
    a = np.atleast_1d(np.asarray(a, dtype=float))
    if len(a) < 2:
        return 0.0
    return float(np.max(np.abs(np.roots(a / a[0]))))


def check_stable(b, a):
    """Raise ``ValueError`` if B(z)/A(z) has a pole on or outside the unit circle.

    The error bound of an unstable recursion is infinite and its frequency
    response is not the DFT of its impulse response, so every check against
    such a declaration would pass whatever the filter computes.
    """
    a = np.atleast_1d(np.asarray(a, dtype=float))
    if a[0] == 0:
        raise ValueError("transfer function: a[0] must be non-zero")
    r = pole_radius(a)
    if r >= 1.0:
        raise ValueError(
            f"transfer function is unstable: pole at |z| = {r:.6g} >= 1, so its error bound is "
            "infinite and no relation could fail; declare a stable B(z)/A(z) (all poles inside "
            "the unit circle)"
        )


def recursion_gain(a, b=(1.0,), tol=1e-12, max_len=1_000_000):
    """||h||_1 for h the impulse response of B(z)/A(z), truncated once it has decayed."""
    from scipy.signal import lfilter

    a = np.asarray(a, dtype=float)
    p = len(a) - 1
    if p == 0:
        return float(np.sum(np.abs(np.asarray(b, dtype=float)))) / abs(a[0])
    r = float(np.max(np.abs(np.roots(a / a[0]))))
    if r >= 1.0:
        return np.inf
    # Enough samples for r^n to fall below tol, with room for repeated poles.
    n = int(min(max_len, (np.log(tol) / np.log(max(r, 1e-300)) if r > 0 else 1) * (p + 1) + len(b) + 16))
    impulse = np.zeros(n)
    impulse[0] = 1.0
    return float(np.sum(np.abs(lfilter(b, a, impulse))))


@dataclass
class IIRTolerance(ToleranceModel):
    """Tolerance for lfilter-like recursions; see module docstring.

    The model bounds the error relative to ||x||, so relations should pass
    ``ref_norm`` equal to the norm of the *input* signal(s).
    """

    b: tuple
    a: tuple
    c: float = 4.0

    def __post_init__(self):
        check_stable(self.b, self.a)
        self.b = tuple(np.atleast_1d(np.asarray(self.b, dtype=float)))
        self.a = tuple(np.atleast_1d(np.asarray(self.a, dtype=float)))
        a0 = abs(self.a[0])
        norm_b = float(np.sum(np.abs(self.b))) / a0
        norm_a_tail = float(np.sum(np.abs(self.a[1:]))) / a0
        self.h_a = recursion_gain(self.a)
        self.h_ba = recursion_gain(self.a, self.b)
        self.gain = self.h_a * (norm_b + norm_a_tail * self.h_ba)
        self.order = len(self.a) + len(self.b) - 1

    def bound(self, n, dtype, ref_norm):
        eps = np.finfo(np.result_type(dtype, np.float32)).eps
        floor = np.finfo(np.result_type(dtype, np.float32)).tiny * n
        return self.c * eps * self.order * self.gain * ref_norm + floor


def longdouble_lfilter(b, a, x):
    """Reference recursion in extended precision (slow, for calibration and tests)."""
    b = np.asarray(b, dtype=np.longdouble)
    a = np.asarray(a, dtype=np.longdouble)
    b, a = b / a[0], a / a[0]
    x = np.asarray(x, dtype=np.longdouble)
    y = np.zeros(len(x), dtype=np.longdouble)
    for n in range(len(x)):
        acc = np.longdouble(0)
        for k in range(min(len(b), n + 1)):
            acc += b[k] * x[n - k]
        for k in range(1, min(len(a), n + 1)):
            acc -= a[k] * y[n - k]
        y[n] = acc
    return y
