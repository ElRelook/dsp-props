"""Deliberately buggy FFT implementations used to measure what dsp-props detects.

Each mutant is declared exactly like the correct ``numpy.fft.fft`` would be,
so a relation that misses it is a real blind spot of the tool.
"""

import numpy as np

import dsp_props as dp


def _declare(func, inverse=np.fft.ifft):
    return dp.transform(inverse=inverse, parseval=True, real_input_hermitian=True)(func)


def reference_fft(x):
    return np.fft.fft(x)


def _ifft_missing_1_over_n(X):
    return np.fft.ifft(X) * len(X)


def ifft_missing_1_over_n(x):
    """The inverse forgets the 1/N factor."""
    return np.fft.fft(x)


def _ifft_missing_conj(X):
    return np.fft.fft(X) / len(X)


def ifft_missing_conj(x):
    """The inverse is computed as a forward FFT without conjugation."""
    return np.fft.fft(x)


def circular_off_by_one(x):
    """Output bins are rotated by one."""
    return np.roll(np.fft.fft(x), 1)


def wrong_normalisation(x):
    """Orthonormal scaling while the caller expects the unnormalised DFT."""
    return np.fft.fft(x) / np.sqrt(len(x))


def float32_internal(x):
    """Silent downcast to single precision inside the transform."""
    return np.fft.fft(np.asarray(x).astype(np.complex64)).astype(np.complex128)


def wrong_twiddle_sign(x):
    """Naive DFT with exp(+2i pi kn/N): the conjugate transform."""
    x = np.asarray(x)
    n = len(x)
    k = np.arange(n)
    return np.exp(2j * np.pi * np.outer(k, k) / n) @ x


def last_sample_dropped(x):
    """The loop stops one sample early."""
    x = np.asarray(x)
    return np.fft.fft(x[:-1], n=len(x)) if len(x) > 1 else np.zeros(len(x), complex)


def dc_offset(x):
    """A tiny constant leaks into every bin."""
    return np.fft.fft(x) + 1e-9


MUTANTS = {
    "fft_ifft_missing_1_over_n": _declare(ifft_missing_1_over_n, inverse=_ifft_missing_1_over_n),
    "fft_ifft_missing_conj": _declare(ifft_missing_conj, inverse=_ifft_missing_conj),
    "fft_circular_off_by_one": _declare(circular_off_by_one),
    "fft_wrong_normalisation": _declare(wrong_normalisation),
    "fft_float32_internal": _declare(float32_internal),
    "fft_wrong_twiddle_sign": _declare(wrong_twiddle_sign),
    "fft_last_sample_dropped": _declare(last_sample_dropped),
    "fft_dc_offset": _declare(dc_offset),
}

REFERENCE = _declare(reference_fft)
