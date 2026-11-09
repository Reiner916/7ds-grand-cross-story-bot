# Outils : entraîner et améliorer le détecteur

Le bot fonctionne **sans ces outils** : le détecteur entraîné est déjà fourni dans `_moteur/`. Ils servent à comprendre comment il a été construit, ou à l'améliorer.

| Étape | Script | Rôle |
| --- | --- | --- |
| 1 | `etiqueter.py` | Étiquette automatiquement des captures du jeu : chaque image de référence de la première version du bot (`modeles_ahk/`, validées une à une) est cherchée dans sa zone de l'écran, chaque correspondance devient une boîte d'entraînement. |
| 2 | `fabriquer.py` | Construit le jeu de données YOLO : vraies captures + écrans fabriqués (un bouton ou une bulle collé sur un autre fond, à une autre taille, une autre teinte) pour que les éléments rares soient assez représentés. Met de côté des captures jamais vues pour le contrôle. |
| 3 | `ajouter_exemples.py` | Boucle d'amélioration : ajoute les captures où le bot s'est trompé (décrites dans `exemples.json`), avec des variantes, et des contre-exemples (« ici, il n'y a rien à cliquer »). |
| 4 | `entrainer_gpu.py` / `ENTRAINER.bat` | Réentraîne le détecteur (YOLO11n, 10 passes, carte graphique NVIDIA conseillée), l'exporte en ONNX et ne l'installe que si le **garde-fou** valide : il doit faire au moins aussi bien que l'ancien sur toutes les vraies captures. |

Les images d'entraînement (environ 1 400 captures du jeu) ne sont pas publiées.

## Chiffres de l'entraînement

- Base : YOLO11n pré-entraîné, images en 960 px, 15 classes (boutons, bulles de quête, menus, combat…)
- Premier entraînement sur processeur : 25 passes, environ 2 h. Réentraînements sur RTX 3060 : 10 passes, quelques minutes.
- Contrôle sur 180 vraies captures : mAP50 = 0,991, mAP50-95 = 0,912.
