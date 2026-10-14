"""Mutation score: how many deliberately buggy DSP operators dsp-props catches.

Usage: python mutants/run_mutants.py [--examples N]
Exit code is non-zero if the reference FFT fails or any mutant survives.
"""

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

import dsp_props as dp  # noqa: E402
from mutants import ALL_MUTANTS, BLIND_SPOTS, REFERENCES  # noqa: E402


def _signal_length(example):
    """Length of the first signal in a relation input (None when there is none)."""
    if hasattr(example, "shape") and getattr(example, "ndim", 0) >= 1:
        return int(example.shape[0])
    if isinstance(example, (list, tuple)):
        for item in example:
            n = _signal_length(item)
            if n is not None:
                return n
    if isinstance(example, int) and not isinstance(example, bool):
        return example  # relations that draw only a length
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", type=int, default=200)
    parser.add_argument("--json", help="write per-mutant results (relations, counterexample size, time) here")
    args = parser.parse_args()

    refs_ok = True
    for family, ref in REFERENCES.items():
        report = dp.verify(ref, max_examples=args.examples, raise_on_failure=False)
        refs_ok &= report.ok
        print(f"reference {family:<10} {'ok' if report.ok else 'FAIL'}")
        if not report.ok:
            print(report)
    print()

    killed, rows = 0, []
    for name, func in ALL_MUTANTS.items():
        t0 = time.perf_counter()
        report = dp.verify(func, max_examples=args.examples, raise_on_failure=False)
        dt = time.perf_counter() - t0
        caught = [f.relation for f in report.failures]
        killed += bool(caught)
        sizes = [n for n in (_signal_length(f.example) for f in report.failures) if n is not None]
        tries = [f.examples_tried for f in report.failures if f.examples_tried is not None]
        size = min(sizes) if sizes else None
        first = min(tries) if tries else None
        status = "killed " if caught else "SURVIVED"
        print(f"{status} {name:<34} {dt:6.1f}s  N_min={size if size is not None else '-':<4} "
              f"first={first if first is not None else '-':<4} by: {', '.join(caught) or '-'}")
        rows.append({"mutant": name, "killed": bool(caught), "seconds": round(dt, 2), "relations": caught,
                     "min_counterexample_length": size, "inputs_before_first_failure": first})

    for name, func in BLIND_SPOTS.items():
        report = dp.verify(func, max_examples=args.examples, raise_on_failure=False)
        print(f"blind spot {name:<31} {'caught (unexpected)' if not report.ok else 'not caught (documented)'}")

    total = len(ALL_MUTANTS)
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps({"examples": args.examples, "mutants": rows}, indent=2))
    print(f"\nMutation score: {killed}/{total} ({100 * killed / total:.0f}%)")
    return 0 if refs_ok and killed == total else 1


if __name__ == "__main__":
    sys.exit(main())
