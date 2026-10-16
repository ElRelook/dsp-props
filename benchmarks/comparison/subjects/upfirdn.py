"""Subject 3: polyphase upsample / FIR filter / downsample.

Same interface and output length as scipy.signal.upfirdn(h, x, up, down) for
1-D inputs: y = downsample(convolve(h, upsample(x, up)), down), full length.
Mutated automatically.
"""

import numpy as np


def output_length(len_h, len_x, up, down):
    return ((len_x - 1) * up + len_h - 1) // down + 1


def upfirdn(h, x, up=1, down=1):
    h = np.asarray(h, dtype=float)
    x = np.asarray(x, dtype=float)
    n_out = output_length(len(h), len(x), up, down)
    y = np.zeros(n_out)
    for m in range(n_out):
        t = m * down
        # samples j of the upsampled signal with 0 <= t - j < len(h) and j % up == 0
        j_min = max(t - len(h) + 1, 0)
        j = j_min + (-j_min) % up
        j_max = min(t, (len(x) - 1) * up)
        js = np.arange(j, j_max + 1, up)
        y[m] = np.dot(h[t - js], x[js // up])
    return y
