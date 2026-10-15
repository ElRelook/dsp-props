#!/bin/sh
# Compile every proof from scratch with coqc and print the axioms used by
# each main theorem (output of Check.v).  Exits non-zero on any error, or if
# a source contains Admitted / admit / Axiom / Parameter / Conjecture.
set -eu
cd "$(dirname "$0")"
if grep -nwE 'Admitted|admit|Axiom|Axioms|Parameter|Parameters|Conjecture' *.v; then
  echo "check.sh: forbidden command found" >&2
  exit 1
fi
make clean >/dev/null
make
