import numpy as np
import pytest

import dsp_props as dp
from mutants import ALL_MUTANTS, REFERENCES


def test_numpy_fft_satisfies_all_relations():
    report = dp.verify(REFERENCES["fft"], max_examples=150)
    assert report.ok
    assert len(report.checked) == 6


@pytest.mark.parametrize("family", ["rfft", "dct", "iir", "streaming"])
def test_other_references_pass(family):
    assert dp.verify(REFERENCES[family], max_examples=100).ok


def test_decorator_api_on_user_function():
    @dp.transform(inverse=np.fft.ifft, parseval=True, real_input_hermitian=True)
    def my_fft(x):
        return np.fft.fft(x)

    assert dp.verify(my_fft, max_examples=50).ok


def test_generic_transform_skips_dft_only_relations():
    @dp.transform(kind="generic", inverse=np.fft.irfft, real_input_only=True)
    def scaled(x):
        return 2.0 * np.asarray(x)

    names = [r.name for r in scaled.__dsp_props__.relations]
    assert "circular shift" not in names
    assert "convolution theorem" not in names


@pytest.mark.parametrize("name", sorted(ALL_MUTANTS))
def test_mutant_is_detected(name):
    report = dp.verify(ALL_MUTANTS[name], max_examples=150, raise_on_failure=False)
    assert not report.ok, f"mutant {name} survived"
