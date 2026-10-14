"""Buggy real-input FFTs, declared like numpy.fft.rfft (kind="rdft")."""

import numpy as np

import dsp_props as dp


def _declare(func, inverse=np.fft.irfft):
    return dp.transform(inverse=inverse, kind="rdft", parseval=True)(func)


def reference_rfft(x):
    return np.fft.rfft(x)


def half_bins_off_by_one(x):
    """Returns N // 2 bins instead of N // 2 + 1 (Nyquist/last bin lost)."""
    return np.fft.fft(x)[: len(x) // 2]


def _irfft_ignores_length(X, n):
    return np.fft.irfft(X)


def irfft_ignores_length(x):
    """The inverse guesses N = 2 (len(X) - 1): wrong for every odd length."""
    return np.fft.rfft(x)


def nyquist_halved(x):
    """The Nyquist bin is halved, as when two-sided spectra are folded twice."""
    X = np.fft.rfft(x)
    if len(x) % 2 == 0 and len(x) > 1:
        X[-1] *= 0.5
    return X


def conjugated(x):
    """exp(+i...) convention: the conjugate spectrum."""
    return np.conj(np.fft.rfft(x))


def _irfft_without_symmetry(X, n):
    full = np.zeros(n, dtype=complex)
    full[: len(X)] = X
    return np.real(np.fft.ifft(full))


def irfft_without_symmetry(x):
    """The inverse zero-pads the half spectrum instead of mirroring it."""
    return np.fft.rfft(x)


MUTANTS = {
    "rfft_half_bins_off_by_one": _declare(half_bins_off_by_one),
    "rfft_inverse_ignores_length": _declare(irfft_ignores_length, inverse=_irfft_ignores_length),
    "rfft_nyquist_halved": _declare(nyquist_halved),
    "rfft_conjugated": _declare(conjugated),
    "rfft_inverse_without_symmetry": _declare(irfft_without_symmetry, inverse=_irfft_without_symmetry),
}

REFERENCE = _declare(reference_rfft)
