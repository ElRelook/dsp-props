(* The paper's root of unity  w_N = e^{-2 pi i / N} = cos(2pi/N) - i sin(2pi/N)
   in the complex numbers R[i] over a real type R (mathcomp-analysis reals,
   mathcomp-real-closed complex numbers) is a primitive N-th root of unity, so
   every theorem of DFT.v applies to the DFT exactly as defined in the paper. *)

From mathcomp Require Import all_ssreflect all_algebra.
From mathcomp.real_closed Require Import complex.
From mathcomp Require Import reals trigo.
From mathcomp.algebra_tactics Require Import ring.
From DSPProofs Require Import DFT Filters TransferFunction.

Set Implicit Arguments.
Unset Strict Implicit.
Unset Printing Implicit Defensive.

Import Order.TTheory GRing.Theory Num.Theory.
Local Open Scope ring_scope.
Local Open Scope complex_scope.

Section Omega.

Variable R : realType.

(* expNi t = e^{-i t} = cos t - i sin t. *)
Definition expNi (t : R) : R[i] := (cos t) +i* (- sin t).

Lemma expNiM (s t : R) : expNi s * expNi t = expNi (s + t).
Proof.
rewrite /expNi /= cosD sinD; simpc; congr (_ +i* _); ring.
Qed.

Lemma expNiX (t : R) j : expNi t ^+ j = expNi (j%:R * t).
Proof.
elim: j => [|j IH]; first by rewrite expr0 mul0r /expNi cos0 sin0 oppr0.
by rewrite exprS IH expNiM mulrS mulrDl mul1r.
Qed.

Lemma expNi_eq1 (t : R) : expNi t = 1 -> cos t = 1 /\ sin t = 0.
Proof. by case=> -> /eqP; rewrite oppr_eq0 => /eqP ->. Qed.

Lemma expNi_neq1 (t : R) : 0 < t < pi *+ 2 -> expNi t != 1.
Proof.
move=> /andP[t_gt0 t_lt]; apply/negP => /eqP /expNi_eq1 [c1 s0].
have [lt|gt|eq] := ltgtP t pi.
- have h : 0 < t < pi by rewrite t_gt0 lt.
  by move: (sin_gt0_pi h); rewrite s0 ltxx.
- have h : 0 < t - pi < pi by rewrite subr_gt0 gt /= ltrBlDr -mulr2n.
  move: (sin_gt0_pi h); rewrite sinB cospi sinpi s0 mul0r mulr0 subr0 ltxx //.
- move: c1; rewrite eq cospi => /(congr1 (fun x => x + 1)); rewrite addNr => /eqP.
  by rewrite eq_sym -mulr2n pnatr_eq0.
Qed.

(* A practical introduction rule for primitive roots. *)
Lemma prim_rootI (F : fieldType) (N : nat) (z : F) :
  (0 < N)%N -> z ^+ N = 1 -> (forall j, (0 < j < N)%N -> z ^+ j != 1) ->
  N.-primitive_root z.
Proof.
move=> N_gt0 zN zj; rewrite /primitive_root_of_unity N_gt0 /=.
apply/forallP => i; rewrite unity_rootE.
have [->|neq] := eqVneq i.+1 N; first by rewrite zN eqxx.
have lt : (i.+1 < N)%N by rewrite ltn_neqAle neq ltn_ord.
by rewrite (negPf (zj i.+1 lt)).
Qed.

(* The paper's omega = e^{-2 pi i / N}. *)
Definition omega (N : nat) : R[i] := expNi (pi *+ 2 / N%:R).

Theorem omega_prim N : (0 < N)%N -> N.-primitive_root (omega N).
Proof.
move=> N_gt0; have Nr_gt0 : (0 : R) < N%:R by rewrite ltr0n.
apply: prim_rootI => //.
  rewrite /omega expNiX mulrCA mulfV ?gt_eqF // mulr1 /expNi cos2pi sin2pi oppr0.
  by [].
move=> j /andP[j_gt0 jN]; rewrite /omega expNiX; apply: expNi_neq1.
have pi2_gt0 : (0 : R) < pi *+ 2 by rewrite pmulrn_rgt0 // pi_gt0.
rewrite mulrCA mulr_gt0 //= ?divr_gt0 ?ltr0n //.
by rewrite gtr_pMr // ltr_pdivrMr // mul1r ltr_nat.
Qed.

End Omega.

(* Corollaries: the DFT with the paper's omega. *)
Section PaperDFT.
Variable R : realType.
Variable N : nat.
Hypothesis N_gt0 : (0 < N)%N.
Notation w := (omega R N).
Let prim := omega_prim R N_gt0.

Corollary paper_dft_cshift s (x : nat -> R[i]) k :
  dft N w (cshift N s x) k = w ^+ (k * s) * dft N w x k.
Proof. exact: dft_cshift prim s x k. Qed.

Corollary paper_parseval (x : nat -> R[i]) :
  \sum_(k < N) `|dft N w x k| ^+ 2 = N%:R * \sum_(n < N) `|x n| ^+ 2.
Proof. exact: parseval prim x. Qed.

Corollary paper_hermitian (x : nat -> R[i]) k :
  (forall n, (n < N)%N -> x n \is Num.real) -> (k <= N)%N ->
  dft N w x (N - k) = (dft N w x k)^*.
Proof. exact: (@dft_hermitian _ N w prim x k). Qed.

Corollary paper_inversion (x : nat -> R[i]) n :
  (n < N)%N -> idft N w (dft N w x) n = x n.
Proof. exact: (@dft_inversion _ N w prim x n). Qed.

Corollary paper_convolution (x y : nat -> R[i]) n :
  (n < N)%N -> idft N w (fun k => dft N w x k * dft N w y k) n = cconv N x y n.
Proof. exact: (@dft_convolution _ N w prim x y n). Qed.

Corollary paper_dft_linear (a b : R[i]) (x y : nat -> R[i]) k :
  dft N w (fun n => a * x n + b * y n) k = a * dft N w x k + b * dft N w y k.
Proof. exact: dft_linear. Qed.

Corollary paper_dc_nyquist_real (x : nat -> R[i]) :
  (forall n, (n < N)%N -> x n \is Num.real) ->
  dft N w x 0 \is Num.real /\ (~~ odd N -> dft N w x N./2 \is Num.real).
Proof.
move=> xr; split; first exact: (@dft_dc_real _ N w prim x xr).
exact: (@dft_nyquist_real _ N w prim x xr).
Qed.

End PaperDFT.

(* Proposition "Transfer function" with the paper's omega_L: bin k of the
   length-L DFT of (h[0..L-1]) is within the tail bound T of
   H(e^{2 pi i k/L}) = B(u)/A(u), u = omega_L^k = e^{-2 pi i k/L}. *)
Corollary paper_transfer_function (R : realType) (L : nat) (L_gt0 : (0 < L)%N)
  p q (a b : nat -> R[i]) (b_fin : forall j, (q < j)%N -> b j = 0) k (T : R[i]) :
  Apoly p a (omega R L ^+ k) != 0 ->
  (forall M, (L <= M)%N -> \sum_(L <= n < M) `|h p a b n| <= T) ->
  (forall e, 0 < e -> exists M0, forall M, (M0 <= M)%N ->
     \sum_(M - p <= n < M) `|h p a b n| <= e) ->
  `|dft L (omega R L) (h p a b) k -
    Bpoly q b (omega R L ^+ k) / Apoly p a (omega R L ^+ k)| <= T.
Proof. exact: (tf_dft b_fin (omega_prim R L_gt0)). Qed.
