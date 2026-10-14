"""Mutation suite: deliberately buggy DSP operators and their correct references."""

from . import dct_mutants, fft_mutants, rfft_mutants, streaming_mutants

FAMILIES = [fft_mutants, rfft_mutants, dct_mutants, streaming_mutants]

ALL_MUTANTS = {name: m for fam in FAMILIES for name, m in fam.MUTANTS.items()}
REFERENCES = {fam.__name__.split(".")[-1].replace("_mutants", ""): fam.REFERENCE for fam in FAMILIES}
