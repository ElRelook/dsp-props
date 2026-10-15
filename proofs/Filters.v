(* Appendix A, Propositions "Linearity" (filter part), "Time invariance and
   causality on finite sequences", "Bounded gain"; and the facts about linear
   recursions used by Appendix B and by the "Transfer function" proposition.

   Signals are functions nat -> R, zero-extended to negative indices: a
   finite signal of length N is any function whose values at n >= N are
   ignored (every statement below is pointwise in n, so it holds on every
   window [0, N)).  A causal LTI filter applied from zero state is the causal
   convolution  conv h x n = \sum_{m <= n} h[n-m] x[m]. *)

From mathcomp Require Import all_ssreflect all_algebra.

Set Implicit Arguments.
Unset Strict Implicit.
Unset Printing Implicit Defensive.

Import Order.TTheory GRing.Theory Num.Theory.
Local Open Scope ring_scope.

Section Conv.

Variable R : comRingType.
Implicit Types (h x y d : nat -> R).

(* [0_s, x] : the signal x delayed by s samples, with s leading zeros. *)
Definition delay (s : nat) x (n : nat) : R := if (s <= n)%N then x (n - s)%N else 0.

(* Causal LTI filter from zero state (convolution truncated at n). *)
Definition conv h x (n : nat) : R := \sum_(0 <= m < n.+1) h (n - m)%N * x m.

Definition dirac (n : nat) : R := (n == 0%N)%:R.

(* Proposition "Linearity", filter part. *)
Theorem conv_linear (a b : R) h x y n :
  conv h (fun m => a * x m + b * y m) n = a * conv h x n + b * conv h y n.
Proof.
rewrite /conv !mulr_sumr -big_split /=; apply: eq_bigr => m _.
by rewrite mulrDr !(mulrCA (h _)).
Qed.

Lemma conv_scale (a : R) h x n : conv h (fun m => a * x m) n = a * conv h x n.
Proof. by rewrite /conv mulr_sumr; apply: eq_bigr => m _; rewrite mulrCA. Qed.

Lemma conv_add h x y n : conv h (fun m => x m + y m) n = conv h x n + conv h y n.
Proof. by rewrite /conv -big_split; apply: eq_bigr => m _; rewrite mulrDr. Qed.

Lemma conv_sum (I : Type) (r : seq I) (P : pred I) (F : I -> nat -> R) h n :
  conv h (fun m => \sum_(i <- r | P i) F i m) n = \sum_(i <- r | P i) conv h (F i) n.
Proof.
rewrite /conv; under eq_bigr do rewrite mulr_sumr.
by rewrite exchange_big.
Qed.

Lemma convC h x n : conv h x n = conv x h n.
Proof.
rewrite /conv big_nat_rev /= add0n.
rewrite big_nat_cond [RHS]big_nat_cond; apply: eq_bigr => m /andP[/andP[_ lt] _].
by rewrite subSS subKn 1?mulrC // -ltnS.
Qed.

Lemma conv_dirac h n : conv h dirac n = h n.
Proof.
rewrite /conv big_nat_recl // subn0 /dirac eqxx mulr1 big1 ?addr0 //.
by move=> i _; rewrite mulr0.
Qed.

Lemma conv_ext h x y n :
  (forall m, (m <= n)%N -> x m = y m) -> conv h x n = conv h y n.
Proof.
move=> xy; rewrite /conv big_nat_cond [RHS]big_nat_cond.
by apply: eq_bigr => m /andP[/andP[_ lt] _]; rewrite xy.
Qed.

(* Proposition "Time invariance and causality on finite sequences", (i):
   f([0_s, x]) = [0_s, f(x)], at every sample (hence on N + s samples). *)
Theorem conv_delay h x s n : conv h (delay s x) n = delay s (conv h x) n.
Proof.
rewrite /delay; case: leqP => [le_sn | lt_ns]; last first.
  rewrite /conv big_nat_cond big1 // => m /andP[/andP[_ lt] _].
  by rewrite ifF ?mulr0 // ltn_geF // (leq_trans lt).
rewrite /conv (@big_cat_nat _ _ _ s _ _ _ _ (leq0n s) (leqW le_sn)) /=.
rewrite big_nat_cond big1 ?add0r; last first.
  by move=> m /andP[/andP[_ lt] _]; rewrite ifF ?mulr0 // ltn_geF.
rewrite -[X in \sum_(X <= _ < _) _]add0n big_addn subSn //.
apply: eq_bigr => i _; rewrite leq_addl addnK addnC subnDA.
by [].
Qed.

(* Proposition "Time invariance and causality on finite sequences", (ii). *)
Theorem conv_causal h x x' k :
  (forall m, (m < k)%N -> x m = x' m) ->
  forall n, (n < k)%N -> conv h x n = conv h x' n.
Proof.
move=> xx' n ltnk; apply: conv_ext => m le; apply: xx'.
exact: leq_ltn_trans le ltnk.
Qed.

(* ------------------------------------------------------------------------ *)
(* Linear recursions  y[n] + \sum_{j=1}^p a_j y[n-j] = d[n]  (a_0 = 1),     *)
(* from zero state.                                                          *)
(* ------------------------------------------------------------------------ *)

Variable p : nat.
Variable a : nat -> R.

Definition fb y (n : nat) : R := \sum_(1 <= j < p.+1) a j * delay j y n.

Definition solves d y := forall n, y n + fb y n = d n.

Fixpoint lrec_aux (k : nat) d : nat -> R :=
  match k with
  | 0 => fun _ => 0
  | k'.+1 => fun n => d n - fb (lrec_aux k' d) n
  end.

(* The (unique) solution from zero state. *)
Definition lrec d (n : nat) : R := lrec_aux n.+1 d n.

Lemma fb_ext y z n :
  (forall m, (m < n)%N -> y m = z m) -> fb y n = fb z n.
Proof.
move=> yz; rewrite /fb big_nat_cond [RHS]big_nat_cond.
apply: eq_bigr => j /andP[/andP[j_gt0 _] _]; rewrite /delay.
case: leqP => // le; rewrite yz //.
by rewrite ltn_subrL j_gt0 (leq_trans j_gt0 le).
Qed.

Lemma lrec_aux_stable d k1 k2 n :
  (n < k1)%N -> (n < k2)%N -> lrec_aux k1 d n = lrec_aux k2 d n.
Proof.
elim: k1 k2 n => // k1 IH [|k2] n // lt1 lt2 /=.
congr (_ - _); apply: fb_ext => m ltm; apply: IH.
  exact: leq_trans ltm _.
exact: leq_trans ltm _.
Qed.

Lemma lrec_solves d : solves d (lrec d).
Proof.
move=> n; rewrite /lrec /= (@fb_ext (lrec_aux n d) (lrec d)) ?subrK //.
by move=> m ltm; rewrite /lrec (lrec_aux_stable d (k2 := m.+1) ltm).
Qed.

Lemma solves_unique d y z : solves d y -> solves d z -> forall n, y n = z n.
Proof.
move=> Hy Hz n; elim/ltn_ind: n => n IH.
have := Hy n; rewrite -(Hz n) (fb_ext (z := z)) //.
by move/addIr.
Qed.

(* Impulse response of 1/A. *)
Definition impresp : nat -> R := lrec dirac.

Lemma fb_conv x h n : fb (conv x h) n = conv x (fb h) n.
Proof.
rewrite /fb conv_sum; apply: eq_bigr => j _.
by rewrite conv_scale conv_delay.
Qed.

(* The solution of A(z) y = d from zero state is  y = h_A * d. *)
Theorem solves_conv d y : solves d y -> forall n, y n = conv impresp d n.
Proof.
move=> Hy n; rewrite convC; apply: (solves_unique Hy) => {}n.
rewrite fb_conv -conv_add.
rewrite (@conv_ext _ _ dirac); first exact: conv_dirac.
by move=> m _; apply: lrec_solves.
Qed.

(* Direct-form IIR filter B/A from zero state:  y + fb y = conv b x.  Its
   output is the convolution with the impulse response h_{B/A} = lrec b. *)
Theorem iir_conv b x y : solves (conv b x) y -> forall n, y n = conv (lrec b) x n.
Proof.
move=> Hy n; rewrite convC; apply: (solves_unique Hy) => {}n.
rewrite fb_conv -conv_add [RHS]convC.
by apply: conv_ext => m _; apply: lrec_solves.
Qed.

(* Proposition "Linearity" for a recursive (IIR) filter from zero state. *)
Lemma fb_linear (c : R) y z n :
  fb (fun m => c * y m + z m) n = c * fb y n + fb z n.
Proof.
rewrite /fb mulr_sumr -big_split; apply: eq_bigr => j _ /=; rewrite /delay.
by case: ifP => _; rewrite ?mulr0 ?addr0 // mulrDr mulrCA.
Qed.

Theorem lrec_linear (c : R) d d' n :
  lrec (fun m => c * d m + d' m) n = c * lrec d n + lrec d' n.
Proof.
apply: (solves_unique (lrec_solves _) (z := fun n => c * lrec d n + lrec d' n)) => {}n.
by rewrite fb_linear addrACA -mulrDr !lrec_solves.
Qed.

Theorem iir_linear (c : R) b x x' n :
  conv (lrec b) (fun m => c * x m + x' m) n =
  c * conv (lrec b) x n + conv (lrec b) x' n.
Proof. by rewrite -[X in _ = _ + X]mul1r -conv_linear; apply: conv_ext => m _; rewrite mul1r. Qed.

End Conv.

(* ------------------------------------------------------------------------- *)
(* Proposition "Bounded gain".                                               *)
(* ------------------------------------------------------------------------- *)

Section Gain.

Variable R : realDomainType.
Implicit Types (h x : nat -> R).

Theorem bounded_gain h x (G : R) n :
  (forall m, (m <= n)%N -> `|x m| <= 1) ->
  (forall L, \sum_(0 <= i < L) `|h i| <= G) ->
  `|conv h x n| <= G.
Proof.
move=> xb hG; apply: le_trans (ler_norm_sum _ _ _) _.
apply: le_trans (hG n.+1).
rewrite (_ : \sum_(0 <= i < n.+1) `|h i| = \sum_(0 <= m < n.+1) `|h (n - m)%N|); last first.
  by rewrite big_nat_rev /= add0n; apply: eq_bigr => m _; rewrite subSS.
rewrite big_nat_cond [X in _ <= X]big_nat_cond; apply: ler_sum => m /andP[/andP[_ lt] _].
by rewrite normrM -[X in _ <= X]mulr1 ler_wpM2l ?xb // -ltnS.
Qed.

Definition sign_input h (n : nat) (m : nat) : R := Num.sg (h (n - m)%N).

Lemma sign_input_bounded h n m : `|sign_input h n m| <= 1.
Proof. by rewrite /sign_input normr_sg; case: (_ != 0) => /=; rewrite ?ler01 ?lexx. Qed.

Theorem sign_input_attains h n :
  conv h (sign_input h n) n = \sum_(0 <= i < n.+1) `|h i|.
Proof.
rewrite /conv /sign_input.
under eq_bigr do rewrite mulrC -normrEsg.
rewrite big_nat_rev /= add0n big_nat_cond [RHS]big_nat_cond.
apply: eq_bigr => m /andP[/andP[_ lt] _].
by rewrite subSS subKn // -ltnS.
Qed.

End Gain.
