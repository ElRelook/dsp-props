(* Appendix A, Propositions "Linearity" (DFT part), "Circular shift",
   "Parseval", "Hermitian symmetry", "Inversion and convolution".

   The DFT of length N is  F x [k] = \sum_{n<N} x[n] w^{k n}  where w is any
   primitive N-th root of unity.  The algebraic results (linearity, shift,
   inversion, convolution) are proved over an arbitrary field; Parseval and
   Hermitian symmetry over an arbitrary numClosedFieldType (an algebraically
   closed field with a conjugation and a norm, e.g. the complex numbers R[i]
   of a real-closed field, or algC).  File Omega.v instantiates w with the
   paper's  e^{-2 pi i/N} = cos(2pi/N) - i sin(2pi/N)  in R[i]. *)

From mathcomp Require Import all_ssreflect all_algebra.

Set Implicit Arguments.
Unset Strict Implicit.
Unset Printing Implicit Defensive.

Import GRing.Theory Num.Theory.
Local Open Scope ring_scope.

(* ------------------------------------------------------------------------- *)
(* A primitive N-th root of unity in a field forces N%:R <> 0.               *)
(* ------------------------------------------------------------------------- *)

Lemma prim_root_natr_neq0 (F : fieldType) (N : nat) (w : F) :
  N.-primitive_root w -> N%:R != 0 :> F.
Proof.
move=> prim.
have N_gt0 := prim_order_gt0 prim.
have Hfac := factor_Xn_sub_1 prim.
have Hsum : 'X^N - 1 = ('X - 1) * \sum_(i < N) 'X^i :> {poly F}.
  by rewrite subrX1.
move: Hfac Hsum; case: N prim N_gt0 => // n prim _.
rewrite big_nat_recl // expr0 => <-.
have X1_neq0 : ('X - 1%:P) != 0 :> {poly F} by rewrite polyXsubC_eq0.
move/(mulfI X1_neq0) => /(congr1 (fun p => p.[1])).
rewrite horner_sum horner_prod.
have -> : \sum_(i < n.+1) ('X^i : {poly F}).[1] = n.+1%:R.
  by rewrite (eq_bigr (fun _ => 1)) ?sumr_const ?card_ord // => i _; rewrite hornerXn expr1n.
move=> <-.
rewrite prodf_seq_neq0; apply/allP => i; rewrite mem_index_iota => /andP[_ lti] /=.
rewrite hornerXsubC subr_eq0 eq_sym -(prim_order_dvd prim).
by rewrite /dvdn modn_small.
Qed.

(* ------------------------------------------------------------------------- *)
(* The DFT over a field with a primitive N-th root of unity.                 *)
(* Sequences are functions nat -> F; only the samples 0..N-1 are used.        *)
(* ------------------------------------------------------------------------- *)

Section DFTField.

Variable F : fieldType.
Variable N : nat.
Variable w : F.
Hypothesis w_prim : N.-primitive_root w.

Let N_gt0 : (0 < N)%N := prim_order_gt0 w_prim.

Definition dft (x : nat -> F) (k : nat) : F := \sum_(n < N) x n * w ^+ (k * n).

(* Circular shift: x_s[n] = x[(n - s) mod N]. *)
Definition cshift (s : nat) (x : nat -> F) (n : nat) : F :=
  x ((n + (N - s %% N)) %% N)%N.

(* Circular convolution: conv(x,y)[n] = \sum_{m<N} x[m] y[(n - m) mod N]. *)
Definition cconv (x y : nat -> F) (n : nat) : F :=
  \sum_(m < N) x m * cshift m y n.

(* Inverse DFT: x[n] = N^-1 \sum_{k<N} X[k] w^{-k n}. *)
Definition idft (X : nat -> F) (n : nat) : F :=
  N%:R^-1 * \sum_(k < N) X k * w^-1 ^+ (k * n).

Lemma w_neq0 : w != 0.
Proof.
apply/eqP => w0; move: (prim_expr_order w_prim).
by rewrite w0 expr0n eqn0Ngt N_gt0 /= => /eqP; rewrite eq_sym oner_eq0.
Qed.

Lemma wk_order k : (w ^+ k) ^+ N = 1.
Proof. by rewrite exprAC (prim_expr_order w_prim) expr1n. Qed.

(* Proposition "Linearity" (DFT part). *)
Theorem dft_linear (a b : F) (x y : nat -> F) k :
  dft (fun n => a * x n + b * y n) k = a * dft x k + b * dft y k.
Proof.
rewrite /dft !mulr_sumr -big_split /=; apply: eq_bigr => n _.
by rewrite mulrDl !mulrA.
Qed.

Lemma dft_periodic x k : dft x (k + N) = dft x k.
Proof.
apply: eq_bigr => n _; congr (_ * _).
by rewrite !exprM exprD (prim_expr_order w_prim) mulr1.
Qed.

(* Rotation of the summation index modulo N. *)
Lemma sum_rot (G : nat -> F) s :
  \sum_(n < N) G ((n + s) %% N)%N = \sum_(n < N) G n.
Proof.
pose f (i : 'I_N) : 'I_N := Ordinal (ltn_pmod (i + s)%N N_gt0).
have f_inj : injective f.
  move=> i j /(congr1 val) /= /eqP; rewrite eqn_modDr !modn_small ?ltn_ord // => /eqP.
  exact: val_inj.
by rewrite [RHS](reindex_inj f_inj).
Qed.

(* Proposition "Circular shift". *)
Theorem dft_cshift s x k : dft (cshift s x) k = w ^+ (k * s) * dft x k.
Proof.
rewrite /dft mulr_sumr.
rewrite -(sum_rot (fun n => cshift s x n * w ^+ (k * n)) (s %% N)%N).
apply: eq_bigr => m _; rewrite /cshift.
have s_lt : (s %% N < N)%N by rewrite ltn_mod.
rewrite modnDml -addnA subnKC ?(ltnW s_lt) // modnDr modn_small ?ltn_ord //.
rewrite mulrCA; congr (_ * _).
rewrite !exprM (expr_mod _ (wk_order k)) exprD (expr_mod _ (wk_order k)).
by rewrite mulrC.
Qed.

(* Orthogonality of the characters. *)
Lemma sum_expr_prim j :
  \sum_(k < N) w ^+ (k * j) = if (N %| j)%N then N%:R else 0.
Proof.
case: ifP => [dvd | ndvd].
  rewrite (eq_bigr (fun _ => 1)) ?sumr_const ?card_ord // => k _.
  move: dvd; rewrite (prim_order_dvd w_prim) => /eqP wj1.
  by rewrite mulnC exprM wj1 expr1n.
have wj1 : w ^+ j - 1 != 0.
  by rewrite subr_eq0 -(prim_order_dvd w_prim) ndvd.
apply/eqP; rewrite -(mulrI_eq0 _ (mulfI wj1)).
under eq_bigr do rewrite mulnC exprM.
by rewrite -subrX1 -exprM mulnC exprM (prim_expr_order w_prim) expr1n subrr.
Qed.

Lemma winv : w^-1 = w ^+ N.-1.
Proof.
apply: (mulfI w_neq0); rewrite mulfV ?w_neq0 // -exprS prednK //.
by rewrite (prim_expr_order w_prim).
Qed.

Lemma orth n m : (n < N)%N -> (m < N)%N ->
  \sum_(k < N) w ^+ (k * n) * w^-1 ^+ (k * m) = if n == m then N%:R else 0.
Proof.
move=> ltn ltm.
under eq_bigr do rewrite winv -exprM -exprD mulnCA -mulnDr.
rewrite sum_expr_prim; congr (if _ then _ else _).
rewrite /dvdn -[0%N](mod0n N) -(eqn_modDr m) add0n -addnA.
rewrite -mulSnr prednK // mulnC addnC modnMDl !modn_small //.
Qed.

Hypothesis N_neq0 : N%:R != 0 :> F.

(* Proposition "Inversion and convolution", first part. *)
Theorem dft_inv x n : (n < N)%N -> idft (dft x) n = x n.
Proof.
move=> ltn; rewrite /idft /dft.
under eq_bigr do rewrite mulr_suml.
rewrite exchange_big /=.
under eq_bigr do (under eq_bigr do rewrite -mulrA; rewrite -mulr_sumr orth ?ltn_ord //).
rewrite (bigD1 (Ordinal ltn)) //= eqxx big1 ?addr0; last first.
  by move=> i /negPf; rewrite -val_eqE /= => ->; rewrite mulr0.
by rewrite mulrC mulfK.
Qed.

Lemma dft_cconv x y k : dft (cconv x y) k = dft x k * dft y k.
Proof.
rewrite /dft /cconv.
under eq_bigr do rewrite mulr_suml.
rewrite exchange_big /= mulr_suml; apply: eq_bigr => m _.
under eq_bigr do rewrite -mulrA.
rewrite -mulr_sumr.
have -> : \sum_(i < N) cshift m y i * w ^+ (k * i) = dft (cshift m y) k by [].
by rewrite dft_cshift mulrA.
Qed.

Lemma eq_idft (X Y : nat -> F) n :
  (forall k, (k < N)%N -> X k = Y k) -> idft X n = idft Y n.
Proof.
by move=> XY; rewrite /idft; congr (_ * _); apply: eq_bigr => k _; rewrite XY.
Qed.

(* Proposition "Inversion and convolution", second part. *)
Theorem idft_cconv x y n : (n < N)%N ->
  idft (fun k => dft x k * dft y k) n = cconv x y n.
Proof.
move=> ltn; rewrite -(dft_inv (cconv x y) ltn).
by apply: eq_idft => k _; rewrite dft_cconv.
Qed.

End DFTField.

(* Versions without the hypothesis N%:R != 0, which follows from primitivity. *)
Theorem dft_inversion (F : fieldType) N (w : F) (w_prim : N.-primitive_root w)
  (x : nat -> F) n :
  (n < N)%N -> idft N w (dft N w x) n = x n.
Proof. exact: (dft_inv w_prim (prim_root_natr_neq0 w_prim)). Qed.

Theorem dft_convolution (F : fieldType) N (w : F) (w_prim : N.-primitive_root w)
  (x y : nat -> F) n :
  (n < N)%N -> idft N w (fun k => dft N w x k * dft N w y k) n = cconv N x y n.
Proof. exact: (idft_cconv w_prim (prim_root_natr_neq0 w_prim)). Qed.

(* ------------------------------------------------------------------------- *)
(* Parseval and Hermitian symmetry over a numClosedFieldType (e.g. complex   *)
(* numbers), where conjugation ^* and the norm `|.| are available.            *)
(* ------------------------------------------------------------------------- *)

Section DFTComplex.

Variable C : numClosedFieldType.
Variable N : nat.
Variable w : C.
Hypothesis w_prim : N.-primitive_root w.

Let N_gt0 : (0 < N)%N := prim_order_gt0 w_prim.

Lemma norm_prim : `|w| = 1.
Proof.
apply/eqP; rewrite -(pexpr_eq1 N_gt0) ?normr_ge0 //.
by rewrite -normrX (prim_expr_order w_prim) normr1.
Qed.

Lemma conj_prim : w^* = w^-1.
Proof.
apply: (mulfI (w_neq0 w_prim)); rewrite mulfV ?(w_neq0 w_prim) //.
by rewrite -normCK norm_prim expr1n.
Qed.

Lemma conj_dft x k : (dft N w x k)^* = \sum_(n < N) (x n)^* * w^-1 ^+ (k * n).
Proof.
rewrite /dft rmorph_sum; apply: eq_bigr => n _.
by rewrite rmorphM rmorphXn conj_prim.
Qed.

(* Proposition "Parseval". *)
Theorem parseval (x : nat -> C) :
  \sum_(k < N) `|dft N w x k| ^+ 2 = N%:R * \sum_(n < N) `|x n| ^+ 2.
Proof.
under eq_bigr do rewrite normCK conj_dft {1}/dft mulr_suml.
under eq_bigr do (under eq_bigr do rewrite mulr_sumr).
rewrite exchange_big /=.
under eq_bigr do rewrite exchange_big /=.
rewrite mulr_sumr; apply: eq_bigr => n _.
under eq_bigr do (under eq_bigr do rewrite mulrACA; rewrite -mulr_sumr orth ?ltn_ord //).
rewrite (bigD1 n) //= eqxx big1 ?addr0; last first.
  by move=> i /negPf; rewrite eq_sym -val_eqE /= => ->; rewrite mulr0.
by rewrite normCK mulrC.
Qed.

(* Proposition "Hermitian symmetry". *)
Theorem dft_hermitian (x : nat -> C) k :
  (forall n, (n < N)%N -> x n \is Num.real) -> (k <= N)%N ->
  dft N w x (N - k) = (dft N w x k)^*.
Proof.
move=> xreal lekN; rewrite conj_dft; apply: eq_bigr => n _.
have /CrealP -> := xreal n (ltn_ord n).
congr (_ * _); apply: (mulIf (expf_neq0 (k * n) (w_neq0 w_prim))).
rewrite -exprD -mulnDl subnK // exprM (prim_expr_order w_prim) expr1n.
by rewrite exprVn mulVf // expf_neq0 // (w_neq0 w_prim).
Qed.

Theorem dft_dc_real (x : nat -> C) :
  (forall n, (n < N)%N -> x n \is Num.real) -> dft N w x 0 \is Num.real.
Proof.
move=> xreal; apply/CrealP.
rewrite -(dft_hermitian xreal (leq0n N)) subn0 -[N]add0n.
by rewrite (dft_periodic w_prim).
Qed.

Theorem dft_nyquist_real (x : nat -> C) :
  (forall n, (n < N)%N -> x n \is Num.real) -> ~~ odd N ->
  dft N w x N./2 \is Num.real.
Proof.
move=> xreal even_N; apply/CrealP.
have le : (N./2 <= N)%N by rewrite -[X in (_ <= X)%N](odd_double_half N) -addnn addnA leq_addl.
rewrite -(dft_hermitian xreal le); congr (dft _ _ _ _).
by rewrite -{1}(odd_double_half N) (negPf even_N) add0n -addnn addnK.
Qed.

End DFTComplex.
