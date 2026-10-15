"""Subject 2: a direct-form II transposed IIR filter with initial state.

Same interface as scipy.signal.lfilter for 1-D inputs: returns ``y`` when
``zi`` is None, ``(y, zf)`` otherwise. Mutated automatically.
"""

import numpy as np


def lfilter(b, a, x, zi=None):
    b = [float(v) for v in np.atleast_1d(b)]
    a = [float(v) for v in np.atleast_1d(a)]
    order = max(len(a), len(b))
    a0 = a[0]
    b = [v / a0 for v in b] + [0.0] * (order - len(b))
    a = [v / a0 for v in a] + [0.0] * (order - len(a))
    if zi is None:
        z = [0.0] * (order - 1)
    else:
        z = [float(v) for v in np.atleast_1d(zi)]
    x = np.asarray(x, dtype=float)
    y = np.zeros(len(x))
    for i in range(len(x)):
        xi = float(x[i])
        yi = b[0] * xi
        if order > 1:
            yi = yi + z[0]
        for k in range(order - 2):
            z[k] = b[k + 1] * xi + z[k + 1] - a[k + 1] * yi
        if order > 1:
            z[order - 2] = b[order - 1] * xi - a[order - 1] * yi
        y[i] = yi
    if zi is None:
        return y
    return y, np.array(z, dtype=float)
