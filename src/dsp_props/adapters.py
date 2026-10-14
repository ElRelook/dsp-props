"""Adapters for DSP code written in C (shared libraries loaded with ctypes).

Two calling conventions are supported, both on contiguous ``double`` arrays:

* stateless: ``void f(const double *x, size_t n, double *y)``, where ``y`` holds
  ``out_length(n)`` samples (``n`` by default);
* block with state: ``void f(const double *x, size_t n, double *y, double *state)``,
  where ``state`` holds ``state_size`` doubles carried from one block to the next.

The returned Python callables can then be declared like any other operator::

    lib = build_shared("biquad.c")
    lowpass = dp.lti_filter(transfer=(b, a))(c_function(lib, "biquad", state_size=2))
    Block = dp.streaming()(c_block_processor(lib, "biquad", state_size=2))
"""

from __future__ import annotations

import ctypes
import os
import pathlib
import shutil
import subprocess
import tempfile

import numpy as np

_DOUBLE_P = ctypes.POINTER(ctypes.c_double)


def build_shared(*sources, out=None, cc=None, flags=("-O2",)):
    """Compile C sources into a shared library and load it (needs a C compiler)."""
    cc = cc or os.environ.get("CC") or shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if cc is None:
        raise RuntimeError("no C compiler found (set CC)")
    if out is None:
        out = pathlib.Path(tempfile.mkdtemp(prefix="dsp_props_")) / "libdsp.so"
    cmd = [cc, *flags, "-shared", "-fPIC", "-o", str(out), *map(str, sources), "-lm"]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return ctypes.CDLL(str(out))


def _load(lib):
    return lib if isinstance(lib, ctypes.CDLL) else ctypes.CDLL(str(lib))


def _symbol(lib, name, with_state):
    f = getattr(_load(lib), name)
    f.restype = None
    f.argtypes = [_DOUBLE_P, ctypes.c_size_t, _DOUBLE_P] + ([_DOUBLE_P] if with_state else [])
    return f


def _ptr(a):
    return a.ctypes.data_as(_DOUBLE_P)


def c_function(lib, name, *, out_length=None, state_size=None):
    """A Python callable ``y = f(x)`` around a C function (state, if any, starts at zero)."""
    f = _symbol(lib, name, state_size is not None)
    out_length = out_length or (lambda n: n)

    def call(x):
        x = np.ascontiguousarray(x, dtype=np.float64)
        y = np.zeros(out_length(len(x)))
        if state_size is None:
            f(_ptr(x), len(x), _ptr(y))
        else:
            state = np.zeros(state_size)
            f(_ptr(x), len(x), _ptr(y), _ptr(state))
        return y

    call.__name__ = name
    call.__qualname__ = name
    return call


def c_block_processor(lib, name, *, state_size, init_state=None):
    """A factory of block processors (``process(block)``) for ``dp.streaming``."""
    f = _symbol(lib, name, True)

    class Processor:
        def __init__(self):
            self.state = np.zeros(state_size) if init_state is None else np.array(init_state, dtype=float)

        def process(self, block):
            x = np.ascontiguousarray(block, dtype=np.float64)
            y = np.zeros(len(x))
            f(_ptr(x), len(x), _ptr(y), _ptr(self.state))
            return y

    Processor.__name__ = Processor.__qualname__ = name
    return Processor
