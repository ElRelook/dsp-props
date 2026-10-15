# Machine-checked proofs of the article's appendices

Coq formalisation of Appendix A ("Proofs of the relations", `app:proofs`) and
Appendix B ("Error bound of a linear recursion", `app:iir`) of
`paper/article/main.tex`. There is no `Admitted`, `admit`, `Axiom` or `Parameter`
in any source. `Check.v` runs `Print Assumptions` on every main theorem.

## Checking

```sh
cd proofs
./check.sh      # refuses Admitted/admit/Axiom/Parameter, then runs make clean && make
# or just: make
```

`make` builds the sources with `coq_makefile`/`coqc` and stops on the first error.
The last file, `Check.v`, prints the axioms each main theorem uses. A full build
from scratch takes about 75 s.

Versions (Ubuntu packages):

| component | version | package |
|---|---|---|
| Coq | 8.18.0 (OCaml 4.14.1) | `coq` |
| MathComp (ssreflect, algebra, field, ...) | 2.1.0 | `libcoq-mathcomp` |
| MathComp Analysis / Classical | 1.0.0 | `libcoq-mathcomp-analysis` |
| MathComp Real Closed (complex numbers `R[i]`) | 2.0.0 | `libcoq-mathcomp-real-closed` (**must be installed:** `apt-get install libcoq-mathcomp-real-closed`) |
| Algebra Tactics (`ring`, `field`, `lra`) | 1.2.3 | `libcoq-mathcomp-algebra-tactics` |
| Hierarchy Builder / coq-elpi | 1.6.0 / 1.19.3 | dependencies |

Coquelicot and Flocq are not used.

## Files

| file | content |
|---|---|
| `DFT.v` | DFT over a field with a primitive N-th root of unity `w`, plus Parseval and Hermitian symmetry over a `numClosedFieldType` |
| `Omega.v` | `omega N = cos(2π/N) - i sin(2π/N) = e^{-2πi/N}` in `R[i]` (with `R` a `realType`) is a primitive N-th root of unity, and the paper-level corollaries |
| `Filters.v` | causal convolution from zero state, delay, causality, linear recursions (IIR) from zero state, bounded gain |
| `Multirate.v` | `down_M ∘ (h * ·) ∘ up_L`: linearity and periodic time invariance |
| `Streaming.v` | state-machine streaming processor: block invariance |
| `TransferFunction.v` | DFT of the truncated impulse response compared with `H = B/A` |
| `IIRBound.v` | Cauchy–Schwarz, Minkowski, Young (ℓ1 * ℓ2), and the Appendix B bound |
| `Check.v` | `Print Assumptions` for every theorem below |

## Modelling choices (common to all files)

* **Signals** are functions `nat -> R`, zero for negative indices. A signal of
  length N is any such function; values at `n >= N` are never used, or the
  statement is pointwise in `n` and so holds on every window `[0, N)`.
* **DFT.** `dft N w x k = \sum_{n<N} x n * w^(k n)`. `w` is any primitive N-th
  root of unity (`N.-primitive_root w` in MathComp), so `N > 0`. Indices are
  reduced mod N with `%%`. Linearity, shift, inversion and the convolution
  theorem are proved over an **arbitrary field**. `N ≠ 0` in the field is
  derived from primitivity (`prim_root_natr_neq0`). Parseval and Hermitian
  symmetry use conjugation and norm, so they are proved over an **arbitrary
  `numClosedFieldType`**. `Omega.v` then specialises everything to the paper's
  `ω = e^{-2πi/N}`, defined as `cos(2π/N) - i sin(2π/N)` in `R[i]` with `R` a
  `realType`. All of this uses exact arithmetic, not floating point.
* **Filters.** A causal LTI filter from zero state is the truncated convolution
  `conv h x n = \sum_{m<=n} h[n-m] x[m]`. A direct-form recursion
  `y[n] + \sum_{j=1}^p a_j y[n-j] = d[n]` (`a_0 = 1`) from zero state is
  `solves d y`. Its solution `lrec d` is constructed explicitly and proved
  unique, so the hypotheses about recursions are never vacuous.
  `impresp = lrec dirac` is `h_A`, and `lrec b` is `h_{B/A}`.
* **Exact real arithmetic everywhere.** Appendix B's floating-point standard
  model is **assumed, not derived** (see below).

## Proposition → theorem map

### Appendix A

| Proposition (article) | Coq theorem(s) | file | Relation to the paper's statement |
|---|---|---|---|
| Linearity — DFT | `dft_linear`, `paper_dft_linear` | DFT.v, Omega.v | Same, over any field with a primitive root, and for the paper's ω. |
| Linearity — LTI filter from zero state | `conv_linear` (any causal impulse response), `lrec_linear`, `iir_linear`, `iir_conv` | Filters.v | Same. Recursive filters are covered by proving the recursion's output is `conv (lrec b) x` (`iir_conv`), which is the paper's "y is the convolution h*x truncated". |
| Linearity — up/filter/down resampler | `resample_linear` | Multirate.v | Same, with a causal filter from zero state and `L, M >= 1`. |
| Circular shift | `dft_cshift`, `paper_dft_cshift` | DFT.v, Omega.v | `cshift s x n = x((n + N - s mod N) mod N)`, i.e. `x[n-s]` mod N. Holds for every `s` and every `k`. |
| Parseval | `parseval`, `paper_parseval` | DFT.v, Omega.v | `\sum_{k<N} |X k|^2 = N \sum_{n<N} |x n|^2` over any `numClosedFieldType`, so complex input is allowed. The orthogonality relation is `sum_expr_prim` / `orth`. |
| Hermitian symmetry | `dft_hermitian`, `dft_dc_real`, `dft_nyquist_real`, `paper_hermitian`, `paper_dc_nyquist_real` | DFT.v, Omega.v | `x n` real for `n < N` and `k <= N` ⇒ `X(N-k) = conj(X k)`; `X 0` is real; for even N, `X(N/2)` is real. |
| Inversion and convolution | `dft_inversion`, `dft_convolution`, `paper_inversion`, `paper_convolution` | DFT.v, Omega.v | `idft X n = N^{-1} \sum_k X k w^{-kn}`. Over ℂ this is the paper's `(1/N) conj(F)` because `conj w = w^{-1}` (`conj_prim`). `cconv x y n = \sum_{m<N} x m · y((n-m) mod N)`. Both are stated for `n < N`. |
| Time invariance and causality (finite sequences) | (i) `conv_delay`, (ii) `conv_causal` | Filters.v | (i) is `f(delay s x) n = delay s (f x) n` for **every** n, which includes the N+s samples of the paper. (ii) is the same as the paper. The note about non-causal filters is not formalised. |
| Transfer function | `transfer_function_bound`, `tf_dft`, `paper_transfer_function`; finite split `tf_split` | TransferFunction.v, Omega.v | See below. |
| Bounded gain | `bounded_gain`, `sign_input_bounded`, `sign_input_attains` | Filters.v | "‖h‖₁ ≤ G" is stated as "every partial sum `\sum_{i<L} |h i| <= G`", which is equivalent for an infinite h. The sign input is `x m = sgn(h(n-m))` for any n, so for `n = N-1` it is the paper's `sign(h[N-1-m])`. It satisfies `|x m| <= 1` and gives `y n = \sum_{i<=n} |h i|`. The filter is causal. |
| Periodic time invariance | `resample_periodic_ti` (helpers `up_delay`, `down_delay`) | Multirate.v | `resample h (delay (M s) x) n = delay (L s) (resample h x) n` for every n, with the extra hypotheses `L >= 1` and `M >= 1`. For `M = 0` the statement is false; for `L = 0` it is meaningless. |
| Block invariance | `block_invariance`, `block_invariance_outputs` | Streaming.v | `phi : Q -> X -> Q * Y` is arbitrary, and `process` returns the final state and the outputs. For **any** list of blocks, empty blocks included, `process_blocks q bs = process q (flatten bs)`, i.e. same outputs **and** same final state. |

**Transfer function, precisely.** Coefficients are in a `numClosedFieldType`
(complex numbers). Write `u = z^{-1}`, `A(u) = 1 + \sum_{j=1}^p a_j u^j` (`Apoly`),
`B(u) = \sum_{j<=q} b_j u^j` (`Bpoly`), and take `h = lrec b`, the impulse
response of the recursion. With `|u| = 1` and `A(u) ≠ 0`, `transfer_function_bound` states:

> `| \sum_{n<L} h[n] u^n - B(u)/A(u) | <= T`

under two hypotheses that encode stability (absolute summability of h):

* `Htail`: every partial tail satisfies `\sum_{L<=n<M} |h n| <= T`. For an
  absolutely summable `h`, take `T = \sum_{n>=L} |h n|`.
* `Hdecay`: the windows `\sum_{M-p<=n<M} |h n|` tend to 0, written as ε–M.

`tf_dft` / `paper_transfer_function` take `u = w^k` (resp. `ω_L^k = e^{-2πik/L}`),
which turns the left-hand sum into bin k of the length-L DFT of
`(h[0..L-1])`. The right-hand side is then `H(e^{2πik/L})`. `tf_split` is the
finite identity `S_M = S_L + \sum_{L<=n<M} h[n] u^n` with
`|\sum_{L<=n<M} h[n] u^n| <= \sum_{L<=n<M} |h[n]|`.

What is *not* formalised: infinite series and limits in ℂ. The proof never
forms `\sum_{n>=0} h[n] u^n`. It proves the finite identity
`A(u) S_M(u) - B(u) = \sum_j a_j u^j \sum_{M-j<=n<M} h[n] u^n` (`key_identity`)
and lets `M → ∞` through `Hdecay`. The step "stable (poles inside the unit
circle) ⇒ h absolutely summable" is also not formalised: it is the meaning of
"stable" assumed here. `A(u) ≠ 0` is an explicit hypothesis. Stability with
`B/A` in lowest terms implies it.

### Appendix B (error bound of a linear recursion)

Setting (`Section AppendixB`, over any real closed field `R`, e.g. the reals):

* `x` is the input. `yh` is an **arbitrary** sequence, the computed output.
* `y_exact = lrec (conv b x)` is the exact output from zero state.
* `delta n = yh n - (\sum_j b_j x[n-j] - \sum_{j>=1} a_j yh[n-j])` and
  `err = yh - y_exact`.
* Norms are over the N computed samples: `nrm2 N v = sqrt(\sum_{n<N} v_n^2)` and
  `nrm1 N v = \sum_{n<N} |v_n|`.

The `‖·‖₁` of `b`, `h_A` and `h_{B/A}` are therefore the partial sums over
`[0, N)`. These are ≤ the full ℓ1 norms, so the statements are slightly
stronger than the paper's, and they need no stability assumption.

* **Assumed (hypothesis `Hdelta`), not derived:**
  `|delta n| <= g (\sum_j |b_j||x[n-j]| + \sum_{j>=1} |a_j||yh[n-j]|)` for `n < N`,
  with `g >= 0`. This is what the standard model
  `fl(x op y) = (x op y)(1+θ), |θ| <= u` gives with `g = γ_k`, `k = p+q+1`
  (Higham's inner-product bound). Neither the standard model nor the γ_k
  bound is formalised; Flocq is not used.

| Step of the article | Coq theorem | Statement |
|---|---|---|
| `A(z)e = δ`, i.e. `e = h_A * δ` | `err_conv` | `err n = conv hA delta n` for every n (exact). |
| Young's inequality | `young` | `nrm2 N (conv h d) <= nrm1 N h * nrm2 N d` for any `h, d`. `cauchy_schwarz` and the Minkowski inequality `nrm2_add` are proved from scratch. |
| `‖e‖₂ ≤ ‖h_A‖₁ ‖δ‖₂` | `err_young` | |
| `‖δ‖₂ ≤ γ_k(‖b‖₁‖x‖₂ + ‖a_{1:}‖₁‖ŷ‖₂)` | `delta_bound` | with `g` in place of γ_k |
| `‖ŷ‖₂ ≤ ‖h_{B/A}‖₁‖x‖₂ + ‖e‖₂` | `yhat_bound` | uses `iir_conv` (`y = h_{B/A} * x`) |
| exact consequence (no "first order") | `iir_error_implicit` | `E <= g HA (B1 + A1 G) X + g HA A1 E` |
| | `iir_error_bound` | if `g HA A1 < 1`: `E <= g HA (B1 + A1 G) X / (1 - g HA A1)` |
| rigorous version of (eq:iir) with c = 4 | `iir_error_c4`, `gamma_le`, `iir_error_gamma` | if `kε <= 1/2` and `2kε HA A1 <= 1/2`, then with `g = kε/(1-kε)`: `E <= 4 kε HA (B1 + A1 G) X` |

In the table, `E = ‖yh − y‖₂`, `X = ‖x‖₂`, `HA = ‖h_A‖₁`, `G = ‖h_{B/A}‖₁`,
`B1 = ‖b‖₁`, `A1 = ‖a_{1:}‖₁`, `kε = keps`.

**On "to first order in ε".** The argument does not give (eq:iir) itself. It
gives the exact inequality of `iir_error_implicit`. That inequality becomes
(eq:iir) with c = 1 once the term `g·HA·A1·E` is dropped (second order, since
E = O(ε)) and γ_k is replaced by kε. `iir_error_gamma` is a version with no
approximation at all: c = 4 is rigorous for **one** computed output against
the exact output, under the two smallness conditions stated above.

## Assumptions printed by `Check.v`

* Every theorem in `DFT.v`, `Filters.v`, `Multirate.v`, `Streaming.v`,
  `TransferFunction.v` and `IIRBound.v` that `Check.v` lists:
  **`Closed under the global context`** (no axioms at all).
* The `Omega.v` corollaries (`omega_prim`, `paper_*`) are instantiated at a
  `realType` from MathComp Analysis, so they inherit the three axioms of
  `mathcomp.classical.boolp`, the standard axioms of MathComp Analysis:
  `propositional_extensionality`, `functional_extensionality_dep`,
  `constructive_indefinite_description`. No axiom is introduced here.
