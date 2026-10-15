(* Appendix B, "Error bound of a linear recursion".

   Exact-arithmetic part of the argument, over an arbitrary real closed field
   R (e.g. the reals).  The floating-point standard model is NOT formalised:
   the computed output yh is an arbitrary sequence, the local error
     delta[n] = yh[n] - (\sum_j b_j x[n-j] - \sum_{j>=1} a_j yh[n-j])
   is defined from it, and the componentwise bound
     |delta[n]| <= g (\sum_j |b_j||x[n-j]| + \sum_{j>=1} |a_j||yh[n-j]|)
   that the standard model gives with g = gamma_k is taken as a hypothesis.
   Norms are over the N computed samples [0, N). *)

From mathcomp Require Import all_ssreflect all_algebra.
From mathcomp.algebra_tactics Require Import ring lra.
From DSPProofs Require Import Filters.

Set Implicit Arguments.
Unset Strict Implicit.
Unset Printing Implicit Defensive.

Import Order.TTheory GRing.Theory Num.Theory.
Local Open Scope ring_scope.

(* ------------------------------------------------------------------------- *)
(* Cauchy-Schwarz for finite sums (Lagrange identity).                       *)
(* ------------------------------------------------------------------------- *)

Section CS.
Variable R : rcfType.

Lemma cauchy_schwarz (r : seq nat) (u v : nat -> R) :
  (\sum_(i <- r) u i * v i) ^+ 2 <=
  (\sum_(i <- r) u i ^+ 2) * (\sum_(i <- r) v i ^+ 2).
Proof.
set U := \sum_(i <- r) u i ^+ 2; set V := \sum_(i <- r) v i ^+ 2.
set P := \sum_(i <- r) u i * v i.
have E : \sum_(i <- r) \sum_(j <- r) (u i * v j - u j * v i) ^+ 2 = (U * V - P ^+ 2) *+ 2.
  have -> : U * V = \sum_(i <- r) \sum_(j <- r) u i ^+ 2 * v j ^+ 2.
    by rewrite /U mulr_suml; apply: eq_bigr => i _; rewrite mulr_sumr.
  have -> : P ^+ 2 = \sum_(i <- r) \sum_(j <- r) (u i * v i) * (u j * v j).
    by rewrite expr2 /P mulr_suml; apply: eq_bigr => i _; rewrite mulr_sumr.
  have S : \sum_(i <- r) \sum_(j <- r) u i ^+ 2 * v j ^+ 2 =
           \sum_(i <- r) \sum_(j <- r) u j ^+ 2 * v i ^+ 2.
    by rewrite exchange_big.
  rewrite mulrnBl mulr2n [X in X + _ - _]S -big_split /= -sumrMnl -sumrB.
  apply: eq_bigr => i _; rewrite -big_split /= -sumrMnl -sumrB.
  by apply: eq_bigr => j _; ring.
have : 0 <= (U * V - P ^+ 2) *+ 2.
  by rewrite -E sumr_ge0 // => i _; rewrite sumr_ge0 // => j _; rewrite sqr_ge0.
by rewrite pmulrn_lge0 // subr_ge0.
Qed.

End CS.

(* ------------------------------------------------------------------------- *)
(* l2 and l1 norms on the window [0, N).                                     *)
(* ------------------------------------------------------------------------- *)

Section Norms.
Variable R : rcfType.
Variable N : nat.
Implicit Types (u v h d : nat -> R).

Definition sq2 u : R := \sum_(0 <= n < N) u n ^+ 2.
Definition nrm2 u : R := Num.sqrt (sq2 u).
Definition nrm1 u : R := \sum_(0 <= n < N) `|u n|.

Lemma sq2_ge0 u : 0 <= sq2 u.
Proof. by rewrite sumr_ge0 // => n _; rewrite sqr_ge0. Qed.

Lemma nrm2_ge0 u : 0 <= nrm2 u.
Proof. exact: sqrtr_ge0. Qed.

Lemma nrm1_ge0 u : 0 <= nrm1 u.
Proof. by rewrite sumr_ge0. Qed.

Lemma nrm2_ext u v : (forall n, (n < N)%N -> u n = v n) -> nrm2 u = nrm2 v.
Proof.
move=> uv; rewrite /nrm2 /sq2 big_nat_cond [X in _ = Num.sqrt X]big_nat_cond.
by congr Num.sqrt; apply: eq_bigr => n /andP[/andP[_ lt] _]; rewrite uv.
Qed.

Lemma sqrt_le_sq (a b : R) : 0 <= b -> a <= b ^+ 2 -> Num.sqrt a <= b.
Proof.
move=> b_ge0 le; apply: le_trans (ler_wsqrtr le) _.
by rewrite sqrtr_sqr ger0_norm.
Qed.

Lemma nrm2_le u v : (forall n, (n < N)%N -> `|u n| <= `|v n|) -> nrm2 u <= nrm2 v.
Proof.
move=> uv; apply: ler_wsqrtr; rewrite /sq2 big_nat_cond [X in _ <= X]big_nat_cond.
apply: ler_sum => n /andP[/andP[_ lt] _].
by rewrite -(real_normK (num_real (u n))) -(real_normK (num_real (v n))) lerXn2r ?uv // nnegrE normr_ge0.
Qed.

Lemma nrm2_scale (c : R) u : nrm2 (fun n => c * u n) = `|c| * nrm2 u.
Proof.
rewrite /nrm2 /sq2 -sqrtr_sqr -sqrtrM ?sqr_ge0 // mulr_sumr.
by congr Num.sqrt; apply: eq_bigr => n _; rewrite exprMn.
Qed.

(* Minkowski inequality. *)
Lemma nrm2_add u v : nrm2 (fun n => u n + v n) <= nrm2 u + nrm2 v.
Proof.
apply: sqrt_le_sq; first by rewrite addr_ge0 ?nrm2_ge0.
rewrite sqrrD /nrm2 !sqr_sqrtr ?sq2_ge0 // /sq2.
have -> : \sum_(0 <= n < N) (u n + v n) ^+ 2 =
          \sum_(0 <= n < N) u n ^+ 2 + (\sum_(0 <= n < N) u n * v n) *+ 2 +
          \sum_(0 <= n < N) v n ^+ 2.
  by rewrite -sumrMnl -!big_split; apply: eq_bigr => n _ /=; rewrite sqrrD.
rewrite lerD2r lerD2l lerMn2r /=.
rewrite -sqrtrM ?sumr_ge0 // => [|n _]; last by rewrite sqr_ge0.
apply: le_trans (ler_norm _) _; rewrite -sqrtr_sqr ler_wsqrtr //.
exact: cauchy_schwarz.
Qed.

Lemma nrm2_sum (r : seq nat) (f : nat -> nat -> R) :
  nrm2 (fun n => \sum_(j <- r) f j n) <= \sum_(j <- r) nrm2 (f j).
Proof.
elim: r => [|j r IH].
  rewrite big_nil (@nrm2_ext _ (fun _ => 0)) => [|n _]; last by rewrite big_nil.
  by rewrite /nrm2 /sq2 big1 ?sqrtr0 // => n _; rewrite expr0n.
rewrite big_cons (@nrm2_ext _ (fun n => f j n + \sum_(j <- r) f j n)).
  by apply: le_trans (nrm2_add _ _) _; rewrite lerD2l.
by move=> n _; rewrite big_cons.
Qed.

Lemma nrm2_delay j u : nrm2 (delay j u) <= nrm2 u.
Proof.
apply: ler_wsqrtr; rewrite /sq2 /delay.
case: (leqP j N) => [le | lt]; last first.
  rewrite big_nat_cond big1 ?sumr_ge0 // => [n _|n /andP[/andP[_ ltn] _]].
    by rewrite sqr_ge0.
  by rewrite ifF ?expr0n // ltn_geF // (ltn_trans ltn).
rewrite (@big_cat_nat _ _ _ j) //= big_nat_cond big1 ?add0r; last first.
  by move=> n /andP[/andP[_ ltn] _]; rewrite ifF ?expr0n // ltn_geF.
rewrite -[X in \sum_(X <= _ < _) _]add0n big_addn.
rewrite [X in _ <= X](@big_cat_nat _ _ _ (N - j)) ?leq_subr //=.
rewrite (eq_bigr (fun i => u i ^+ 2)) => [|i _]; last by rewrite leq_addl addnK.
by rewrite lerDl sumr_ge0 // => i _; rewrite sqr_ge0.
Qed.

Lemma nrm1_delay j u : \sum_(0 <= n < N) `|delay j u n| <= nrm1 u.
Proof.
rewrite /nrm1 /delay.
case: (leqP j N) => [le | lt]; last first.
  rewrite big_nat_cond big1 ?sumr_ge0 // => n /andP[/andP[_ ltn] _].
  by rewrite ifF ?normr0 // ltn_geF // (ltn_trans ltn).
rewrite (@big_cat_nat _ _ _ j) //= big_nat_cond big1 ?add0r; last first.
  by move=> n /andP[/andP[_ ltn] _]; rewrite ifF ?normr0 // ltn_geF.
rewrite -[X in \sum_(X <= _ < _) _]add0n big_addn.
rewrite [X in _ <= X](@big_cat_nat _ _ _ (N - j)) ?leq_subr //=.
rewrite (eq_bigr (fun i => `|u i|)) => [|i _]; last by rewrite leq_addl addnK.
by rewrite lerDl sumr_ge0.
Qed.

(* Weighted Cauchy-Schwarz:  (sum w a)^2 <= (sum w) (sum w a^2), w >= 0. *)
Lemma wcauchy_schwarz (r : seq nat) (w c : nat -> R) :
  (forall i, 0 <= w i) ->
  (\sum_(i <- r) w i * c i) ^+ 2 <=
  (\sum_(i <- r) w i) * (\sum_(i <- r) w i * c i ^+ 2).
Proof.
move=> w_ge0.
have sw i : Num.sqrt (w i) ^+ 2 = w i by rewrite sqr_sqrtr.
have := cauchy_schwarz r (fun i => Num.sqrt (w i)) (fun i => Num.sqrt (w i) * c i).
under eq_bigr do rewrite mulrA -expr2 sw.
under [X in _ <= X * _]eq_bigr do rewrite sw.
by under [X in _ <= _ * X]eq_bigr do rewrite exprMn sw.
Qed.

(* Young's inequality  ||h * d||_2 <= ||h||_1 ||d||_2  on [0, N), for the
   causal convolution from zero state. *)
Theorem young h d : nrm2 (conv h d) <= nrm1 h * nrm2 d.
Proof.
set H := nrm1 h.
have H_ge0 : 0 <= H := nrm1_ge0 h.
have partial n : (n < N)%N -> \sum_(0 <= m < n.+1) `|h (n - m)%N| <= H.
  move=> ltn; rewrite big_nat_rev /= add0n.
  rewrite big_nat_cond (eq_bigr (fun i => `|h i|)) => [|i /andP[/andP[_ lti] _]]; last by rewrite subSS subKn // -ltnS.
  rewrite -big_nat_cond.
  rewrite /H /nrm1 [X in _ <= X](@big_cat_nat _ _ _ n.+1) //= lerDl.
  by rewrite sumr_ge0.
(* pointwise bound *)
have pt n : (n < N)%N ->
    conv h d n ^+ 2 <= H * \sum_(0 <= m < n.+1) `|h (n - m)%N| * d m ^+ 2.
  move=> ltn.
  apply: le_trans (_ : (\sum_(0 <= m < n.+1) `|h (n - m)%N| * `|d m|) ^+ 2 <= _).
    rewrite -(real_normK (num_real (conv h d n))) lerXn2r ?nnegrE ?normr_ge0 ?sumr_ge0 //.
      by move=> m _; rewrite mulr_ge0.
    apply: le_trans (ler_norm_sum _ _ _) _.
    by apply: ler_sum => m _; rewrite normrM.
  apply: le_trans (wcauchy_schwarz _ _ _) _ => [m|]; first exact: normr_ge0.
  under [X in _ * X <= _]eq_bigr do rewrite real_normK ?num_real //.
  rewrite ler_wpM2r ?partial //.
  by rewrite sumr_ge0 // => m _; rewrite mulr_ge0 ?sqr_ge0.
apply: sqrt_le_sq; first by rewrite mulr_ge0 ?nrm2_ge0.
rewrite exprMn /nrm2 sqr_sqrtr ?sq2_ge0 // /sq2.
apply: (@le_trans _ _ (\sum_(0 <= n < N) H *
   \sum_(0 <= m < N) (if (m <= n)%N then `|h (n - m)%N| * d m ^+ 2 else 0))).
  rewrite big_nat_cond [X in _ <= X]big_nat_cond.
  apply: ler_sum => n /andP[/andP[_ ltn] _]; apply: le_trans (pt n ltn) _.
  rewrite ler_wpM2l // [X in _ <= X](@big_cat_nat _ _ _ n.+1) //=.
  rewrite [X in _ <= _ + X]big_nat_cond [X in _ <= _ + X]big1 ?addr0; last first.
    by move=> m /andP[/andP[le _] _]; rewrite ifF // ltn_geF.
  rewrite big_nat_cond [X in _ <= X]big_nat_cond.
  by apply: ler_sum => m /andP[/andP[_ le] _]; rewrite ifT.
rewrite -mulr_sumr expr2 -mulrA ler_wpM2l //.
rewrite exchange_big /= mulr_sumr; apply: ler_sum => m _.
rewrite (eq_bigr (fun i => `|delay m h i| * d m ^+ 2)) => [|i _]; last first.
  by rewrite /delay; case: ifP; rewrite ?normr0 ?mul0r.
by rewrite -mulr_suml ler_wpM2r ?sqr_ge0 ?nrm1_delay.
Qed.

End Norms.

(* ------------------------------------------------------------------------- *)
(* The argument of Appendix B.                                               *)
(* ------------------------------------------------------------------------- *)

Section AppendixB.

Variable R : rcfType.
Variables (N p : nat).
Variables (a b x yh : nat -> R).  (* a_1..a_p (a_0 = 1), b, input, computed output *)
Variable g : R.                   (* gamma_k *)
Hypothesis g_ge0 : 0 <= g.

(* Exact output of the recursion from zero state:  y + \sum_j a_j y[.-j] = b * x. *)
Definition y_exact : nat -> R := lrec p a (conv b x).
(* Local error committed at step n by the computed output. *)
Definition delta (n : nat) : R := yh n - (conv b x n - fb p a yh n).
Definition err (n : nat) : R := yh n - y_exact n.
Definition hA : nat -> R := impresp p a.     (* impulse response of 1/A *)
Definition hBA : nat -> R := lrec p a b.     (* impulse response of B/A *)

(* Componentwise bound given by the standard model (assumed, not derived). *)
Hypothesis Hdelta : forall n, (n < N)%N ->
  `|delta n| <= g * (conv (fun j => `|b j|) (fun m => `|x m|) n +
                     \sum_(1 <= j < p.+1) `|a j| * `|delay j yh n|).

Let A1 := \sum_(1 <= j < p.+1) `|a j|.
Let B1 := nrm1 N b.
Let HA := nrm1 N hA.
Let G := nrm1 N hBA.
Let X := nrm2 N x.
Let E := nrm2 N err.

Lemma fb_sub (u v : nat -> R) n : fb p a (fun m => u m - v m) n = fb p a u n - fb p a v n.
Proof.
rewrite /fb -sumrB; apply: eq_bigr => j _; rewrite /delay.
by case: ifP => _; rewrite ?mulr0 ?subrr // mulrBr.
Qed.

(* A(z) e = delta, i.e.  e = h_A * delta  (exact). *)
Theorem err_conv n : err n = conv hA delta n.
Proof.
apply: (solves_conv (p := p) (a := a)) => {}n.
rewrite /err fb_sub /delta.
have Hy := lrec_solves p a (conv b x) n; rewrite -/y_exact in Hy.
rewrite -Hy; ring.
Qed.

(* Young:  ||e||_2 <= ||h_A||_1 ||delta||_2. *)
Theorem err_young : E <= HA * nrm2 N delta.
Proof. by rewrite /E (@nrm2_ext _ _ _ (conv hA delta)) ?young // => n _; rewrite err_conv. Qed.

Lemma nrm2_abs (u : nat -> R) : nrm2 N (fun n => `|u n|) = nrm2 N u.
Proof.
by apply/le_anti; rewrite !nrm2_le // => n _; rewrite normr_id.
Qed.

Lemma nrm1_abs (u : nat -> R) : nrm1 N (fun n => `|u n|) = nrm1 N u.
Proof. by apply: eq_bigr => n _; rewrite normr_id. Qed.

(* ||delta||_2 <= g (||b||_1 ||x||_2 + ||a_{1:}||_1 ||yh||_2). *)
Theorem delta_bound : nrm2 N delta <= g * (B1 * X + A1 * nrm2 N yh).
Proof.
set S1 := conv (fun j => `|b j|) (fun m => `|x m|).
set S2 := fun n => \sum_(1 <= j < p.+1) `|a j| * `|delay j yh n|.
have S1_ge0 n : 0 <= S1 n by rewrite sumr_ge0 // => m _; rewrite mulr_ge0.
have S2_ge0 n : 0 <= S2 n by rewrite sumr_ge0 // => m _; rewrite mulr_ge0.
apply: le_trans (_ : nrm2 N (fun n => g * (S1 n + S2 n)) <= _).
  apply: nrm2_le => n ltn; apply: le_trans (Hdelta ltn) _.
  by rewrite ger0_norm // mulr_ge0 // addr_ge0.
rewrite nrm2_scale ger0_norm // ler_wpM2l //.
apply: le_trans (nrm2_add _ S1 S2) _; apply: lerD.
  apply: le_trans (young _ _ _) _.
  by rewrite nrm1_abs nrm2_abs.
apply: le_trans (nrm2_sum _ _ _) _.
rewrite /A1 mulr_suml; apply: ler_sum => j _.
rewrite nrm2_scale normr_id ler_wpM2l //.
by rewrite nrm2_abs nrm2_delay.
Qed.

(* ||yh||_2 <= ||h_{B/A}||_1 ||x||_2 + ||e||_2. *)
Theorem yhat_bound : nrm2 N yh <= G * X + E.
Proof.
rewrite (@nrm2_ext _ _ _ (fun n => conv hBA x n + err n)); last first.
  move=> n _; rewrite /err -(iir_conv (lrec_solves p a (conv b x))) /y_exact.
  by rewrite addrC subrK.
apply: le_trans (nrm2_add _ _ _) _; rewrite lerD2r.
exact: young.
Qed.

Lemma nonneg : 0 <= A1 /\ 0 <= B1 /\ 0 <= HA /\ 0 <= G /\ 0 <= X /\ 0 <= E.
Proof.
by do !split; rewrite ?sumr_ge0 ?nrm1_ge0 ?nrm2_ge0.
Qed.

(* The exact inequality the argument yields:
     ||e|| <= g ||h_A||_1 (||b||_1 + ||a_{1:}||_1 ||h_{B/A}||_1) ||x|| + g ||h_A||_1 ||a_{1:}||_1 ||e||.
   Dropping the last (second-order) term gives the article's bound with c = 1. *)
Theorem iir_error_implicit : E <= g * HA * (B1 + A1 * G) * X + g * HA * A1 * E.
Proof.
have [A1_ge0 [B1_ge0 [HA_ge0 [G_ge0 [X_ge0 E_ge0]]]]] := nonneg.
apply: le_trans err_young _.
apply: le_trans (_ : HA * (g * (B1 * X + A1 * (G * X + E))) <= _).
  rewrite ler_wpM2l //; apply: le_trans delta_bound _.
  by rewrite ler_wpM2l // lerD2l ler_wpM2l // yhat_bound.
rewrite le_eqVlt; apply/orP; left; apply/eqP; ring.
Qed.

Theorem iir_error_bound : g * HA * A1 < 1 ->
  E <= g * HA * (B1 + A1 * G) * X / (1 - g * HA * A1).
Proof.
move=> small; rewrite ler_pdivlMr ?subr_gt0 //.
have := iir_error_implicit; rewrite mulrBr mulr1 lerBlDr.
by rewrite [X in _ <= _ + X]mulrC.
Qed.

(* With g = gamma_k = k eps / (1 - k eps): if k eps <= 1/2 then g <= 2 k eps, and
   if moreover g ||h_A||_1 ||a_{1:}||_1 <= 1/2, the bound holds rigorously with
   c = 4 (for one computed output against the exact one). *)
Theorem iir_error_c4 (keps : R) :
  g <= 2%:R * keps -> g * HA * A1 <= 2%:R^-1 ->
  E <= 4%:R * keps * HA * (B1 + A1 * G) * X.
Proof.
move=> g_le small.
have [A1_ge0 [B1_ge0 [HA_ge0 [G_ge0 [X_ge0 E_ge0]]]]] := nonneg.
set K := HA * (B1 + A1 * G) * X.
have K_ge0 : 0 <= K.
  by apply: mulr_ge0 => //; apply: mulr_ge0 => //; apply: addr_ge0 => //; apply: mulr_ge0.
have keps_ge0 : 0 <= keps.
  have : 0 <= 2%:R * keps by apply: le_trans g_le.
  by rewrite pmulr_rge0 ?ltr0n.
have half_lt1 : 2%:R^-1 < 1 :> R by rewrite invf_lt1 ?ltr1n.
have lt1 : g * HA * A1 < 1 by apply: le_lt_trans small half_lt1.
apply: le_trans (iir_error_bound lt1) _.
have -> : g * HA * (B1 + A1 * G) * X = g * K by rewrite /K; ring.
have -> : 4%:R * keps * HA * (B1 + A1 * G) * X = 4%:R * keps * K by rewrite /K; ring.
rewrite ler_pdivrMr ?subr_gt0 //.
apply: le_trans (_ : 2%:R * keps * K <= _).
  by rewrite ler_wpM2r.
have -> : 2%:R * keps * K = 4%:R * keps * K * 2%:R^-1.
  by field.
have half : 2%:R^-1 <= 1 - g * HA * A1.
  have h2 : 2%:R^-1 + 2%:R^-1 = 1 :> R by field.
  lra.
apply: ler_wpM2l half.
by apply: mulr_ge0 => //; apply: mulr_ge0; rewrite ?ler0n.
Qed.

End AppendixB.

(* gamma_k = k eps / (1 - k eps) <= 2 k eps when k eps <= 1/2. *)
Lemma gamma_le (R : rcfType) (keps : R) :
  0 <= keps -> keps <= 2%:R^-1 -> keps / (1 - keps) <= 2%:R * keps.
Proof.
move=> ke_ge0 ke_le.
have h2 : 2%:R^-1 + 2%:R^-1 = 1 :> R by field.
have pos : 0 < 1 - keps by lra.
rewrite ler_pdivrMr //.
have -> : 2%:R * keps * (1 - keps) = keps * (2%:R * (1 - keps)) by ring.
rewrite -[X in X <= _]mulr1 ler_wpM2l //.
have -> : 2%:R * (1 - keps) = (1 - keps) + (1 - keps) :> R by ring.
lra.
Qed.

(* Final statement in the article's terms: with gamma_k = k eps/(1 - k eps),
   k eps <= 1/2 and 2 k eps ||h_A||_1 ||a_{1:}||_1 <= 1/2,
     ||yh - y||_2 <= 4 k eps ||h_A||_1 (||b||_1 + ||a_{1:}||_1 ||h_{B/A}||_1) ||x||_2,
   i.e. the bound (eq:iir) with c = 4, rigorously, for one computation. *)
Theorem iir_error_gamma (R : rcfType) (N p : nat) (a b x yh : nat -> R) (keps : R) :
  0 <= keps -> keps <= 2%:R^-1 ->
  (forall n, (n < N)%N ->
     `|delta p a b x yh n| <= keps / (1 - keps) *
        (conv (fun j => `|b j|) (fun m => `|x m|) n +
         \sum_(1 <= j < p.+1) `|a j| * `|delay j yh n|)) ->
  2%:R * keps * nrm1 N (hA p a) * (\sum_(1 <= j < p.+1) `|a j|) <= 2%:R^-1 ->
  nrm2 N (err p a b x yh) <=
  4%:R * keps * nrm1 N (hA p a) *
    (nrm1 N b + (\sum_(1 <= j < p.+1) `|a j|) * nrm1 N (hBA p a b)) * nrm2 N x.
Proof.
move=> ke_ge0 ke_le Hdelta small.
have h2 : 2%:R^-1 + 2%:R^-1 = 1 :> R by field.
have pos : 0 < 1 - keps by lra.
have g_ge0 : 0 <= keps / (1 - keps) by rewrite divr_ge0 // ltW.
have g_le := gamma_le ke_ge0 ke_le.
apply: (iir_error_c4 g_ge0 Hdelta g_le).
apply: le_trans small; rewrite ler_wpM2r ?sumr_ge0 // ler_wpM2r ?nrm1_ge0 //.
Qed.
