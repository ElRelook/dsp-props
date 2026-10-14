"""Buggy orthonormal DCT-II implementations (kind="generic")."""

import numpy as np
import scipy.fft as sfft

import dsp_props as dp


def _idct(X):
    return sfft.idct(X, norm="ortho")


def _declare(func, inverse=_idct):
    return dp.transform(kind="generic", inverse=inverse, parseval=True,
                        parseval_scale=lambda n: 1.0, real_input_only=True)(func)


def reference_dct(x):
    return sfft.dct(x, norm="ortho")


def missing_dc_weight(x):
    """Orthonormal scaling applied uniformly: X[0] lacks its 1/sqrt(2)."""
    n = len(x)
    return sfft.dct(x) * np.sqrt(1.0 / (2 * n))


def _inverse_wrong_type(X):
    return sfft.dct(X, type=2, norm="ortho")


def inverse_wrong_type(x):
    """The inverse uses DCT-II instead of DCT-III."""
    return sfft.dct(x, norm="ortho")


def float32_internal(x):
    return sfft.dct(np.asarray(x, dtype=np.float32), norm="ortho").astype(np.float64)


MUTANTS = {
    "dct_missing_dc_weight": _declare(missing_dc_weight),
    "dct_inverse_wrong_type": _declare(inverse_wrong_type, inverse=_inverse_wrong_type),
    "dct_float32_internal": _declare(float32_internal),
}

REFERENCE = _declare(reference_dct)
