import numpy as np
import pytest

from dsp_props.core import FFTTolerance, ToleranceError, assert_close


def test_identical_arrays_pass():
    x = np.arange(8.0)
    assert_close(x, x.copy(), FFTTolerance())


def test_error_above_bound_fails():
    x = np.ones(64)
    with pytest.raises(ToleranceError):
        assert_close(x + 1e-6, x, FFTTolerance())


def test_nan_is_rejected():
    with pytest.raises(ToleranceError):
        assert_close(np.array([np.nan]), np.array([0.0]), FFTTolerance())


def test_float32_bound_is_looser_than_float64():
    m = FFTTolerance()
    assert m.bound(256, np.float32, 1.0) > m.bound(256, np.float64, 1.0)
