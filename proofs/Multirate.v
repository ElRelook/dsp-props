(* Appendix A, Proposition "Periodic time invariance" and the resampler part
   of Proposition "Linearity".  The resampler is f = down_M o (h * .) o up_L,
   with a causal filter h applied from zero state (Filters.conv). *)

From mathcomp Require Import all_ssreflect all_algebra.
From DSPProofs Require Import Filters.

Set Implicit Arguments.
Unset Strict Implicit.
Unset Printing Implicit Defensive.

Import GRing.Theory Num.Theory.
Local Open Scope ring_scope.

Section Multirate.

Variable R : comRingType.
Variables (L M : nat).
Hypotheses (L_gt0 : (0 < L)%N) (M_gt0 : (0 < M)%N).
Implicit Types (h x y : nat -> R).

(* Zero insertion: up_L x [n] = x[n/L] if L | n, 0 otherwise. *)
Definition up x (n : nat) : R := if (L %| n)%N then x (n %/ L)%N else 0.
(* Decimation: down_M y [n] = y[n M]. *)
Definition down y (n : nat) : R := y (n * M)%N.
Definition resample h x (n : nat) : R := down (conv h (up x)) n.

(* Proposition "Linearity", resampler part. *)
Theorem resample_linear (a b : R) h x y n :
  resample h (fun m => a * x m + b * y m) n = a * resample h x n + b * resample h y n.
Proof.
rewrite /resample /down -conv_linear; apply: conv_ext => m _; rewrite /up.
by case: ifP; rewrite ?mulr0 ?addr0.
Qed.

Lemma up_delay x s n : up (delay s x) n = delay (L * s) (up x) n.
Proof.
rewrite /up /delay.
case: (leqP (L * s) n) => [le | lt].
  have -> : (L %| n - L * s)%N = (L %| n)%N.
    by rewrite -(dvdn_addr _ (dvdn_mulr s (dvdnn L))) subnKC.
  case: ifP => // dvd.
  rewrite leq_divRL // mulnC le; congr (x _).
  rewrite [in RHS](_ : n = L * (n %/ L))%N; last by rewrite mulnC divnK.
  by rewrite -mulnBr mulKn.
case: ifP => // dvd; rewrite ifF //; apply/negbTE; rewrite -ltnNge.
by rewrite ltn_divLR // mulnC.
Qed.

Lemma down_delay y s n : down (delay (L * s * M) y) n = delay (L * s) (down y) n.
Proof.
rewrite /down /delay leq_pmul2r // -mulnBl.
by [].
Qed.

(* Proposition "Periodic time invariance": delaying the input by M s samples
   delays the output by L s samples. *)
Theorem resample_periodic_ti h x s n :
  resample h (delay (M * s) x) n = delay (L * s) (resample h x) n.
Proof.
rewrite /resample -down_delay /down -conv_delay.
apply: conv_ext => m _; rewrite up_delay.
by rewrite mulnCA mulnC.
Qed.

End Multirate.
