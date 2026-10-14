# Schéma directeur

Le schéma directeur complet (état de l'art, catalogue de propriétés, feuille de route, pistes de publication) est maintenu dans le document de projet : https://claude.ai/code/artifact/a8c9b15e-7a21-480b-9455-3732a46f1e03

## Résumé

- **Objectif** : une couche DSP au-dessus d'Hypothesis : relations métamorphiques, générateurs de signaux, tolérances par opérateur.
- **Périmètre v1** : NumPy/SciPy, LTI, transformées, filtrage par blocs, multicadence.
- **Critère de réussite** : score de mutation, temps de détection, taille du contre-exemple minimal.
- **Publications visées** : JOSS (logiciel), SciPy/EuroSciPy (talk), ICST ou atelier MET (catalogue + évaluation par mutation), GRETSI/EUSIPCO (moteur de tolérance).

## Phase 1 : état

- [x] Squelette du paquet, licence, CI
- [x] Générateurs : impulsion, DC, sinusoïde hors grille, quasi-Nyquist, tons proches, parcimonieux, bruit blanc ; longueurs pathologiques
- [x] Relations : linéarité, décalage circulaire, Parseval, symétrie hermitienne, inversibilité, théorème de convolution
- [x] `numpy.fft` passe toutes les relations ; 8 mutants sur 8 détectés
- [x] Premier bug réel signalé en amont : [scipy/scipy#26406](https://github.com/scipy/scipy/issues/26406) (`lfilter`/`sosfilt` sur bloc vide)
- [x] Transformées réelles (`kind="rdft"`), transformées génériques (DCT, STFT) et streaming par blocs (`dp.streaming`, `dp.stateful`)
- [x] 20 mutants en quatre familles, tous détectés

## Observations à suivre en phase 2

- La tolérance FFT (c · ε · log2 N · ‖y‖, c = 20) a rejeté le calcul de référence du théorème du décalage tant que l'argument des twiddles n'était pas réduit modulo N : la référence elle-même doit être plus précise que l'opérateur testé.
- Une DFT naïve en O(N²) dépasse la borne FFT : le modèle de tolérance doit dépendre de l'algorithme, pas seulement de l'opération.
- Les amplitudes extrêmes (1e±100) imposent des normes calculées sans débordement.
- La première CI a trouvé un cas réel : une entrée quasi dénormalisée (‖x‖ ≈ 3e-303) faisait produire NaN au calcul de norme complexe (division complexe par un sous-normal). Les dénormaux doivent devenir un générateur à part entière.
