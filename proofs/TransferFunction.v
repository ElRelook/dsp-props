(* Appendix A, Proposition "Transfer function".

   Setting: coefficients in a numClosedFieldType C (e.g. complex numbers),
   a direct-form recursive filter  B/A  with  A(z) = 1 + \sum_{j=1}^p a_j z^-j,
   B(z) = \sum_{j=0}^q b_j z^-j, impulse response h = lrec b (Filters.v).
   We write u for z^-1, so that  H(e^{i theta}) = B(u)/A(u)  with
   u = e^{-i theta}; for theta = 2 pi k / L, u = omega_L^k.

   "Stable" is used through two consequences of absolute summability of h:
     Htail  : every partial tail  \sum_{L <= n < M} |h n|  is <= T
              (T = \sum_{n >= L} |h n| for a summable h), and
     Hdecay : the windows  \sum_{M-p <= n < M} |h n|  tend to 0.
   The conclusion is the paper's bound  |DFT_L(h[0..L-1])[k] - H| <= T. *)

From mathcomp Require Import all_ssreflect all_algebra.
From mathcomp.algebra_tactics Require Import ring.
From DSPProofs Require Import Filters DFT.

Set Implicit Arguments.
Unset Strict Implicit.
Unset Printing Implicit Defensive.

Import Order.TTheory GRing.Theory Num.Theory.
Local Open Scope ring_scope.

Section TF.

Variable C : numClosedFieldType.
Variables (p q : nat) (a b : nat -> C).
Hypothesis b_fin : forall j, (q < j)%N -> b j = 0.

Definition h : nat -> C := lrec p a b.

Definition Apoly (u : C) : C := 1 + \sum_(1 <= j < p.+1) a j * u ^+ j.
Definition Bpoly (u : C) : C := \sum_(0 <= j < q.+1) b j * u ^+ j.

(* Partial sums of the series  \sum_n y[n] u^n. *)
Definition psum (y : nat -> C) (m M : nat) (u : C) : C :=
  \sum_(m <= n < M) y n * u ^+ n.

Lemma psum_split y L M u : (L <= M)%N -> psum y 0 M u = psum y 0 L u + psum y L M u.
Proof. by move=> le; rewrite /psum (@big_cat_nat _ _ _ L). Qed.

Lemma psum_delay j y M u : psum (delay j y) 0 M u = u ^+ j * psum y 0 (M - j) u.
Proof.
rewrite /psum /delay; case: (leqP j M) => [le | lt]; last first.
  have -> : (M - j)%N = 0%N by apply/eqP; rewrite subn_eq0 ltnW.
  rewrite [in RHS]big_geq // mulr0.
  rewrite big_nat_cond big1 // => n /andP[/andP[_ ltn] _].
  by rewrite ifF ?mul0r // ltn_geF // (ltn_trans ltn).
rewrite (@big_cat_nat _ _ _ j) //= big_nat_cond big1 ?add0r; last first.
  by move=> n /andP[/andP[_ ltn] _]; rewrite ifF ?mul0r // ltn_geF.
rewrite -[X in \sum_(X <= _ < _) _]add0n big_addn mulr_sumr.
apply: eq_bigr => i _; rewrite leq_addl addnK exprD.
by ring.
Qed.

Lemma Bpoly_psum M u : (q < M)%N -> psum b 0 M u = Bpoly u.
Proof.
move=> lt; rewrite /psum (@big_cat_nat _ _ _ q.+1) //= [X in _ + X]big_nat_cond [X in _ + X]big1 ?addr0 //.
by move=> n /andP[/andP[le _] _]; rewrite b_fin ?mul0r.
Qed.

(* Finite form of  A(u) H(u) = B(u):  for every M,
   A(u) S_M(u) - B_M(u) = \sum_{j=1}^p a_j u^j \sum_{M-j <= n < M} h[n] u^n. *)
Lemma key_identity M u :
  Apoly u * psum h 0 M u - psum b 0 M u =
  \sum_(1 <= j < p.+1) a j * u ^+ j * psum h (M - j) M u.
Proof.
have -> : psum b 0 M u = psum h 0 M u + \sum_(1 <= j < p.+1) a j * psum (delay j h) 0 M u.
  rewrite /psum [X in _ + X](eq_bigr (fun j => \sum_(0 <= n < M) a j * delay j h n * u ^+ n)); last first.
    by move=> j _; rewrite mulr_sumr; apply: eq_bigr => n _; rewrite mulrA.
  rewrite [X in _ + X]exchange_big /= -big_split /=; apply: eq_bigr => n _.
  rewrite -(lrec_solves p a b n) mulrDl; congr (_ + _).
  by rewrite /fb mulr_suml.
rewrite /Apoly mulrDl mul1r mulr_suml opprD addrACA subrr add0r -sumrB.
apply: eq_bigr => j _.
rewrite psum_delay (@psum_split h (M - j) M) ?leq_subr //.
by ring.
Qed.

Lemma norm_psum (y : nat -> C) m M u : `|u| = 1 -> `|psum y m M u| <= \sum_(m <= n < M) `|y n|.
Proof.
move=> u1; apply: le_trans (ler_norm_sum _ _ _) _.
by apply: ler_sum => n _; rewrite normrM normrX u1 expr1n mulr1.
Qed.

Lemma window_mono (y : nat -> C) j M : (j <= p)%N ->
  \sum_(M - j <= n < M) `|y n| <= \sum_(M - p <= n < M) `|y n|.
Proof.
move=> lejp; rewrite [X in _ <= X](@big_cat_nat _ _ _ (M - j)) ?leq_subr //=.
  by rewrite lerDr sumr_ge0.
by rewrite leq_sub2l.
Qed.

(* Finite split: the length-L DFT of h is the partial sum S_L(u), and the
   series up to M differs from it by the "aliasing" term, bounded by the
   corresponding piece of the tail. *)
Lemma tf_split L M u : (L <= M)%N -> `|u| = 1 ->
  psum h 0 M u = psum h 0 L u + psum h L M u /\
  `|psum h L M u| <= \sum_(L <= n < M) `|h n|.
Proof. by move=> le u1; split; [exact: psum_split | exact: norm_psum]. Qed.

Variable (L : nat) (u : C) (T : C).
Hypothesis u1 : `|u| = 1.
Hypothesis A_neq0 : Apoly u != 0.
Hypothesis Htail : forall M, (L <= M)%N -> \sum_(L <= n < M) `|h n| <= T.
Hypothesis Hdecay : forall e, 0 < e -> exists M0, forall M, (M0 <= M)%N ->
  \sum_(M - p <= n < M) `|h n| <= e.

(* Proposition "Transfer function": the truncated series (= the DFT bin, see
   tf_dft below) differs from H = B/A by at most the tail T. *)
Theorem transfer_function_bound : `|psum h 0 L u - Bpoly u / Apoly u| <= T.
Proof.
set A1 := \sum_(1 <= j < p.+1) `|a j|.
have A1_ge0 : 0 <= A1 by rewrite sumr_ge0.
have nA_gt0 : 0 < `|Apoly u| by rewrite normr_gt0.
apply/ler_addgt0Pr => e e_gt0.
have eta_gt0 : 0 < e * `|Apoly u| / (A1 + 1).
  by rewrite divr_gt0 ?mulr_gt0 // ltr_wpDl.
have [M0 HM0] := Hdecay eta_gt0.
set M := maxn (maxn M0 L) q.+1.
have leM0 : (M0 <= M)%N by rewrite /M !leq_max leqnn.
have leL : (L <= M)%N by rewrite /M !leq_max leqnn orbT.
have ltq : (q < M)%N by rewrite /M leq_max leqnn orbT.
rewrite -[psum h 0 L u](addrK (psum h L M u)) -psum_split //.
rewrite addrAC; apply: le_trans (ler_normB _ _) _; rewrite [X in X <= _]addrC lerD //.
  by apply: le_trans (norm_psum _ _ _ u1) (Htail leL).
have -> : psum h 0 M u - Bpoly u / Apoly u =
          (Apoly u * psum h 0 M u - psum b 0 M u) / Apoly u.
  by rewrite Bpoly_psum // mulrBl mulrAC divff // mul1r.
rewrite key_identity normrM normfV ler_pdivrMr //.
apply: le_trans (ler_norm_sum _ _ _) _.
apply: le_trans (_ : \sum_(1 <= j < p.+1) `|a j| * (e * `|Apoly u| / (A1 + 1)) <= _).
  rewrite big_nat_cond [X in _ <= X]big_nat_cond.
  apply: ler_sum => j /andP[/andP[j_gt0 ltj] _].
  rewrite normrM normrM normrX u1 expr1n mulr1 ler_wpM2l //.
  apply: le_trans (norm_psum _ _ _ u1) _.
  by apply: le_trans (window_mono _ _ _) (HM0 _ leM0).
rewrite -mulr_suml -/A1 mulrCA ler_piMr ?mulr_ge0 ?normr_ge0 ?ltW //.
by rewrite ltr_pdivrMr ?ltr_wpDl // mul1r ltrDl.
Qed.

End TF.

(* The same statement written with the DFT of DFT.v: for any primitive L-th
   root of unity w (for instance Omega.omega L, the paper's e^{-2 pi i/L}),
   bin k of the length-L DFT of (h[0], ..., h[L-1]) is within T of
   H = B(w^k)/A(w^k). *)
Theorem tf_dft (C : numClosedFieldType) p q (a b : nat -> C)
  (b_fin : forall j, (q < j)%N -> b j = 0)
  L (w : C) (w_prim : L.-primitive_root w) k (T : C) :
  Apoly p a (w ^+ k) != 0 ->
  (forall M, (L <= M)%N -> \sum_(L <= n < M) `|h p a b n| <= T) ->
  (forall e, 0 < e -> exists M0, forall M, (M0 <= M)%N ->
     \sum_(M - p <= n < M) `|h p a b n| <= e) ->
  `|dft L w (h p a b) k - Bpoly q b (w ^+ k) / Apoly p a (w ^+ k)| <= T.
Proof.
move=> A_neq0 Htail Hdecay.
have u1 : `|w ^+ k| = 1 by rewrite normrX (norm_prim w_prim) expr1n.
have -> : dft L w (h p a b) k = psum (h p a b) 0 L (w ^+ k).
  rewrite /dft /psum big_mkord; apply: eq_bigr => n _.
  by rewrite exprM.
exact: transfer_function_bound.
Qed.
