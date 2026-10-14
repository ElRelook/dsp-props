"""Buggy recursive filters, declared like scipy.signal.lfilter with a resonant 4th-order filter."""

import numpy as np
import scipy.signal as ss

import dsp_props as dp
from dsp_props.core import IIRTolerance

# Two resonant pole pairs (radius 0.95), zeros on the unit circle.
_POLES = 0.95 * np.exp(1j * np.array([0.3, -0.3, 1.2, -1.2]))
A = np.real(np.poly(_POLES))
B = np.array([0.2, 0.0, -0.4, 0.0, 0.2])
TOL = IIRTolerance(B, A)


def _declare(func, causal=True):
    return dp.lti_filter(causal=causal, transfer=(B, A))(func)


def reference(x):
    return ss.lfilter(B, A, x)


def float32_recursion(x):
    """Coefficients and state in single precision."""
    return ss.lfilter(B.astype(np.float32), A.astype(np.float32), np.asarray(x, np.float32)).astype(float)


def zero_phase_instead(x):
    """filtfilt used where a causal filter was declared."""
    x = np.asarray(x, dtype=float)
    if len(x) <= 3 * max(len(A), len(B)):
        return ss.lfilter(B, A, x)
    return ss.filtfilt(B, A, x)


def coefficients_change(x):
    """The filter is redesigned after 64 samples (time-varying)."""
    x = np.asarray(x, dtype=float)
    y1, zf = ss.lfilter(B, A, x[:64], zi=np.zeros(len(A) - 1))
    a2 = A.copy()
    a2[1] *= 0.99
    y2, _ = ss.lfilter(B, a2, x[64:], zi=zf)
    return np.concatenate([y1, y2])


def nonzero_initial_state(x):
    """Filter state initialised to 1e-6 instead of 0."""
    return ss.lfilter(B, A, x, zi=np.full(len(A) - 1, 1e-6))[0]


def wrong_gain(x):
    """Numerator scaled by 1.01: a wrong filter that is still linear, time-invariant and causal."""
    return ss.lfilter(1.01 * B, A, x)


MUTANTS = {
    "iir_float32_recursion": _declare(float32_recursion),
    "iir_zero_phase_declared_causal": _declare(zero_phase_instead),
    "iir_coefficients_change": _declare(coefficients_change),
    "iir_nonzero_initial_state": _declare(nonzero_initial_state),
}

# A wrong but still linear, time-invariant, causal filter: only the declared
# transfer function can catch it.
MUTANTS["iir_wrong_gain"] = _declare(wrong_gain)

# Without a declared transfer function the same mutant is a blind spot.
BLIND_SPOTS = {
    # a separate function object: decorators attach the declaration to the function
    "iir_wrong_gain_without_transfer": dp.lti_filter(tolerance=TOL)(lambda x: wrong_gain(x)),
}

REFERENCE = _declare(reference)
