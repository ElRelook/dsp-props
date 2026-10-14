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

## Valider l'outil : la suite de mutants

`mutants/` contient des FFT volontairement boguées (facteur 1/N oublié, conjugaison manquante, décalage d'un indice, normalisation erronée, calcul en float32, signe des twiddles inversé, dernier échantillon ignoré, offset constant). Le score de mutation mesure ce que l'outil détecte :

```
python mutants/run_mutants.py
...
Mutation score: 8/8 (100%)
```

## Installation (développement)

```
git clone https://github.com/ElRelook/dsp-props
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

1. **Fondations** : générateurs, relations de base, tests sur `numpy.fft` *(en cours)*
2. **Moteur de tolérance** : modèles d'erreur par classe d'opérateur, calibration contre précision étendue
3. **Relations avancées** : causalité, stabilité, streaming par blocs, multicadence
4. **Suite de mutants** : une quarantaine de mutants, essai sur `scipy.signal`
5. **Shrinking et rapport** : contre-exemples minimaux, rapport HTML
6. **Auto-découverte et adaptateur C**

## Licence

BSD-3-Clause, comme NumPy et SciPy.
