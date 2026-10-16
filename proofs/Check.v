(* Prints the axioms each main theorem depends on. *)
From mathcomp Require Import all_ssreflect.
From DSPProofs Require Import DFT Filters Multirate Streaming TransferFunction IIRBound Omega.

(* DFT.v *)
Goal True. idtac "--- prim_root_natr_neq0". Abort.
Print Assumptions prim_root_natr_neq0.
Goal True. idtac "--- dft_linear". Abort.
Print Assumptions dft_linear.
Goal True. idtac "--- dft_cshift". Abort.
Print Assumptions dft_cshift.
Goal True. idtac "--- parseval". Abort.
Print Assumptions parseval.
Goal True. idtac "--- dft_hermitian". Abort.
Print Assumptions dft_hermitian.
Goal True. idtac "--- dft_dc_real". Abort.
Print Assumptions dft_dc_real.
Goal True. idtac "--- dft_nyquist_real". Abort.
Print Assumptions dft_nyquist_real.
Goal True. idtac "--- dft_inversion". Abort.
Print Assumptions dft_inversion.
Goal True. idtac "--- dft_convolution". Abort.
Print Assumptions dft_convolution.
(* Filters.v *)
Goal True. idtac "--- conv_linear". Abort.
Print Assumptions conv_linear.
Goal True. idtac "--- lrec_linear". Abort.
Print Assumptions lrec_linear.
Goal True. idtac "--- iir_linear". Abort.
Print Assumptions iir_linear.
Goal True. idtac "--- iir_conv". Abort.
Print Assumptions iir_conv.
Goal True. idtac "--- solves_conv". Abort.
Print Assumptions solves_conv.
Goal True. idtac "--- conv_delay". Abort.
Print Assumptions conv_delay.
Goal True. idtac "--- conv_causal". Abort.
Print Assumptions conv_causal.
Goal True. idtac "--- bounded_gain". Abort.
Print Assumptions bounded_gain.
Goal True. idtac "--- sign_input_bounded". Abort.
Print Assumptions sign_input_bounded.
Goal True. idtac "--- sign_input_attains". Abort.
Print Assumptions sign_input_attains.
(* Multirate.v *)
Goal True. idtac "--- resample_linear". Abort.
Print Assumptions resample_linear.
Goal True. idtac "--- resample_periodic_ti". Abort.
Print Assumptions resample_periodic_ti.
(* Streaming.v *)
Goal True. idtac "--- block_invariance". Abort.
Print Assumptions block_invariance.
(* TransferFunction.v *)
Goal True. idtac "--- tf_split". Abort.
Print Assumptions tf_split.
Goal True. idtac "--- transfer_function_bound". Abort.
Print Assumptions transfer_function_bound.
Goal True. idtac "--- tf_dft". Abort.
Print Assumptions tf_dft.
(* IIRBound.v *)
Goal True. idtac "--- cauchy_schwarz". Abort.
Print Assumptions cauchy_schwarz.
Goal True. idtac "--- young". Abort.
Print Assumptions young.
Goal True. idtac "--- err_conv". Abort.
Print Assumptions err_conv.
Goal True. idtac "--- err_young". Abort.
Print Assumptions err_young.
Goal True. idtac "--- delta_bound". Abort.
Print Assumptions delta_bound.
Goal True. idtac "--- yhat_bound". Abort.
Print Assumptions yhat_bound.
Goal True. idtac "--- iir_error_implicit". Abort.
Print Assumptions iir_error_implicit.
Goal True. idtac "--- iir_error_bound". Abort.
Print Assumptions iir_error_bound.
Goal True. idtac "--- iir_error_c4". Abort.
Print Assumptions iir_error_c4.
Goal True. idtac "--- gamma_le". Abort.
Print Assumptions gamma_le.
Goal True. idtac "--- iir_error_gamma". Abort.
Print Assumptions iir_error_gamma.
(* Omega.v : the paper's omega = e^{-2 pi i/N} in R[i], R a realType *)
Goal True. idtac "--- omega_prim". Abort.
Print Assumptions omega_prim.
Goal True. idtac "--- paper_dft_linear". Abort.
Print Assumptions paper_dft_linear.
Goal True. idtac "--- paper_dft_cshift". Abort.
Print Assumptions paper_dft_cshift.
Goal True. idtac "--- paper_parseval". Abort.
Print Assumptions paper_parseval.
Goal True. idtac "--- paper_hermitian". Abort.
Print Assumptions paper_hermitian.
Goal True. idtac "--- paper_dc_nyquist_real". Abort.
Print Assumptions paper_dc_nyquist_real.
Goal True. idtac "--- paper_inversion". Abort.
Print Assumptions paper_inversion.
Goal True. idtac "--- paper_convolution". Abort.
Print Assumptions paper_convolution.
Goal True. idtac "--- paper_transfer_function". Abort.
Print Assumptions paper_transfer_function.
