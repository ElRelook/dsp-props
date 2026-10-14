# Campagne 2 du 14 octobre 2026 : librosa, torchaudio, scipy.signal

Environnement : SciPy 1.18.1, librosa 1.0.0 (python-soxr 1.1.0), torchaudio 2.11.0, PyTorch 2.14.1, NumPy 2.5.3.
Commande : `python benchmarks/campaign.py --examples 200` : 46 cibles, 40 passent.

## Nouvelles pistes

### A. scipy.signal.tf2sos supprime les retards purs (incohérence probable)

`sosfilt(tf2sos(b, a), x)` diffère de `lfilter(b, a, x)` dès que le filtre a plus de pôles que de zéros
(par exemple un retard pur). `zpk2sos` complète avec des zéros à l'origine, ce qui revient à multiplier
H(z) par z^k : le gain est conservé, mais le retard disparaît. La documentation de `zpk2sos` indique bien
qu'elle « ajoute des pôles ou des zéros à l'origine si nécessaire », sans signaler que la réponse
temporelle change.

```python
import numpy as np, scipy.signal as ss
b, a = [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]      # y[n] = x[n-2]
print(ss.tf2sos(b, a))                        # [[1. 0. 0. 1. 0. 0.]]  -> identité
x = np.arange(5.0)
print(ss.lfilter(b, a, x))                    # [0. 0. 0. 1. 2.]
print(ss.sosfilt(ss.tf2sos(b, a), x))         # [0. 1. 2. 3. 4.]
```

Contre-exemple minimal Hypothesis : `b = [0, 1]`, `a = [1, 0, 0]`, x = 32 échantillons à 1.
À discuter avec les mainteneurs avant de le qualifier de bug : comportement documenté mais surprenant.

### B. torchaudio.functional.deemphasis écrête silencieusement la sortie à [-1, 1]

`deemphasis` appelle `lfilter` avec `clamp=True` par défaut, ce que la documentation ne mentionne pas.
`deemphasis(preemphasis(x))` ne rend donc pas `x` dès que l'amplitude dépasse 1, alors que la
documentation la présente comme « l'inverse de preemphasis ».

```python
import torch, torchaudio.functional as F
x = torch.tensor([1000.0, 500.0], dtype=torch.float64)
F.deemphasis(F.preemphasis(x, 0.0), 0.0)     # tensor([1., 1.]) au lieu de [1000., 500.]
```

### C. librosa.effects.preemphasis plante sur un bloc vide (conséquence de scipy#26406)

`preemphasis(np.array([]), zi=..., return_zf=True)` lève `ValueError: v cannot be empty`, venant du chemin FIR
de `scipy.signal.lfilter`. Le bug signalé dans [scipy/scipy#26406](https://github.com/scipy/scipy/issues/26406)
touche donc aussi le traitement en streaming de librosa.

## Déjà connu

`lfilter` et `sosfilt` sur bloc vide : retrouvés par trois cibles, dont la nouvelle relation de bibliothèque
`dp.stateful` (signalé dans scipy#26406).

## Écartés au triage (erreurs de spécification de nos tests, pas des bugs)

- `filtfilt` avec le remplissage par défaut n'est pas symétrique par renversement temporel : c'est voulu.
  Avec `method="gust"`, la symétrie tient (vérifiée).
- `stft` réduit `nperseg` à `len(x)` avec un avertissement ; `istft` ne peut pas le deviner.
- Le rééchantillonneur soxr « HQ » de librosa travaille à environ 20 bits de précision par conception.
  Observation annexe : il renvoie NaN pour des amplitudes supérieures à ~3.4e38 (limite float32) en entrée float64.

## Ce qui passe

STFT/ISTFT de librosa et de torchaudio (Spectrogram/InverseSpectrogram), `torchaudio.functional.lfilter`
comparé à SciPy, `fftconvolve` de torchaudio, rééchantillonnage identité (librosa, torchaudio, scipy),
aller-retour `resample` ×2 de SciPy, `hilbert`, Parseval de `periodogram`, `filtfilt(method="gust")`,
loi μ de librosa, ainsi que les 23 cibles de la première campagne.
