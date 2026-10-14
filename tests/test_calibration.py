import numpy as np
import pytest

import dsp_props as dp
from dsp_props.core import CalibratedTolerance, CalibrationError, relative_error, longdouble_dft


def test_numpy_fft_is_within_a_few_eps():
    tol = dp.calibrate(np.fft.fft, lengths=range(1, 65), trials=2)
    assert tol.worst < 50


def test_calibration_refuses_a_wrong_operator():
    with pytest.raises(CalibrationError):
        dp.calibrate(lambda x: np.roll(np.fft.fft(x), 1), lengths=range(2, 10), trials=1)


def test_calibrated_model_never_below_analytic_base():
    tol = CalibratedTolerance(ratios={8: 0.1})
    assert tol.bound(8, np.float64, 1.0) >= tol.base.bound(8, np.float64, 1.0)


def test_unmeasured_length_uses_worst_ratio():
    tol = CalibratedTolerance(ratios={8: 3.0, 9: 500.0})
    assert tol.ratio(1000) == 500.0


def test_relative_error_of_exact_operator_is_zero():
    x = np.zeros(16)
    assert relative_error(np.fft.fft, longdouble_dft, x) == 0.0


def test_calibrated_tolerance_still_catches_mutants():
    from mutants.fft_mutants import MUTANTS

    tol = dp.calibrate(np.fft.fft, lengths=range(1, 129), trials=2)
    m = MUTANTS["fft_float32_internal"]
    spec = dp.transform(inverse=np.fft.ifft, parseval=True, real_input_hermitian=True, tolerance=tol)(
        m.__wrapped__ if hasattr(m, "__wrapped__") else m.__dsp_props__.func
    )
    assert not dp.verify(spec, max_examples=100, raise_on_failure=False).ok
