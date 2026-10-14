"""Hypothesis strategies that produce signals a DSP engineer would recognise.

Every strategy takes the length ``n`` explicitly so that relations can draw
several signals of the same length. Generators are ordered so that Hypothesis
shrinks towards simple cases: short lengths, impulses, unit amplitude.
"""

from __future__ import annotations

import numpy as np
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

# Lengths that historically break DSP code: tiny, odd, prime, 2^k +/- 1.
PATHOLOGICAL_LENGTHS = [1, 2, 3, 5, 7, 8, 15, 16, 17, 31, 32, 33, 97, 127, 128, 129, 255, 256, 257]

AMPLITUDES = [1.0, 1e-3, 1e3, 1e-100, 1e100]


def lengths(max_n: int = 512) -> st.SearchStrategy[int]:
    """Signal lengths, biased towards pathological values."""
    patho = [n for n in PATHOLOGICAL_LENGTHS if n <= max_n]
    return st.one_of(st.sampled_from(patho), st.integers(1, max_n))


def _amplitude():
    return st.sampled_from(AMPLITUDES)


def impulse(n: int):
    return st.builds(
        lambda k, a: _impulse(n, k, a), st.integers(0, n - 1), _amplitude()
    )


def _impulse(n, k, a):
    x = np.zeros(n)
    x[k] = a
    return x


def dc(n: int):
    return _amplitude().map(lambda a: np.full(n, a))


def _sine(n, f, phi, a):
    t = np.arange(n)
    return a * np.cos(2 * np.pi * f * t + phi)


def offgrid_sine(n: int):
    """Sinusoid whose normalised frequency is not a multiple of 1/N."""
    freq = st.floats(0.0, 0.5, allow_nan=False, exclude_max=False)
    phase = st.floats(-np.pi, np.pi, allow_nan=False)
    return st.builds(lambda f, p, a: _sine(n, f, p, a), freq, phase, _amplitude())


def near_nyquist_sine(n: int):
    freq = st.floats(0.45, 0.5, allow_nan=False)
    phase = st.floats(-np.pi, np.pi, allow_nan=False)
    return st.builds(lambda f, p, a: _sine(n, f, p, a), freq, phase, _amplitude())


def close_tones(n: int):
    """Two sinusoids separated by less than one frequency bin."""
    f0 = st.floats(0.01, 0.45, allow_nan=False)
    df = st.floats(0.0, 1.0, allow_nan=False)
    return st.builds(
        lambda f, d, a: _sine(n, f, 0.0, a) + _sine(n, f + d / max(n, 1), 0.3, a),
        f0,
        df,
        _amplitude(),
    )


def white_noise(n: int):
    elems = st.floats(-1.0, 1.0, allow_nan=False, allow_infinity=False, width=64)
    return st.builds(
        lambda x, a: a * x, hnp.arrays(np.float64, n, elements=elems), _amplitude()
    )


def sparse(n: int):
    """A few impulses at arbitrary positions."""
    return st.builds(
        lambda idx, a: _sparse(n, idx, a),
        st.lists(st.integers(0, n - 1), min_size=1, max_size=min(n, 4)),
        _amplitude(),
    )


def _sparse(n, idx, a):
    x = np.zeros(n)
    for i, k in enumerate(idx):
        x[k] += a * (-1) ** i
    return x


SIGNAL_KINDS = [impulse, dc, offgrid_sine, near_nyquist_sine, close_tones, sparse, white_noise]


def signals(n: int):
    """Any of the signal families above, of length ``n``."""
    return st.one_of([kind(n) for kind in SIGNAL_KINDS])


@st.composite
def signal_pairs(draw, max_n: int = 512):
    n = draw(lengths(max_n))
    return draw(signals(n)), draw(signals(n))


@st.composite
def block_splits(draw, n: int, max_blocks: int = 8):
    """Cut points splitting a length-``n`` signal into blocks.

    Includes empty blocks and blocks of a single sample, the cases that
    expose state-handling bugs in streaming code.
    """
    return sorted(draw(st.lists(st.integers(0, n), max_size=max_blocks - 1)))


def split_blocks(x, cuts):
    edges = [0, *cuts, len(x)]
    return [x[i:j] for i, j in zip(edges[:-1], edges[1:])]
