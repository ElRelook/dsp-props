import numpy as np
from hypothesis import given, settings

from dsp_props.generators import complex_signals, lengths, signal_pairs, signals
from hypothesis import strategies as st


@settings(max_examples=100, deadline=None)
@given(st.data())
def test_signals_have_requested_length_and_are_finite(data):
    n = data.draw(lengths(256))
    x = data.draw(signals(n))
    assert x.shape == (n,)
    assert np.all(np.isfinite(x))


@settings(max_examples=50, deadline=None)
@given(signal_pairs(64))
def test_pairs_share_length(pair):
    x, y = pair
    assert x.shape == y.shape


@settings(max_examples=100, deadline=None)
@given(st.data())
def test_complex_signals_have_requested_length_and_are_finite(data):
    n = data.draw(lengths(256))
    x = data.draw(complex_signals(n))
    assert x.shape == (n,)
    assert np.all(np.isfinite(x))


def test_complex_signals_include_complex_input():
    seen = []

    @settings(max_examples=100, deadline=None, database=None)
    @given(complex_signals(8))
    def record(x):
        seen.append(np.iscomplexobj(x) and np.any(np.imag(x) != 0))

    record()
    assert any(seen)
