"""Verification reports: per-relation outcome, minimal counterexample, exports."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

SHOWN_SAMPLES = 8


def describe(value) -> Any:
    """A short, JSON-friendly description of a relation input (signals become summaries)."""
    if isinstance(value, np.ndarray):
        v = value.ravel()
        info = {"N": int(v.size), "dtype": str(v.dtype)}
        if v.size and np.all(np.isfinite(v)):
            info["max_abs"] = float(np.max(np.abs(v)))
            info["nonzero"] = int(np.count_nonzero(v))
        if v.size <= SHOWN_SAMPLES:
            info["samples"] = [_scalar(s) for s in v]
        return info
    if isinstance(value, (list, tuple)):
        return [describe(v) for v in value]
    if isinstance(value, (np.generic, int, float, complex, bool)) or value is None:
        return _scalar(value)
    return repr(value)


def _scalar(s):
    if isinstance(s, (complex, np.complexfloating)):
        return {"re": float(s.real), "im": float(s.imag)}
    if isinstance(s, (np.generic,)):
        return s.item()
    return s


def _short(desc) -> str:
    """One-line rendering of ``describe`` output."""
    if isinstance(desc, dict) and "N" in desc:
        if "samples" in desc:
            vals = ", ".join(_fmt(s) for s in desc["samples"])
            return f"[{vals}]"
        parts = [f"N={desc['N']}"]
        if "max_abs" in desc:
            parts.append(f"max|x|={desc['max_abs']:.3g}")
            parts.append(f"{desc['nonzero']} non-zero")
        return "signal(" + ", ".join(parts) + ")"
    if isinstance(desc, list):
        inner = ", ".join(_short(d) for d in desc)
        return f"({inner},)" if len(desc) == 1 else f"({inner})"
    return _fmt(desc)


def _fmt(s):
    if isinstance(s, dict) and "re" in s:
        return f"{s['re']:.4g}{s['im']:+.4g}j"
    if isinstance(s, float):
        return f"{s:.4g}"
    return str(s)


@dataclass
class Failure:
    relation: str
    error: BaseException
    example: Any = None  # the shrunk input, as passed to the relation's check
    examples_tried: Optional[int] = None  # inputs generated before the first failure

    def __str__(self):
        return f"{self.relation}: {self.error}"

    @property
    def message(self):
        return str(self.error).splitlines()[0] if str(self.error) else type(self.error).__name__

    def to_dict(self):
        return {
            "relation": self.relation,
            "error": type(self.error).__name__,
            "message": self.message,
            "examples_tried": self.examples_tried,
            "counterexample": describe(self.example),
        }


@dataclass
class Report:
    func_name: str
    checked: list
    failures: list
    kind: str = ""
    examples_per_relation: int = 0
    seconds: dict = field(default_factory=dict)

    @property
    def ok(self):
        return not self.failures

    def __str__(self):
        lines = [f"dsp-props report for {self.func_name}"]
        for name in self.checked:
            bad = [f for f in self.failures if f.relation == name]
            lines.append(f"  {'FAIL' if bad else 'ok  '} {name}")
            for f in bad:
                lines.append(f"       {f.message}")
                if f.example is not None:
                    lines.append(f"       minimal input: {_short(describe(f.example))}")
        return "\n".join(lines)

    def to_dict(self):
        return {
            "function": self.func_name,
            "kind": self.kind,
            "ok": self.ok,
            "examples_per_relation": self.examples_per_relation,
            "relations": [
                {
                    "name": name,
                    "ok": not any(f.relation == name for f in self.failures),
                    "seconds": round(self.seconds.get(name, 0.0), 3),
                }
                for name in self.checked
            ],
            "failures": [f.to_dict() for f in self.failures],
        }

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), **{"indent": 2, **kwargs})

    def to_markdown(self):
        status = "passes every relation" if self.ok else f"fails {len(self.failures)} relation(s)"
        lines = [f"### `{self.func_name}` {status}", "", "| Relation | Result | Time (s) |", "| --- | --- | --- |"]
        for name in self.checked:
            bad = any(f.relation == name for f in self.failures)
            lines.append(f"| {name} | {'**FAIL**' if bad else 'ok'} | {self.seconds.get(name, 0.0):.2f} |")
        for f in self.failures:
            lines += ["", f"**{f.relation}**: {f.message}", ""]
            if f.example is not None:
                lines.append(f"Minimal input: `{_short(describe(f.example))}`")
            if f.examples_tried is not None:
                lines.append(f"First failure after {f.examples_tried} generated input(s).")
        return "\n".join(lines)


class PropertyViolation(AssertionError):
    def __init__(self, report: Report):
        super().__init__(str(report))
        self.report = report
