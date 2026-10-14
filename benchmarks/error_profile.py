"""Measured FFT error versus length, for NumPy and PyTorch (phase 2 data).

Usage: python benchmarks/error_profile.py [--max-n 1200] [--out benchmarks/error_profile.csv]
Writes one row per N: factorisation, worst relative error in eps for each library.
"""

import argparse
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src")]

import numpy as np  # noqa: E402

from dsp_props.core import calibrate  # noqa: E402


def factor(n):
    out, d = [], 2
    while d * d <= n:
        while n % d == 0:
            out.append(d)
            n //= d
        d += 1
    if n > 1:
        out.append(n)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--max-n", type=int, default=1200)
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--out", default=str(ROOT / "benchmarks" / "error_profile.csv"))
    args = p.parse_args()
    lengths = range(2, args.max_n + 1)

    ops = {"numpy": np.fft.fft}
    try:
        import torch

        ops["torch"] = lambda x: torch.fft.fft(torch.from_numpy(np.asarray(x))).numpy()
    except ImportError:
        pass
    try:
        import scipy.fft

        ops["scipy"] = scipy.fft.fft
    except ImportError:
        pass

    models = {name: calibrate(op, lengths=lengths, trials=args.trials) for name, op in ops.items()}
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["N", "factors", "log2N", *[f"{name}_eps" for name in models]])
        for n in lengths:
            w.writerow([n, "x".join(map(str, factor(n))), f"{np.log2(n):.3f}",
                        *[f"{m.ratios[n]:.3f}" for m in models.values()]])
    for name, m in models.items():
        print(f"[{name}] {m.summary(5)}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
