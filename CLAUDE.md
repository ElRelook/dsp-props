# dsp-props

Couche de property-based testing pour le traitement du signal, construite sur Hypothesis.
Au lieu de comparer à une sortie de référence, on vérifie des relations métamorphiques qui
doivent tenir pour toute implémentation correcte, avec une tolérance dérivée d'un modèle
d'erreur, et on rapporte le plus petit contre-exemple.

Auteurs : Clément Basdevant, Nicolas Boganski. Papier JOSS en préparation (`paper/paper.md`, `paper/paper.bib`).
Version 0.1.0 publiée sur PyPI (procédure : `RELEASING.md`). Plan de développement :
`docs/schema-directeur.md`. Tickets de bugs à poster en amont : `papers/tickets-a-poster.md`.

## Les trois briques

1. **Catalogue de relations** : linéarité, théorèmes de décalage et de convolution, Parseval,
   symétrie hermitienne (DFT réelle : N//2+1 bins, DC et Nyquist réels), inversibilité,
   invariance temporelle, causalité, cohérence avec une fonction de transfert déclarée,
   invariance temporelle périodique d'un rééchantillonneur L/M, invariance au découpage en
   blocs d'un processeur en streaming (blocs vides et d'un échantillon compris).
2. **Générateurs de signaux** (stratégies Hypothesis) : impulsions, constantes, sinusoïdes
   hors grille et quasi-Nyquist, paires de tons proches, signaux parcimonieux, bruit blanc ;
   longueurs pathologiques (1, 2, premiers, 2^k ± 1) ; amplitudes de 1e-100 à 1e100 ;
   découpages en blocs avec blocs vides et d'un échantillon.
3. **Moteur de tolérance** : FFT en O(ε log N) (Schatzman 1996) ; filtres récursifs avec une
   borne d'erreur directe qui croît avec l'ordre et les normes ℓ1 des réponses
   impulsionnelles (Higham 2002) ; `dp.calibrate` mesure une implémentation contre une
   référence `longdouble`, longueur par longueur.

## API

```python
import dsp_props as dp

@dp.transform(inverse=np.fft.ifft, parseval=True, real_input_hermitian=True)
def my_fft(x): return np.fft.fft(x)

dp.verify(my_fft)   # lève PropertyViolation avec un contre-exemple minimal
```

Déclarations disponibles : transformées (complexe, entrée réelle, linéaire générique comme
la DCT), filtres LTI (fonction de transfert et borne de gain optionnelles), rééchantillonneurs
rationnels, processeurs en streaming ou à état. Adaptateurs NumPy, SciPy, PyTorch, et C via
ctypes.

## Commandes

```bash
python -m pip install -e ".[dev]"      # installation de développement
python -m pytest -q                    # suite de tests interne (83 tests, ~3 min)
dsp-props check module_or_file.py      # découvre les opérateurs déclarés, code de sortie ≠ 0 si échec
python mutants/run_mutants.py          # suite de mutation (31 mutants, 6 familles)
python benchmarks/campaign.py          # campagne sur 46 cibles réelles
python benchmarks/error_profile.py     # profil d'erreur FFT, N = 2..1200
```

La CI (`.github/workflows/ci.yml`) lance pytest, la suite de mutation, la CLI sur
`examples/filters.py` et la construction du paquet, sous Python 3.10, 3.12 et 3.13.

## Règles du projet

- **Ne jamais élargir une tolérance pour faire passer un test.** Si une relation échoue,
  c'est soit un bug de l'opérateur, soit un modèle d'erreur faux à corriger en le justifiant.
  `dp.calibrate` refuse volontairement les erreurs implausibles plutôt que de les absorber.
- **Chaque chiffre du papier vient d'un script du dépôt** (les trois ci-dessus). Après toute
  modification des relations, des générateurs ou des tolérances, relancer les scripts et
  mettre à jour le papier si les chiffres changent.
- Un contre-exemple n'est utile que s'il est petit : surveiller la qualité du shrinking
  (actuellement médiane de 2 échantillons).
- L'API déclarative doit rester légère : un décorateur par opérateur.

## État actuel (octobre 2026)

- Mutants : 31/31 détectés avec 200 entrées par relation ; 27 échouent dans les 3 premières
  entrées. Angle mort connu : un filtre faux mais toujours LTI et causal, détecté dès qu'on
  déclare sa fonction de transfert.
- Bugs trouvés : `scipy.signal.lfilter` / `sosfilt` avec un bloc vide et un état initial
  (scipy/scipy#26406). La partie `lfilter` redécouvre scipy/scipy#22571 (déjà connu, corrigé
  dans la version de dev) ; la partie `sosfilt` est nouvelle. Le cas FIR de `lfilter` se
  propage à la pré-emphase en streaming de librosa. SciPy applique une politique IA : tickets
  et PR rédigés par l'auteur, pas par une IA. Comportements
  documentés mais surprenants : `tf2sos` supprime les retards purs ; `deemphasis` de
  torchaudio écrête dans [-1, 1].
- FFT CPU de PyTorch : jusqu'à 195 ε pour certaines longueurs à grands facteurs premiers
  (N = 596), contre environ 4 ε pour NumPy/SciPy.

## Pistes ouvertes (fiche de projet)

- CLI qui devine la catégorie d'une fonction non déclarée (signature, nom, docstring).
- Relations de multicadence avancées (identités nobles), stabilité BIBO, cohérence
  float32/float64, dénormaux.
- Génération automatique de tests de non-régression à partir des contre-exemples.
- Code C embarqué en virgule fixe.
- Propriétés d'estimateurs : biais, variance contre la borne de Cramér-Rao.
