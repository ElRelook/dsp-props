# Tickets à poster

Brouillons prêts, à poster depuis le compte GitHub du projet. Une fois posté, remplacer « à poster » par le lien.

| # | Où | Statut |
| --- | --- | --- |
| 0 | scipy/scipy : lfilter/sosfilt sur bloc vide | posté : [scipy#26406](https://github.com/scipy/scipy/issues/26406) |
| 1 | pytorch/audio : deemphasis écrête à [-1, 1] | à poster |
| 2 | scipy/scipy : tf2sos supprime les retards purs | à poster |
| 3 | commentaire sur scipy#26406 : impact librosa | à poster |

---

## 1. pytorch/audio

Lien : https://github.com/pytorch/audio/issues/new (modèle Bug report)

**Titre :** deemphasis silently clamps output to [-1, 1], so it is not the inverse of preemphasis

### 🐛 Describe the bug

`torchaudio.functional.deemphasis` is documented as the "Inverse of `preemphasis`", but it calls `lfilter` with the default `clamp=True`, so its output is silently clamped to [-1, 1]. As a result `deemphasis(preemphasis(x))` does not return `x` as soon as `|x| > 1`, and the clamping is not mentioned in the documentation.

```python
import torch
import torchaudio.functional as F

x = torch.tensor([1000.0, 500.0], dtype=torch.float64)
print(F.deemphasis(F.preemphasis(x, 0.0), 0.0))
# tensor([1., 1.], dtype=torch.float64)   expected: tensor([1000., 500.])

x = torch.tensor([0.9, 0.9, 0.9], dtype=torch.float64)
print(F.deemphasis(x, 0.97))
# tensor([0.9000, 1.0000, 1.0000]): values above 1 are clamped although the input is a valid waveform
```

Suggested fix: pass `clamp=False` to `lfilter` in `deemphasis` (or expose a `clamp` argument and document it).

### Versions

torchaudio 2.11.0, PyTorch 2.14.1, Python 3.13, Linux x86_64 (CPU).

Found with dsp-props (https://github.com/clement-basdevant/dsp-props), a property-based testing layer for DSP code, through the relation `deemphasis(preemphasis(x)) == x`.

---

## 2. scipy/scipy

Lien : https://github.com/scipy/scipy/issues/new/choose (Bug report)

**Titre :** BUG: signal.tf2sos/zpk2sos drop pure delays (more poles than zeros), so sosfilt(tf2sos(b, a)) != lfilter(b, a)

### Describe your issue.

For a digital filter with more poles than zeros, e.g. a pure delay `y[n] = x[n-2]`, `tf2sos` returns a section that is the identity, so `sosfilt(tf2sos(b, a), x)` differs from `lfilter(b, a, x)` by a time shift.

The `zpk2sos` docs say it will "add poles or zeros to the origin as necessary to obtain the same number of poles and zeros". Adding only zeros at the origin multiplies H(z) by z^k: the magnitude response is preserved but the delay is lost. Is this intended? If so, it might deserve a warning in the docs of `tf2sos`/`zpk2sos`, since round-tripping `lfilter` -> `sosfilt` is a common migration path.

### Reproducing Code Example

```python
import numpy as np
import scipy.signal as ss

b, a = [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]   # y[n] = x[n-2]
print(ss.tf2sos(b, a))                     # [[1. 0. 0. 1. 0. 0.]]  (identity)

x = np.arange(5.0)
print(ss.lfilter(b, a, x))                 # [0. 0. 0. 1. 2.]
print(ss.sosfilt(ss.tf2sos(b, a), x))      # [0. 1. 2. 3. 4.]
```

The same happens for `b = [0, 1], a = [1, 0, 0]` and for IIR filters with leading zeros in `b`, e.g. `b = [0, 1, 0.5], a = [1, -0.5]`.

### Error message

```shell
No error: the result is silently shifted.
```

### SciPy/NumPy/Python version and system information

```shell
1.18.1 2.5.3 sys.version_info(major=3, minor=13, micro=16, releaselevel='final', serial=0)
Linux x86_64, scipy-openblas 0.3.31.dev
```

Found with dsp-props (https://github.com/clement-basdevant/dsp-props) through the relation `sosfilt(tf2sos(b, a), x) == lfilter(b, a, x)`.

---

## 3. Commentaire sur scipy#26406

Lien : https://github.com/scipy/scipy/issues/26406

Additional impact downstream: `librosa.effects.preemphasis` (librosa 1.0.0) uses `scipy.signal.lfilter` and inherits the FIR case, so streaming pre-emphasis fails on an empty block:

```python
import numpy as np, librosa
librosa.effects.preemphasis(np.array([]), coef=0.5, zi=np.zeros(1), return_zf=True)
# ValueError: v cannot be empty   (from scipy/signal/_signaltools.py, lfilter FIR path)
```
