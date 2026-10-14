"""Mutation score: how many deliberately buggy DSP operators dsp-props catches.

Usage: python mutants/run_mutants.py [--examples N]
Exit code is non-zero if the reference FFT fails or any mutant survives.
"""

import argparse
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

import dsp_props as dp  # noqa: E402
from mutants import ALL_MUTANTS, REFERENCES  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", type=int, default=200)
    args = parser.parse_args()

    refs_ok = True
    for family, ref in REFERENCES.items():
        report = dp.verify(ref, max_examples=args.examples, raise_on_failure=False)
        refs_ok &= report.ok
        print(f"reference {family:<10} {'ok' if report.ok else 'FAIL'}")
        if not report.ok:
            print(report)
    print()

    killed = 0
    for name, func in ALL_MUTANTS.items():
        t0 = time.perf_counter()
        report = dp.verify(func, max_examples=args.examples, raise_on_failure=False)
        dt = time.perf_counter() - t0
        caught = [f.relation for f in report.failures]
        killed += bool(caught)
        status = "killed " if caught else "SURVIVED"
        print(f"{status} {name:<34} {dt:6.1f}s  by: {', '.join(caught) or '-'}")

    total = len(ALL_MUTANTS)
    print(f"\nMutation score: {killed}/{total} ({100 * killed / total:.0f}%)")
    return 0 if refs_ok and killed == total else 1


if __name__ == "__main__":
    sys.exit(main())
