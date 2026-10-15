"""Subject 1: a textbook FFT (radix-2 Cooley-Tukey, Bluestein for other lengths).

Same interface as numpy.fft.fft / numpy.fft.ifft for 1-D inputs. This file
is mutated automatically by benchmarks/comparison/mutate.py; keep it free of
dead code so that every mutant changes reachable behaviour.
"""

import numpy as np


def _bit_reverse(n):
    bits = n.bit_length() - 1
    v = np.arange(n)
    r = np.zeros(n, dtype=np.int64)
    for _ in range(bits):
        r = (r << 1) | (v & 1)
        v = v >> 1
    return r


def _radix2(x):
    n = len(x)
    a = x[_bit_reverse(n)]
    size = 2
    while size <= n:
        half = size // 2
        w = np.exp(-2j * np.pi * np.arange(half) / size)
        blocks = a.reshape(n // size, size)
        even = blocks[:, :half].copy()
        odd = blocks[:, half:] * w
        blocks[:, :half] = even + odd
        blocks[:, half:] = even - odd
        a = blocks.reshape(n)
        size = size * 2
    return a


def _bluestein(x):
    n = len(x)
    m = 1
    while m < 2 * n - 1:
        m = m * 2
    k = np.arange(n)
    chirp = np.exp(-1j * np.pi * ((k * k) % (2 * n)) / n)
    a = np.zeros(m, dtype=complex)
    a[:n] = x * chirp
    b = np.zeros(m, dtype=complex)
    b[:n] = np.conj(chirp)
    b[m - n + 1:] = np.conj(chirp[1:][::-1])
    conv = np.conj(_radix2(np.conj(_radix2(a) * _radix2(b)))) / m
    return conv[:n] * chirp


def fft(x):
    x = np.array(x, dtype=complex)
    n = len(x)
    if n <= 1:
        return x
    if (n & (n - 1)) == 0:
        return _radix2(x)
    return _bluestein(x)


def ifft(X):
    X = np.array(X, dtype=complex)
    n = len(X)
    if n == 0:
        return X
    return np.conj(fft(np.conj(X))) / n
