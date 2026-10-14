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


def test_norm_handles_subnormal_complex_values():
    from dsp_props.core import norm

    v = np.array([5e-324 + 0j, 0j, 1e-310j])
    assert np.isfinite(norm(v))
    assert norm(v) > 0


def test_norm_does_not_overflow_on_huge_values():
    from dsp_props.core import norm

    assert np.isclose(norm(np.full(4, 1e300)), 2e300)
