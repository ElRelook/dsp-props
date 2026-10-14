import numpy as np
from hypothesis import given, settings

from dsp_props.generators import lengths, signal_pairs, signals
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
