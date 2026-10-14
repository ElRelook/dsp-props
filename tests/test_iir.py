import numpy as np
import scipy.signal as ss

import dsp_props as dp
from dsp_props.core import IIRTolerance, longdouble_lfilter, norm, recursion_gain


def test_recursion_gain_one_pole():
    # 1 / (1 - 0.5 z^-1): h[n] = 0.5^n, ||h||_1 = 2
    assert np.isclose(recursion_gain([1.0, -0.5]), 2.0, rtol=1e-9)


def test_unstable_filter_has_infinite_gain():
    assert recursion_gain([1.0, -1.5]) == np.inf


def test_bound_holds_for_resonant_filters():
    rng = np.random.default_rng(1)
    for r in (0.9, 0.99, 0.999):
        poles = r * np.exp(1j * np.array([0.4, -0.4, 1.1, -1.1]))
        a = np.real(np.poly(poles))
        b = rng.uniform(-1, 1, 5)
        x = rng.standard_normal(128)
        err = norm(ss.lfilter(b, a, x) - longdouble_lfilter(b, a, x).astype(float))
        assert err <= IIRTolerance(b, a).bound(128, np.float64, norm(x))


def test_lti_filter_api_on_scipy_lfilter():
    b, a = [0.2, 0.3], [1.0, -0.9]
    f = dp.lti_filter(tolerance=IIRTolerance(b, a))(lambda x: ss.lfilter(b, a, x))
    assert dp.verify(f, max_examples=100).ok


def test_non_causal_filter_declared_causal_is_caught():
    f = dp.lti_filter(causal=True)(lambda x: np.convolve(x, [0.25, 0.5, 0.25], mode="same"))
    report = dp.verify(f, max_examples=100, raise_on_failure=False)
    assert "causality" in [fl.relation for fl in report.failures]
