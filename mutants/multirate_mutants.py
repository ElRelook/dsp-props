"""Buggy rational resamplers (2/3), declared like scipy.signal.resample_poly."""

import numpy as np
import scipy.signal as ss

import dsp_props as dp

UP, DOWN = 2, 3


def _declare(func):
    return dp.resampler(UP, DOWN)(func)


def reference(x):
    return ss.resample_poly(x, UP, DOWN)


def _design(gain):
    # the filter resample_poly designs; resample_poly multiplies a given window by UP
    max_rate = max(UP, DOWN)
    h = ss.firwin(2 * 10 * max_rate + 1, 1.0 / max_rate, window=("kaiser", 5.0))
    return gain / UP * h


def missing_interpolation_gain(x):
    """The anti-imaging filter is not multiplied by the up factor: half the amplitude."""
    return ss.resample_poly(x, UP, DOWN, window=_design(1.0))


def weak_antialiasing(x):
    """Linear interpolation then plain decimation: images and aliases leak through."""
    x = np.asarray(x, dtype=float)
    up = np.zeros(UP * len(x))
    up[::UP] = x
    y = np.convolve(up, [0.5, 1.0, 0.5])[1 : 1 + len(up)]
    return y[::DOWN]


def floor_length(x):
    """Drops the last partial output sample (floor instead of ceil)."""
    n = len(x) * UP // DOWN
    return ss.resample_poly(x, UP, DOWN)[:n]


def phase_depends_on_length(x):
    """Polyphase start chosen from the input length parity."""
    x = np.asarray(x, dtype=float)
    y = ss.resample_poly(np.concatenate([np.zeros(len(x) % 2), x]), UP, DOWN)
    return y[len(y) - -(-len(x) * UP // DOWN):]


def float32_filter(x):
    """Filtering in single precision (inputs scaled to stay in float32 range)."""
    x = np.asarray(x, dtype=float)
    scale = float(np.max(np.abs(x))) if len(x) and np.any(x) else 1.0
    y = ss.resample_poly((x / scale).astype(np.float32), UP, DOWN)
    return y.astype(float) * scale


class _Leaky:
    tail = 1.0


def state_leak(x):
    """A global keeps a trace of the previous call and adds it to the next output."""
    x = np.asarray(x, dtype=float)
    y = ss.resample_poly(x, UP, DOWN)
    if len(y):
        y[0] += 1e-3 * _Leaky.tail
        _Leaky.tail = 1.0 + abs(y[-1])
    return y


MUTANTS = {
    "rate_missing_interpolation_gain": _declare(missing_interpolation_gain),
    "rate_weak_antialiasing": _declare(weak_antialiasing),
    "rate_floor_length": _declare(floor_length),
    "rate_phase_depends_on_length": _declare(phase_depends_on_length),
    "rate_float32_filter": _declare(float32_filter),
    "rate_state_leak": _declare(state_leak),
}

REFERENCE = _declare(reference)
