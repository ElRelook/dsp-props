"""Bug-hunting campaign: run dsp-props relations against real libraries.

Usage: python benchmarks/campaign.py [--examples N] [--only SUBSTRING]

Each target is a (name, check, strategy) triple. Failures are reported with
the minimal input found by Hypothesis.
"""

import argparse
import pathlib
import sys
import time
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

import numpy as np  # noqa: E402
from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

import dsp_props as dp  # noqa: E402
from dsp_props.core import FFTTolerance, assert_close, norm  # noqa: E402
from dsp_props.generators import lengths, signals  # noqa: E402

TOL = FFTTolerance()
TARGETS = []


def target(name, strategy):
    def register(check):
        TARGETS.append((name, check, strategy))
        return check

    return register


@st.composite
def sig(draw, max_n=256, min_n=1):
    n = draw(lengths(max_n).filter(lambda k: k >= min_n))
    return draw(signals(n))


@st.composite
def sig_pair(draw, max_n=256, min_n=1, same_length=False):
    x = draw(sig(max_n, min_n))
    y = draw(signals(len(x))) if same_length else draw(sig(max_n, min_n))
    return x, y


@st.composite
def stable_iir(draw, max_order=6):
    """Random stable IIR filter (poles inside radius 0.97)."""
    order = draw(st.integers(1, max_order))
    radii = draw(st.lists(st.floats(0.0, 0.97), min_size=order, max_size=order))
    angles = draw(st.lists(st.floats(0.0, np.pi), min_size=order, max_size=order))
    poles = []
    for r, t in zip(radii, angles):
        poles += [r * np.exp(1j * t), r * np.exp(-1j * t)]
    a = np.real(np.poly(poles))
    b = np.array(draw(st.lists(st.floats(-1, 1), min_size=1, max_size=2 * order + 1)))
    if not np.any(b):
        b[0] = 1.0
    return b, a


@st.composite
def block_splits(draw, n):
    """Split points for block processing, including blocks of size 0 and 1."""
    cuts = draw(st.lists(st.integers(0, n), max_size=8))
    return sorted(cuts)


def blocks(x, cuts):
    edges = [0, *cuts, len(x)]
    return [x[i:j] for i, j in zip(edges[:-1], edges[1:])]


# --------------------------------------------------------------------------
# Transforms: reuse the library relations through @dp.transform
# --------------------------------------------------------------------------

def _transform_targets():
    import scipy.fft as sfft
    import torch

    def t_fft(x):
        return torch.fft.fft(torch.from_numpy(np.asarray(x))).numpy()

    def t_ifft(X):
        return torch.fft.ifft(torch.from_numpy(np.asarray(X))).numpy()

    out = {
        "scipy.fft.fft": dp.transform(inverse=sfft.ifft, parseval=True, real_input_hermitian=True)(
            lambda x: sfft.fft(x)),
        "torch.fft.fft (float64)": dp.transform(inverse=t_ifft, parseval=True, real_input_hermitian=True)(t_fft),
        "scipy.fft.dct-II ortho": dp.transform(
            kind="generic", inverse=lambda X: sfft.idct(X, norm="ortho"), parseval=True,
            parseval_scale=lambda n: 1.0, real_input_only=True)(lambda x: sfft.dct(x, norm="ortho")),
        "scipy.fft.dst-II ortho": dp.transform(
            kind="generic", inverse=lambda X: sfft.idst(X, norm="ortho"), parseval=True,
            parseval_scale=lambda n: 1.0, real_input_only=True)(lambda x: sfft.dst(x, norm="ortho")),
        "scipy.fft.dct-IV ortho": dp.transform(
            kind="generic", inverse=lambda X: sfft.idct(X, type=4, norm="ortho"), parseval=True,
            parseval_scale=lambda n: 1.0, real_input_only=True)(lambda x: sfft.dct(x, type=4, norm="ortho")),
    }
    return out


# --------------------------------------------------------------------------
# Real FFTs: inversibility with explicit length, agreement with full FFT
# --------------------------------------------------------------------------

@target("scipy.fft.irfft(rfft(x), n) == x", sig())
def _(x):
    import scipy.fft as sfft
    assert_close(sfft.irfft(sfft.rfft(x), len(x)), x, TOL, what="rfft roundtrip")


@target("torch irfft(rfft(x), n) == x", sig())
def _(x):
    import torch
    t = torch.from_numpy(x)
    y = torch.fft.irfft(torch.fft.rfft(t), n=len(x)).numpy()
    assert_close(y, x, TOL, what="torch rfft roundtrip")


@target("scipy.fft.rfft == fft[:n//2+1]", sig())
def _(x):
    import scipy.fft as sfft
    full = sfft.fft(x)
    assert_close(sfft.rfft(x), full[: len(x) // 2 + 1], TOL, ref_norm=norm(full), what="rfft vs fft")


@target("float32 vs float64 fft (scipy)", sig())
def _(x):
    import scipy.fft as sfft
    x32 = x.astype(np.float32)
    if not np.all(np.isfinite(x32)) or norm(x32) < np.finfo(np.float32).tiny * 1e6:
        return  # out of float32 range: not a meaningful comparison
    y32 = sfft.fft(x32)
    assert y32.dtype == np.complex64, f"dtype {y32.dtype}"
    ref = sfft.fft(x32.astype(np.float64))
    assert_close(y32.astype(np.complex128), ref, FFTTolerance(c=20 * np.finfo(np.float32).eps / np.finfo(np.float64).eps), what="fft float32")


@target("float32 vs float64 fft (torch)", sig())
def _(x):
    import torch
    x32 = x.astype(np.float32)
    if not np.all(np.isfinite(x32)) or norm(x32) < np.finfo(np.float32).tiny * 1e6:
        return
    y32 = torch.fft.fft(torch.from_numpy(x32)).numpy()
    ref = np.fft.fft(x32.astype(np.float64))
    assert_close(y32.astype(np.complex128), ref, FFTTolerance(c=20 * np.finfo(np.float32).eps / np.finfo(np.float64).eps), what="torch fft float32")


@target("scipy.signal.czt default == fft", sig())
def _(x):
    import scipy.signal as ss
    full = np.fft.fft(x)
    assert_close(ss.czt(x), full, FFTTolerance(c=200), ref_norm=norm(full), what="czt vs fft")


@target("scipy.signal.zoom_fft full band == fft", sig(min_n=2))
def _(x):
    import scipy.signal as ss
    full = np.fft.fft(x)
    assert_close(ss.zoom_fft(x, 2.0, endpoint=False), full, FFTTolerance(c=200), ref_norm=norm(full), what="zoom_fft vs fft")


# --------------------------------------------------------------------------
# Convolution: fast methods vs direct sum
# --------------------------------------------------------------------------

def _conv_ref(x, y, out):
    return np.sqrt(len(out)) * norm(x) * norm(y)


for _mode in ["full", "same", "valid"]:
    for _fn in ["fftconvolve", "oaconvolve"]:

        @target(f"scipy.signal.{_fn}(mode={_mode}) == direct", sig_pair())
        def _(pair, fn=_fn, mode=_mode):
            import scipy.signal as ss
            x, y = pair
            if mode == "valid" and len(x) < len(y):
                x, y = y, x
            direct = ss.convolve(x, y, mode=mode, method="direct")
            fast = getattr(ss, fn)(x, y, mode=mode)
            assert_close(fast, direct, TOL, ref_norm=_conv_ref(x, y, direct), what=f"{fn} {mode}")


@target("scipy.signal.correlate == convolve(x, reversed y)", sig_pair())
def _(pair):
    import scipy.signal as ss
    x, y = pair
    a = ss.correlate(x, y, mode="full", method="fft")
    b = ss.convolve(x, y[::-1], mode="full", method="direct")
    assert_close(a, b, TOL, ref_norm=_conv_ref(x, y, b), what="correlate")


# --------------------------------------------------------------------------
# Streaming: block processing with carried state == one-shot processing
# --------------------------------------------------------------------------

@st.composite
def stream_case(draw):
    x = draw(sig(256))
    return x, draw(stable_iir()), draw(block_splits(len(x)))


@target("scipy.signal.lfilter by blocks == one shot", stream_case())
def _(case):
    import scipy.signal as ss
    x, (b, a), cuts = case
    whole = ss.lfilter(b, a, x)
    zi = np.zeros(max(len(a), len(b)) - 1)
    parts = []
    for blk in blocks(x, cuts):
        y, zi = ss.lfilter(b, a, blk, zi=zi)
        parts.append(y)
    assert_close(np.concatenate(parts), whole, FFTTolerance(c=1000), what="lfilter blocks")


@target("scipy.signal.sosfilt by blocks == one shot", stream_case())
def _(case):
    import scipy.signal as ss
    x, (b, a), cuts = case
    sos = ss.tf2sos(b, a)
    whole = ss.sosfilt(sos, x)
    zi = np.zeros((sos.shape[0], 2))
    parts = []
    for blk in blocks(x, cuts):
        y, zi = ss.sosfilt(sos, blk, zi=zi)
        parts.append(y)
    assert_close(np.concatenate(parts), whole, FFTTolerance(c=1000), what="sosfilt blocks")


@target("scipy.signal.upfirdn by blocks (no resampling) == one shot", stream_case())
def _(case):
    import scipy.signal as ss
    x, (b, _a), cuts = case
    whole = ss.lfilter(b, [1.0], x)
    via = ss.upfirdn(b, x)[: len(x)]
    assert_close(via, whole, FFTTolerance(c=1000), what="upfirdn vs lfilter")


# --------------------------------------------------------------------------
# Time-frequency: STFT inversibility
# --------------------------------------------------------------------------

@target("scipy ShortTimeFFT: istft(stft(x)) == x", st.tuples(sig(256, min_n=16), st.sampled_from([8, 16, 32]), st.sampled_from([2, 4])))
def _(case):
    import scipy.signal as ss
    x, nperseg, frac = case
    win = ss.windows.hann(nperseg, sym=False)
    hop = nperseg // frac
    stft = ss.ShortTimeFFT(win, hop=hop, fs=1.0)
    S = stft.stft(x)
    y = stft.istft(S, k1=len(x))
    assert_close(y, x, FFTTolerance(c=200), what=f"ShortTimeFFT nperseg={nperseg} hop={hop}")


@target("torch istft(stft(x)) == x", st.tuples(sig(256, min_n=32), st.sampled_from([8, 16, 32]), st.sampled_from([2, 4])))
def _(case):
    import torch
    x, n_fft, frac = case
    t = torch.from_numpy(x)
    win = torch.hann_window(n_fft, dtype=torch.float64)
    hop = n_fft // frac
    S = torch.stft(t, n_fft, hop_length=hop, window=win, return_complex=True, center=True)
    y = torch.istft(S, n_fft, hop_length=hop, window=win, center=True, length=len(x)).numpy()
    assert_close(y, x, FFTTolerance(c=200), what=f"torch stft n_fft={n_fft} hop={hop}")


@target("scipy.signal.resample_poly(x, 1, 1) == x", sig())
def _(x):
    import scipy.signal as ss
    assert_close(ss.resample_poly(x, 1, 1), x, TOL, what="resample_poly identity")


@target("scipy.signal.decimate is linear", sig_pair(256, min_n=40, same_length=True))
def _(pair):
    import scipy.signal as ss
    x, y = pair
    lhs = ss.decimate(2 * x - 3 * y, 2)
    rhs = 2 * ss.decimate(x, 2) - 3 * ss.decimate(y, 2)
    ref = 2 * norm(ss.decimate(x, 2)) + 3 * norm(ss.decimate(y, 2))
    assert_close(lhs, rhs, FFTTolerance(c=1000), ref_norm=ref, what="decimate linearity")


def run(examples, only):
    results = []
    for name, spec in _transform_targets().items():
        if only and only not in name:
            continue
        t0 = time.perf_counter()
        rep = dp.verify(spec, max_examples=examples, raise_on_failure=False)
        results.append((name, rep.ok, str(rep) if not rep.ok else "", time.perf_counter() - t0))
    for name, check, strategy in TARGETS:
        if only and only not in name:
            continue
        seen = []

        @settings(max_examples=examples, deadline=None, database=None, print_blob=False,
                  suppress_health_check=list(HealthCheck))
        @given(strategy)
        def test(inputs):
            seen.append(inputs)
            check(inputs)

        t0 = time.perf_counter()
        try:
            test()
            results.append((name, True, "", time.perf_counter() - t0))
        except Exception as exc:  # noqa: BLE001
            msg = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            minimal = seen[-1] if seen else None
            results.append((name, False, f"{msg}\n    minimal input: {_short(minimal)}", time.perf_counter() - t0))
    return results


def _short(obj):
    with np.printoptions(precision=4, threshold=12, edgeitems=3):
        return repr(obj)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--examples", type=int, default=300)
    p.add_argument("--only", default="")
    args = p.parse_args()
    results = run(args.examples, args.only)
    for name, ok, detail, dt in results:
        print(f"{'ok  ' if ok else 'FAIL'} {dt:6.1f}s  {name}")
        if detail:
            print("    " + detail.replace("\n", "\n    "))
    bad = sum(not ok for _, ok, _, _ in results)
    print(f"\n{len(results) - bad}/{len(results)} targets pass")


if __name__ == "__main__":
    main()
