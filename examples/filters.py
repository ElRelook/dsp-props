"""Example operators for `dsp-props check examples/filters.py`."""

import numpy as np
from scipy import signal

import dsp_props as dp

B, A = signal.butter(4, 0.2)


@dp.transform(inverse=np.fft.ifft, parseval=True, real_input_hermitian=True)
def fft(x):
    return np.fft.fft(x)


@dp.lti_filter(transfer=(B, A))
def lowpass(x):
    return signal.lfilter(B, A, x)


@dp.resampler(2, 3)
def resample_2_3(x):
    return signal.resample_poly(x, 2, 3)


@dp.transform(inverse=np.fft.ifft)
def buggy_fft(x):
    """Off by one bin: dsp-props reports the smallest input that shows it."""
    return np.roll(np.fft.fft(x), 1)
