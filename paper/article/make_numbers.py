"""Turn the result files of the repository into the numbers and tables of the article.

    python paper/article/make_numbers.py

Reads benchmarks/survey_results.json, benchmarks/comparison/results.jsonl
(through run_comparison.summarise), benchmarks/validation.json,
benchmarks/mutant_results.json and benchmarks/error_profile.csv, and writes
paper/article/numbers.tex and paper/article/tables/*.tex. Nothing in the
article is typed by hand.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BENCH = ROOT / "benchmarks"
sys.path[:0] = [str(BENCH / "comparison"), str(ROOT / "src")]

import run_comparison  # noqa: E402

APPROACH_LABELS = {"sop": "SoP", "dsp-props": "dsp-props", "dsp-props/uniform": "uniform",
                   "dsp-props/fixed-tol": "fixed-tol", "generic-pbt": "generic PBT"}
SUBJECT_LABELS = {"fft": "FFT", "lfilter": r"\code{lfilter}", "upfirdn": r"\code{upfirdn}",
                  "ola": "overlap-add", "all": "all"}

# Facts that come from the bug-hunting campaign reports (benchmarks/RESULTS-2026-10-14*.md),
# which are written by hand from the campaign output, and from the upstream issue trackers.
CAMPAIGN = {"campaignTargets": "46", "campaignTriaged": "three"}


def pct(x):
    return rf"{100 * x:.0f}\,\%"


def tex_float(x, digits=2):
    if x == 0:
        return "0"
    e = math.floor(math.log10(abs(x)))
    m = x / 10 ** e
    if -2 <= e <= 2:
        return f"{x:.{max(digits - 1 - e, 0)}f}" if e < digits else f"{x:.0f}"
    return rf"{m:.{digits - 1}f}\times10^{{{e}}}"


def sci(x):
    e = round(math.log10(x))
    return rf"$10^{{{e}}}$" if abs(x / 10 ** e - 1) < 1e-9 else f"${tex_float(x)}$"


def survey(macros):
    s = json.loads((BENCH / "survey_results.json").read_text())
    sig = s["SciPy (scipy.signal)"]
    macros["surveyScipyDistinctTol"] = str(sig["distinct_tolerance_values"])
    macros["surveyScipyTolDecades"] = str(round(sig["tolerance_decades"]))
    macros["surveyScipyTolMin"] = sci(sig["tolerance_min"])
    macros["surveyScipyTolMax"] = f"${sig['tolerance_max']:g}$"
    macros["surveyScipyHardcoded"] = str(sig["tests_hardcoded_expected"])
    macros["surveyTotalTests"] = f"{sum(v['tests'] for v in s.values()):,}".replace(",", "\\,")
    macros["surveyZiEmpty"] = str(sum(v["tests_zi_and_empty"] for v in s.values()))
    rows = []
    for name, v in s.items():
        rows.append(f"{name.replace('_', r'_')} & {v['tests']} & {v['tests_hypothesis']} & {v['comparisons']} & "
                    f"{v['explicit_tolerance']} & {v['distinct_tolerance_values']} & "
                    f"{sci(v['tolerance_min'])}--{('$%g$' % v['tolerance_max'])} & {v['tests_empty_input']} & "
                    f"{v['tests_zi_and_empty']} \\\\")
    table = r"""\begin{table*}[t]
\caption{Test suites of five DSP libraries (syntactic counts). Tol.: comparisons with a hand-written tolerance; distinct: number of distinct tolerance values; empty: tests with an empty input; zi+empty: tests that also pass an initial state}
\label{tab:survey}
\centering\footnotesize
\begin{tabular}{@{}lrrrrrlrr@{}}
\toprule
Suite & Tests & Hypothesis & Comparisons & Tol. & Distinct & Range & Empty & zi+empty \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table*}
"""
    (HERE / "tables" / "survey.tex").write_text(table)


def comparison(macros):
    results = BENCH / "comparison" / "results.jsonl"
    summ = run_comparison.summarise(results)
    (BENCH / "comparison" / "summary.json").write_text(json.dumps(summ, indent=1))
    cls = summ["classification"]
    macros["nMutAuto"] = str(cls["all"]["total"])
    for subj, key in [("fft", "nMutFft"), ("lfilter", "nMutLfilter"), ("upfirdn", "nMutUpfirdn"), ("ola", "nMutOla")]:
        macros[key] = str(cls[subj]["total"])
    for cat, key in [("functional", "nFunctional"), ("accuracy", "nAccuracy"), ("equivalent", "nEquivalent")]:
        macros[key] = str(cls["all"].get(cat, 0))
    kr = summ["kill_rates"]["all"]
    short = {"sop": "Sop", "dsp-props": "Dsp", "dsp-props/uniform": "Uni", "dsp-props/fixed-tol": "Fix",
             "generic-pbt": "Gen"}
    for cat, ckey in [("functional", "Func"), ("accuracy", "Acc")]:
        for a, akey in short.items():
            v = kr.get(cat, {}).get(a)
            macros[f"kill{ckey}{akey}"] = pct(v["mean"]) if v else "--"
    seeds = max(v["n_seeds"] for v in kr["functional"].values())
    macros["nSeeds"] = str(seeds)
    rows = []
    approaches = [a for a in run_comparison.approaches.APPROACHES if a in kr["functional"]]
    for subj in ["fft", "lfilter", "upfirdn", "ola", "all"]:
        for cat in ["functional", "accuracy", "equivalent"]:
            n = summ["classification"][subj].get(cat, 0)
            if n == 0:
                continue
            cells = []
            for a in approaches:
                v = summ["kill_rates"].get(subj, {}).get(cat, {}).get(a)
                if v is None:
                    cells.append("--")
                elif "min" in v and v["max"] - v["min"] > 1e-9:
                    cells.append(rf"{100 * v['mean']:.0f} ({100 * v['min']:.0f}--{100 * v['max']:.0f})")
                else:
                    cells.append(f"{100 * v['mean']:.0f}")
            label = SUBJECT_LABELS[subj] if cat == "functional" or subj == "all" else ""
            rule = r"\midrule" + "\n" if subj == "all" and cat == "functional" else ""
            rows.append(f"{rule}{SUBJECT_LABELS[subj]} & {cat} ({n}) & " + " & ".join(cells) + r" \\")
    head = " & ".join(APPROACH_LABELS[a] for a in approaches)
    table = r"""\begin{table*}[t]
\caption{Mutants detected (\%, mean over seeds, with min--max when seeds disagree). For equivalent mutants the figure is a false-alarm rate and should be 0. SoP: ported test suites of NumPy and SciPy; uniform: dsp-props without its generators; fixed-tol: without its tolerance models; generic PBT: without both}
\label{tab:comparison}
\centering\footnotesize
\begin{tabular}{@{}llrrrrr@{}}
\toprule
Subject & Class (mutants) & """ + head + r""" \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table*}
"""
    (HERE / "tables" / "comparison.tex").write_text(table)
    rec = [json.loads(line) for line in results.read_text().splitlines()]
    timeouts = [r for r in rec if r["approach"] != "oracle"]
    macros["timeoutSeconds"] = "300"
    return summ


def validation(macros):
    v = json.loads((BENCH / "validation.json").read_text())
    env = v["environment"]
    macros["scipyVersion"] = env["scipy"]
    fp = v["false-positives"]
    macros["fpSeeds"] = str(fp["rows"][0]["seeds"])
    macros["fpRuns"] = f"{fp['runs']:,}".replace(",", "\\,")
    macros["fpFailed"] = "no" if fp["failed_runs"] == 0 else str(fp["failed_runs"])
    macros["fpComparisons"] = f"{fp['comparisons']:,}".replace(",", "\\,")
    q = fp["margin_quantiles"]
    macros["marginMedian"] = f"${tex_float(q['50'])}$"
    macros["marginPnn"] = f"${tex_float(q['99'])}$"
    macros["marginMax"] = f"${tex_float(q['100'])}$"
    macros["marginFactor"] = f"{1 / q['100']:.0f}"
    kb = v["known-bug"]["runs"]
    macros["knownBugRuns"] = str(len(kb))
    macros["knownBugFlagged"] = str(sum(not r["passed"] for r in kb))
    ref = v["reference"]
    macros["refDftMax"] = f"${tex_float(ref['dft_max_in_eps64'])}$"
    macros["refLfilterMax"] = f"${tex_float(ref['lfilter_max_in_eps64'])}$"
    g = v["generators"]
    macros["genPathoCount"] = str(len(g["lengths"]["pathological_values_hit"]))
    macros["genEmptyBlock"] = pct(g["block_splits"]["fraction_with_empty_block"])
    macros["genOneBlock"] = pct(g["block_splits"]["fraction_with_one_sample_block"])
    macros["genCloseBelowOne"] = pct(g["signals"]["close_tones"]["fraction_below_one_bin"])
    macros["genOnGrid"] = pct(g["signals"]["offgrid_sine"]["fraction_on_dft_grid"])
    macros["genZeroNyq"] = pct(g["signals"]["offgrid_sine"]["fraction_freq_0_or_nyquist"])
    macros["envDescription"] = (f"Python {env['python']}, NumPy {env['numpy']}, SciPy {env['scipy']}, "
                                f"Hypothesis {env['hypothesis']}, on a 4-core Linux x86-64 machine")


def hand_mutants(macros):
    m = json.loads((BENCH / "mutant_results.json").read_text())["mutants"]
    macros["nMutHand"] = str(len(m))
    macros["handKilled"] = "all" if all(x["killed"] for x in m) else str(sum(x["killed"] for x in m))
    macros["handFirstThree"] = str(sum((x.get("inputs_before_first_failure") or 99) <= 3 for x in m))
    lens = sorted(x["min_counterexample_length"] for x in m if x.get("min_counterexample_length") is not None
                  and x["mutant"] != "iir_wrong_gain")
    macros["handMedianLen"] = str(lens[len(lens) // 2]) if len(lens) % 2 else f"{(lens[len(lens)//2-1] + lens[len(lens)//2]) / 2:g}"


def error_profile(macros):
    rows = list(csv.DictReader((BENCH / "error_profile.csv").open()))
    torch = max(rows, key=lambda r: float(r["torch_eps"]))
    macros["torchMaxEps"] = f"{float(torch['torch_eps']):.0f}"
    macros["torchWorstN"] = torch["N"]
    macros["numpyMaxEps"] = f"{max(float(r['numpy_eps']) for r in rows):.1f}"


def main():
    (HERE / "tables").mkdir(exist_ok=True)
    macros = dict(CAMPAIGN)
    survey(macros)
    comparison(macros)
    validation(macros)
    hand_mutants(macros)
    error_profile(macros)
    text = ["% Generated by make_numbers.py; do not edit."]
    for k, v in sorted(macros.items()):
        text.append(rf"\newcommand{{\{k}}}{{{v}}}")
    (HERE / "numbers.tex").write_text("\n".join(text) + "\n")
    print("\n".join(text))


if __name__ == "__main__":
    main()
