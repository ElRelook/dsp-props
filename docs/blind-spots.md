# What the relations don't see

A relation detects a fault only if the fault breaks it. dsp-props is strongest
on faults of **structure** (state handling, edges, indexing, normalisation,
precision of intermediates) and weakest on faults of **value**, where an
expected output remains the only oracle. This page lists the known blind spots,
with what you can do about each.

For scale: the repository's mutation suite (`python mutants/run_mutants.py`)
has 31 deliberately buggy operators in six families, and all 31 are detected
with the default 200 inputs per relation. In the companion article, on 166
generated faults in FFT, `lfilter`, `upfirdn` and overlap-add subjects, dsp-props
detects 90 %, ported NumPy and SciPy test suites 96 %, and the two together
100 %: the sets are complementary, not nested. The misses below explain why.

## A wrong operator of the right class

The structural relations say that an operator *is* an LTI filter, a resampler,
a DFT; they do not say that it is *the one you meant*.

**A filter with wrong coefficients that is still linear, time-invariant and
causal passes every structural relation.** This is the one documented blind
spot of the mutation suite: a resonant IIR filter whose gain is wrong by 1 %
(`iir_wrong_gain`) is invisible to linearity, time invariance and causality. It
is detected only because its transfer function is declared:

```python
from scipy import signal
import dsp_props as dp

b, a = signal.butter(2, 0.25)

@dp.lti_filter()                    # passes: still LTI and causal
def off_by_one_percent(x):
    return signal.lfilter(1.01 * b, a, x)

@dp.lti_filter(transfer=(b, a))     # fails the transfer-function relation
def off_by_one_percent(x):
    return signal.lfilter(1.01 * b, a, x)
```

The [tutorial](tutorial.md#a-bug-the-structural-relations-cannot-see) shows
the full output. **Declare `transfer=(b, a)` whenever you know the
coefficients.**

The same holds in other classes, and some of these gaps have no declaration
that closes them:

- a resampler that consistently ignores the last input sample satisfies
  linearity and periodic time invariance, since both sides of each relation
  ignore it identically;
- a transform declared with `kind="generic"` is only checked for linearity,
  Parseval (if declared) and inversion: a DCT of the wrong type that is
  orthonormal and correctly inverted passes;
- a transform with no declared `inverse` gets neither the inversion nor the
  convolution-theorem relation;
- `real_input_hermitian=False` (the default) skips the Hermitian-symmetry
  relation for a complex DFT.

## Parameters are not generated

A declaration fixes the operator's parameters (filter coefficients, rates, the
inverse) and the relations vary **only the input signal**. A fault that shows
only for other parameter values is invisible. In the article's comparison,
every fault dsp-props missed is of this kind: seven `lfilter` faults break only
filters of order 0 or 1, or filters whose numerator is shorter than the
denominator, and the declared filters had orders 4 and 2; four `upfirdn` faults
change only its default arguments, which the declarations never used.

**Declare each operator for several representative parameter sets, including
degenerate ones**: order 0 and 1 filters, a numerator shorter than the
denominator, rate 1, default arguments. A module-level dictionary of declared
operators is picked up by `dsp-props check`:

```python
from scipy import signal
import dsp_props as dp

FILTERS = {
    f"butter{order}": dp.lti_filter(transfer=(b, a))(
        lambda x, b=b, a=a: signal.lfilter(b, a, x))
    for order in (1, 2, 4)
    for b, a in [signal.butter(order, 0.2)]
}
```

## Inputs that are never generated

The generators are aimed at the inputs that break DSP code, but they do not
cover everything:

- **dtype and shape.** Generated signals are 1-D float64 arrays. Complex inputs
  reach a transform only through the linearity relation, which uses complex
  coefficients. float32 inputs, integer inputs, multi-channel arrays and the
  `axis=` argument are never exercised.
- **Length.** Lengths go up to `max_n` (512 by default; the convolution theorem
  caps at 256). A bug that appears only for longer signals, such as a code path
  for large N, is missed unless you raise `max_n` in the declaration.
- **Random search.** Each relation sees `max_examples` inputs (200 by default).
  A fault that needs a very specific input can escape in some runs. Raise
  `max_examples` (or `--examples` on the command line) for a deeper search;
  `derandomize=True` makes runs reproducible, but also fixes which inputs are
  tried.
- **Resampler edges.** The DC-gain and alias-rejection relations look at the
  middle half of a long output, away from edge transients; the edges are only
  covered by linearity and periodic time invariance.

## Errors within the tolerance

A relation passes whenever the error is below the [tolerance
model](tolerances.md). Accuracy losses smaller than the model are invisible by
design, and they can be large in absolute terms:

- a calibrated tolerance accepts what calibration measured: PyTorch's CPU FFT,
  at up to 195 ε, passes with a tolerance calibrated on it;
- `IIRTolerance` grows with the conditioning of the recursion, so an
  ill-conditioned filter (an eighth-order Butterworth at 0.05 × Nyquist as a
  single transfer function) is checked to about 3e-5 relative error only;
- comparisons are normwise: an error concentrated in a few output samples is
  compared with the norm of the whole output, so a small localised fault in a
  large-norm output can stay below the bound.

The tolerance must not be widened to make a relation pass (see the [project
rule](tolerances.md)); by the same token, a passing relation only certifies
accuracy up to the model.

## Hidden state

Each relation call builds its inputs and calls the operator several times. An
operator whose output depends on previous calls (a global accumulator, a cache
that is not invalidated) is caught when the leak breaks a relation, as in the
`rate_state_leak` mutant, or when a failing input passes once Hypothesis
replays it, which the report states as a "non-deterministic operator". Neither
is guaranteed: state that changes the output only rarely may go unnoticed.
Streaming processors get a fresh instance for each side of the block-invariance
relation, so state carried *between instances* is not checked.

## Unstable declarations

`IIRTolerance` and the transfer-function relation assume a stable declared
filter. With a pole on or outside the unit circle, the tolerance is infinite
(NaN for an all-zero input), so time invariance and causality pass
vacuously, and the transfer-function relation errors out. Declare unstable
recursions with an explicit `tolerance=` and without `transfer`.

## Things outside the scope

There are no relations for nonlinear operators, estimators (bias, variance
against the Cramér-Rao bound), multirate identities beyond the L/M resampler
(noble identities), float32/float64 consistency, denormal handling, or
fixed-point code. Some of these are on the roadmap.

## Complementary, not competing

In practice the method and expected-value tests combine: a library keeps its
regression tests, which pin values and parameter combinations, and adds
relations, which need no values and explore inputs no one thought to write
down. The cost is one declaration per operator and a few seconds per run.
