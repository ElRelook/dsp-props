(* Appendix A, Proposition "Block invariance".  A streaming processor is a
   state machine  phi : Q -> X -> Q * Y  applied sample by sample; process
   runs it over a block from a given state and returns the final state and the
   outputs.  Processing any split of the input into blocks (empty blocks
   included), threading the state, gives the same outputs and final state as
   processing the whole input at once. *)

From mathcomp Require Import all_ssreflect.

Set Implicit Arguments.
Unset Strict Implicit.
Unset Printing Implicit Defensive.

Section Streaming.

Variables (Q X Y : Type).
Variable phi : Q -> X -> Q * Y.

Fixpoint process (q : Q) (xs : seq X) : Q * seq Y :=
  match xs with
  | [::] => (q, [::])
  | x :: xs' =>
      let (q1, y) := phi q x in
      let (q2, ys) := process q1 xs' in (q2, y :: ys)
  end.

(* Feed the blocks one after the other, storing the state between calls and
   concatenating the outputs. *)
Fixpoint process_blocks (q : Q) (bs : seq (seq X)) : Q * seq Y :=
  match bs with
  | [::] => (q, [::])
  | b :: bs' =>
      let (q1, ys1) := process q b in
      let (q2, ys2) := process_blocks q1 bs' in (q2, ys1 ++ ys2)
  end.

Lemma process_nil q : process q [::] = (q, [::]).
Proof. by []. Qed.

Lemma process_cat q xs1 xs2 :
  process q (xs1 ++ xs2) =
  let (q1, ys1) := process q xs1 in
  let (q2, ys2) := process q1 xs2 in (q2, ys1 ++ ys2).
Proof.
elim: xs1 q => [|x xs1 IH] q /=; first by case: (process q xs2).
case: (phi q x) => q1 y; rewrite IH.
by case: (process q1 xs1) => q2 ys1; case: (process q2 xs2).
Qed.

(* Proposition "Block invariance". *)
Theorem block_invariance q (bs : seq (seq X)) :
  process_blocks q bs = process q (flatten bs).
Proof.
elim: bs q => [|b bs IH] q //=.
rewrite process_cat; case: (process q b) => q1 ys1.
by rewrite IH.
Qed.

(* In particular, the concatenated outputs do not depend on the split. *)
Corollary block_invariance_outputs q (bs : seq (seq X)) :
  (process_blocks q bs).2 = (process q (flatten bs)).2.
Proof. by rewrite block_invariance. Qed.

End Streaming.
