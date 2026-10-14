# dsp-props

**Tests de propriété pour le traitement du signal** · *Property-based testing for DSP code*

Le code DSP est souvent testé en comparant sa sortie à une référence (MATLAB, SciPy) sur quelques signaux, avec une tolérance choisie à la main. `dsp-props` vérifie plutôt des **relations qui doivent toujours tenir** (linéarité, théorème du décalage, Parseval, symétrie hermitienne, inversibilité, théorème de convolution), sur des **signaux générés automatiquement** par [Hypothesis](https://hypothesis.works/) et choisis pour piéger le code : impulsions, sinusoïdes hors grille, tons proches, quasi-Nyquist, amplitudes extrêmes, longueurs 1, premières ou 2^k ± 1. Les tolérances dépendent de l'opération (erreur en O(ε log N) pour une FFT) au lieu d'un `atol` fixe.

> Statut : pré-alpha, phase 1 du [schéma directeur](docs/schema-directeur.md).

## Exemple

```python
import numpy as np
import dsp_props as dp

@dp.transform(inverse=np.fft.ifft, parseval=True, real_input_hermitian=True)
def my_fft(x):
    return np.fft.fft(x)

print(dp.verify(my_fft))
```

```
dsp-props report for my_fft
  ok   linearity
  ok   circular shift
  ok   parseval
  ok   hermitian symmetry
  ok   inversibility
  ok   convolution theorem
```

En cas d'échec, `verify` lève `PropertyViolation` avec, pour chaque relation violée, le contre-exemple réduit par Hypothesis.

Autres déclarations :

```python
# FFT réelle : l'inverse reçoit la longueur N
dp.transform(inverse=np.fft.irfft, kind="rdft", parseval=True)(np.fft.rfft)

# Transformée linéaire quelconque (DCT, ondelettes...)
dp.transform(kind="generic", inverse=idct_ortho, parseval=True, parseval_scale=lambda n: 1.0)(dct_ortho)

# Filtre LTI : linéarité, invariance temporelle, causalité, réponse en fréquence = B(z)/A(z).
# La tolérance suit le conditionnement de la récursion (IIRTolerance).
dp.lti_filter(causal=True, transfer=(b, a))(lambda x: scipy.signal.lfilter(b, a, x))

# Stabilité EBSB : aucune entrée bornée par 1 ne doit dépasser le gain déclaré (entrée pire cas construite)
dp.lti_filter(max_gain=l1_de_h)(mon_filtre)

# Rééchantillonneur rationnel L/M : linéarité, retard de M échantillons en entrée = retard de L en sortie,
# longueur ceil(N L / M), gain DC, et rejet du repliement quand on décime
dp.resampler(2, 3)(lambda x: scipy.signal.resample_poly(x, 2, 3))

# Traitement par blocs : tout découpage (blocs vides et d'un échantillon compris) doit donner la même sortie
@dp.streaming()
class MonFiltre:
    def process(self, bloc): ...

# Fonction à état explicite, par exemple lfilter avec zi
dp.stateful(lambda bloc, z: scipy.signal.lfilter(b, a, bloc, zi=z), init_state=np.zeros(2))
```

## En ligne de commande

`dsp-props check` trouve tous les opérateurs déclarés dans un module ou un fichier et les vérifie :

```
$ dsp-props check examples/filters.py --examples 100
FAIL examples/filters.py:buggy_fft  (4 relations, 3.4s)
      FAIL inversibility
           inversibility: L2 error 2.000e+00 exceeds tolerance 6.280e-15 (N=2, ref norm 1.414e+00)
           minimal input: [1, 1]
ok   examples/filters.py:fft  (6 relations, 6.5s)
ok   examples/filters.py:lowpass  (4 relations, 3.1s)
ok   examples/filters.py:resample_2_3  (5 relations, 2.8s)

3/4 operators pass
```

Cibles possibles : `paquet.module`, `fichier.py`, `module:operateur`. Options : `--json`, `--markdown`, `--html`, `--examples N`, `--derandomize` (entrées reproductibles en CI). Code de sortie 1 si une relation échoue, ce qui suffit pour bloquer une CI.

## Code C

`dsp_props.adapters` charge une fonction C (bibliothèque partagée, via ctypes) et la déclare comme n'importe quel opérateur. Convention : `void f(const double *x, size_t n, double *y, double *etat)`.

```python
from dsp_props.adapters import build_shared, c_function, c_block_processor

lib = build_shared("examples/c/biquad.c")
dp.verify(dp.lti_filter(transfer=(b, a))(c_function(lib, "biquad", state_size=2)))
dp.verify(dp.streaming()(c_block_processor(lib, "biquad", state_size=2)))
```

`examples/c/biquad.c` contient un biquad correct et deux variantes boguées. Celle qui oublie une variable d'état entre deux blocs passe tous les tests sur un appel unique et n'est détectée que par l'invariance au découpage en blocs.

## Tolérances calibrées

Une borne fixe en ε · log N ne décrit pas toutes les bibliothèques : sur N = 2…1200, la FFT de PyTorch (MKL) atteint 195 ε contre 4 ε pour NumPy, selon la factorisation de N. `dp.calibrate` mesure l'erreur réelle contre une référence en précision étendue et en déduit la tolérance :

```python
tol = dp.calibrate(torch_fft, lengths=range(1, 513))   # refuse un opérateur faux
print(tol.summary())
dp.transform(inverse=torch_ifft, parseval=True, tolerance=tol)(torch_fft)
```

`python benchmarks/error_profile.py` produit le profil d'erreur complet (`benchmarks/error_profile.csv`), et `python benchmarks/plot_error_profile.py` la figure ci-dessous.

![Erreur relative de la FFT selon N, NumPy contre PyTorch](https://raw.githubusercontent.com/clement-basdevant/dsp-props/main/docs/figures/error_profile.png)

## Valider l'outil : la suite de mutants

`mutants/` contient 31 implémentations volontairement boguées, réparties en six familles :

| Famille | Mutants |
| --- | --- |
| FFT complexe | 1/N oublié, conjugaison manquante, décalage d'un indice, normalisation erronée, calcul en float32, signe des twiddles, dernier échantillon ignoré, offset constant |
| FFT réelle (`rfft`) | un bin de moins, inverse qui ignore N, bin de Nyquist divisé par 2, spectre conjugué, inverse sans symétrie hermitienne |
| DCT-II orthonormée | poids du coefficient DC oublié, inverse du mauvais type, calcul en float32 |
| Filtre IIR (ordre 4, résonant) | récursion en float32, filtfilt déclaré causal, coefficients qui changent en cours de route, état initial non nul, gain faux de 1 % |
| Rééchantillonneur 2/3 | gain d'interpolation oublié, anti-repliement trop faible, longueur arrondie par défaut, phase qui dépend de la parité de N, filtrage en float32, état global qui fuit d'un appel à l'autre |
| Streaming par blocs | état remis à zéro, historique décalé d'un échantillon, bloc vide qui efface l'état, blocs courts non filtrés |

```
python mutants/run_mutants.py
...
Mutation score: 31/31 (100%)
```

Les contre-exemples sont minuscules : pour 27 mutants sur 30 (hors `iir_wrong_gain`, détecté sur la réponse impulsionnelle), le signal réduit par Hypothesis fait au plus 3 échantillons (médiane : 2), et 27 mutants tombent dans les 3 premières entrées générées. Les exceptions sont attendues : 97 échantillons pour un filtre qui change après 64, et 192 pour les relations de gain DC et de repliement, qui exigent des signaux longs. `python mutants/run_mutants.py --json benchmarks/mutant_results.json` enregistre ces mesures.

Chaque rapport donne l'entrée minimale et s'exporte :

```python
report = dp.verify(ma_fft, raise_on_failure=False)
print(report)              # FAIL inversibility ... minimal input: [1, 1]
report.to_json()           # pour la CI ou un tableau de résultats
report.to_markdown()       # pour une PR ou un ticket
```

Angle mort documenté : un filtre faux mais toujours linéaire, invariant et causal (gain multiplié par 1,01) passe toutes les relations si l'on ne déclare pas sa fonction de transfert. Avec `transfer=(b, a)`, il est détecté.

## Chasse aux bugs dans de vraies bibliothèques

`benchmarks/campaign.py` applique les relations à SciPy, NumPy, PyTorch, librosa et torchaudio (46 cibles).
Premier bug signalé : [scipy/scipy#26406](https://github.com/scipy/scipy/issues/26406). Résultats détaillés dans `benchmarks/RESULTS-*.md`.

## Installation

Depuis PyPI ([pypi.org/project/dsp-props](https://pypi.org/project/dsp-props/)) :

```
python -m pip install "dsp-props[scipy]"   # [scipy] pour les filtres IIR et les fonctions de transfert
```

En développement :

```
git clone https://github.com/clement-basdevant/dsp-props
cd dsp-props
python -m pip install -e ".[dev]"
python -m pytest
```

## Organisation

| Dossier | Contenu |
| --- | --- |
| `src/dsp_props/core/` | Modèles de tolérance, comparaison robuste |
| `src/dsp_props/generators/` | Stratégies Hypothesis pour signaux |
| `src/dsp_props/relations/` | Une relation métamorphique = une classe |
| `mutants/` | Implémentations boguées et calcul du score de mutation |
| `tests/` | Tests de l'outil lui-même |
| `docs/` | Schéma directeur et documentation |
| `papers/` | Bibliographie et brouillons d'articles |

## Feuille de route

1. **Fondations** : générateurs, relations de base, tests sur `numpy.fft` *(fait)*
2. **Moteur de tolérance** : modèles d'erreur par classe d'opérateur, calibration contre précision étendue *(fait)*
3. **Relations avancées** : causalité, stabilité, streaming par blocs, multicadence *(fait)*
4. **Suite de mutants** : une quarantaine de mutants, essai sur `scipy.signal` *(31 mutants, campagne sur 46 cibles réelles ; à compléter)*
5. **Shrinking et rapport** : contre-exemples minimaux, rapport HTML *(fait)*
6. **Auto-découverte et adaptateur C** *(fait : `dsp-props check`, `dsp_props.adapters`)*

## Licence

BSD-3-Clause, comme NumPy et SciPy.
