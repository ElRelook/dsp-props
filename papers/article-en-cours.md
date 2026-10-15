# Article LaTeX : état au 15 octobre 2026 (travail en pause)

Objectif : article de recherche en 2 colonnes, 10 pt (dans `paper/article/`, à créer). Il suit le plan demandé dans la relecture : abstract, introduction, background et travaux connexes, contribution, résultats, conclusion, remerciements, déclaration d'usage de l'IA, conflits d'intérêts, références. `paper/paper.md` (JOSS) reste inchangé.

## Fait

- `dp.verify(..., seed=N)` rend une exécution reproductible (`src/dsp_props/api.py`).
- Étude des suites de tests (motivation) : `benchmarks/survey_test_suites.py`, résultats dans `benchmarks/survey_results.json`.
  - Checkouts utilisés : numpy 0820ec5, scipy 19a262b, librosa 08e2c0a, torchaudio 1255104.
  - Aucun test Hypothesis dans les 5 suites.
  - Dans scipy.signal, les tolérances fixées à la main couvrent 66 valeurs distinctes, de 1e-31 à 3.
  - 2 tests seulement combinent `zi` et une entrée vide.
- Comparaison avec l'état de la pratique (`benchmarks/comparison/`) :
  - `subjects/` : 4 implémentations correctes (FFT radix-2 + Bluestein, lfilter DF-II transposée, upfirdn polyphase, FIR par overlap-add par blocs). Toutes vérifiées contre NumPy/SciPy, erreur relative ≤ 1,6e-15.
  - `mutate.py` : mutants automatiques du premier ordre (AOR, BOR, ROR, CRP, UOI, MCR, SDL), soit 183 mutants (fft 76, lfilter 55, upfirdn 36, ola 16).
  - `suites.py` : déclarations dsp-props, suites « état de la pratique » portées des tests NumPy/SciPy (origine dans chaque docstring), et oracle de classification des mutants.
  - `approaches.py` : sop, dsp-props, dsp-props/uniform (sans générateurs métier), dsp-props/fixed-tol (rtol 1e-7), generic-pbt (les deux retirés).
  - Les sujets corrects passent toutes les suites et toutes les déclarations.

## À faire

1. `benchmarks/comparison/run_comparison.py` : classer les mutants contre l'oracle.
   - équivalent si l'erreur relative est ≤ 1e-12 ;
   - faute de précision si elle est comprise entre 1e-12 et 1e-6 ;
   - faute fonctionnelle au-delà de 1e-6, ou en cas d'exception ou de blocage.
   
   Puis lancer les 5 approches, avec 5 graines pour les approches aléatoires, en parallèle avec un délai maximal, et écrire un JSON.
2. Mutants faits main (31) : dsp-props et ses ablations, ainsi que generic-pbt, sur 5 graines.
3. Validation de l'outil :
   - faux positifs sur les références, sur 20 graines ;
   - distribution de erreur/tolérance ;
   - `longdouble_dft` et `longdouble_lfilter` contre mpmath ;
   - audit des générateurs ;
   - preuves des relations en annexe.
4. Vérifier les références bibliographiques. Pistes : Ergün 1995 et Frigo & Johnson 2005 (auto-test de FFTW), Blum–Luby–Rubinfeld 1993, Ergün–Kumar–Rubinfeld 2001, Di Franco et al. 2017, Kanewala & Bieman, Segura et al. 2016, pluginval.
5. Rédiger le LaTeX : classe `article` en twocolumn 10 pt, `mathptmx`, `ieeetr.bst`. IEEEtran n'est pas installé dans l'environnement cloud. Définir chaque abréviation à sa première occurrence et placer les rapports de bugs en conclusion.

## Point important à corriger dans l'article

La partie `lfilter` de scipy#26406 était déjà connue : [scipy#22571](https://github.com/scipy/scipy/issues/22571), reproduite sur 1.15.2. Le dépôt SciPy de développement contient maintenant `test_lfilter_empty_input`, qui cite gh-22571. dsp-props l'a donc **redécouvert** indépendamment.

La nouveauté porte sur `sosfilt` (et sur l'impact librosa). Avant de poster les tickets 1 et 2, vérifier qu'ils ne font pas doublon.
