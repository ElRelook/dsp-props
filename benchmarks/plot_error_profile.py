"""Figure: measured FFT error versus N (reads benchmarks/error_profile.csv).

Usage: python benchmarks/plot_error_profile.py [--out docs/figures/error_profile.png]
"""

import argparse
import csv
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Reference categorical palette, slots 1-2 (validated: CVD-safe pair).
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=str(ROOT / "benchmarks" / "error_profile.csv"))
    p.add_argument("--out", default=str(ROOT / "docs" / "figures" / "error_profile.png"))
    args = p.parse_args()

    rows = list(csv.DictReader(open(args.csv)))
    n = np.array([int(r["N"]) for r in rows])
    numpy_eps = np.array([float(r["numpy_eps"]) for r in rows])
    torch_eps = np.array([float(r["torch_eps"]) for r in rows]) if "torch_eps" in rows[0] else None

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
    ax.set_yscale("log")
    ax.plot(n, 4 * np.log2(n), color=INK_2, lw=1, ls="--", zorder=1)
    ax.text(n[-1], 4 * np.log2(n[-1]) * 1.15, "4 · log2 N", color=INK_2, fontsize=8, ha="right", va="bottom")
    ax.scatter(n, numpy_eps, s=6, color=BLUE, lw=0, label="NumPy (SciPy identique)", zorder=2)
    if torch_eps is not None:
        ax.scatter(n, torch_eps, s=6, color=ORANGE, lw=0, label="PyTorch (MKL)", zorder=3)
        worst = int(np.argmax(torch_eps))
        ax.annotate(f"N = {n[worst]} = 4 × {n[worst] // 4}\n{torch_eps[worst]:.0f} ε",
                    xy=(n[worst], torch_eps[worst]), xytext=(n[worst] + 120, torch_eps[worst] * 0.9),
                    fontsize=8, color=INK, arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.8))

    ax.set_xlabel("Longueur N", color=INK_2, fontsize=9)
    ax.set_ylabel("Erreur relative de la FFT (en ε)", color=INK_2, fontsize=9)
    ax.set_title("La FFT de PyTorch atteint 195 ε pour certaines longueurs, NumPy reste sous 5 ε",
                 loc="left", fontsize=10.5, color=INK, pad=10)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=8)
    ax.legend(frameon=False, fontsize=8, loc="upper left", markerscale=2.5)
    fig.text(0.01, 0.01, "Pire erreur sur 2 signaux gaussiens et 3 signaux structurés par longueur, "
             "contre une FFT en long double. Source : benchmarks/error_profile.csv",
             fontsize=7, color=INK_2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
