# Bot mode histoire · 7DS Grand Cross

Bot qui joue **tout seul au mode histoire** de *The Seven Deadly Sins: Grand Cross* (client PC officiel de Netmarble) : il suit la quête, parle aux personnages, passe les dialogues, compose l'équipe, lance les combats et ramasse les récompenses. On le lance le soir, on éteint l'écran, et l'histoire avance pendant la nuit.

Il **voit l'écran comme un joueur** : un détecteur d'objets (YOLO) entraîné sur plus de 1 400 images du jeu repère les boutons, les bulles de quête et les menus, puis le bot décide quoi faire et clique. Il ne lit ni ne modifie rien dans le jeu.

Projet personnel d'**Amir Chouchane**, étudiant en BTS SIO.

![Ce que voit le bot, étape par étape](docs/demo.gif)

## Résultats

| | |
| --- | --- |
| Plus longue session sans intervention | **8 h 53** (117 victoires, 64 récompenses de quête) |
| Fiabilité du détecteur sur de vraies captures | **0,99** (mAP50, 180 captures de contrôle) |
| Part du mode histoire automatisée | **environ 90 à 95 %** (voir [Limites](#limites)) |
| Analyse d'un écran | environ 0,2 s sur un processeur ordinaire |

## Ce que fait le bot

**Dans le jeu**
- Relance la quête suivie depuis le journal (quête principale ou quête secondaire, au choix)
- Repère les bulles de quête au-dessus des personnages, quelle que soit leur forme ou leur couleur (« ? », « ! », loupe, épées, bulles lumineuses) et ignore les bulles de discussion inutiles
- Passe les dialogues et les cinématiques (SKIP, PASSER), y compris pendant les attaques spéciales
- Écran d'équipe : *Choix auto*, puis **range les héros imposés par la quête en remplaçant** pour garder ses meilleurs personnages au combat ; emprunte le héros manquant si besoin
- Utilise une potion d'endurance quand il n'y en a plus, valide les victoires, ferme les récompenses, gère les changements de chapitre et les nouvelles aventures

**Sécurités**
- **Reprise automatique** quand rien ne bouge (clics de dégagement, relance de la quête) avant de s'arrêter
- **Anti-boucle** : un bouton cliqué sans effet ou une fausse bulle sont repérés puis ignorés
- S'arrête proprement sur une défaite, l'écran de cuisine ou des potions épuisées, avec une capture d'écran pour comprendre
- **Rapport de session** (`rapport.txt`) : durée, combats, victoires, potions utilisées, arrêts et leur cause

## Installer et lancer

Le tutoriel pas à pas est ici : **[TUTO.md](TUTO.md)**. En résumé :

1. Installer [Python](https://www.python.org/downloads/) en cochant **« Add python.exe to PATH »**
2. Télécharger ce dépôt (**Code → Download ZIP**) et le décompresser
3. Double-cliquer sur **`INSTALLER.bat`** (une seule fois)
4. Lancer le jeu en **1920 × 1080, en français**, puis double-cliquer sur **`0_LANCER.bat`** : le bot démarre tout seul

Au premier lancement, le bot demande quelle quête suivre. Il faut aussi, **une seule fois**, ouvrir un écran d'équipe dans le jeu avec ses 4 meilleurs personnages et appuyer sur **F11** : le bot ne les déplacera jamais.

| Touche | Action |
| --- | --- |
| F8 | Pause / reprise |
| F9 | Quitter (écrit le rapport) |
| F11 | Enregistrer son équipe (sur un écran d'équipe) |
| F12 | Passer de la quête principale à la quête secondaire et inversement |
| F6 | Capture d'écran manuelle |
| F7 | Changer l'endroit du « clic dans le vide » |
| F10 | Diagnostic : ce que le bot reconnaît à l'écran |

## Comment ça marche

![Schéma de fonctionnement](docs/fonctionnement.png)

- **Détecteur YOLO11n** (Ultralytics) entraîné sur 15 types d'éléments, exporté au format **ONNX** pour tourner sans carte graphique. Le jeu de données mélange de vraies captures et des **images fabriquées** (un bouton ou une bulle collé ailleurs, à une autre taille, une autre teinte) pour couvrir les cas rares.
- **Comparaison d'image exacte** (OpenCV) pour les écrans qui ne changent jamais : victoire, défaite, récompenses, bouton SKIP, combat en cours, bandeau « Héros requis » et portraits de l'équipe. C'est plus fiable que le détecteur dans ces cas précis.
- **Logique de décision** : ordre de priorité des actions, temps d'attente adaptés (laisser le personnage marcher, attendre la fin d'une animation), détection des boucles et reprises.
- **Pilotage de Windows** par l'API Win32 (fenêtre du jeu, clics, glisser-déposer, raccourcis clavier lus en continu).
- **Amélioration continue** : à chaque blocage, le bot garde une capture. Ces captures sont étiquetées, enrichies de variantes, puis le détecteur est réentraîné sur la carte graphique. **Un garde-fou** compare le nouveau détecteur à l'ancien sur les vraies captures et ne l'installe que s'il fait au moins aussi bien. Les scripts sont dans [`outils/`](outils/).

## Limites

- **Environ 90 à 95 % du mode histoire**, pas 100 % : la cuisine (choix des ingrédients), certaines quêtes à mécanique spéciale et les combats trop difficiles demandent d'intervenir à la main. Le bot s'arrête alors et garde une capture.
- Testé uniquement sur le **client PC officiel, en français, en 1920 × 1080**, sous Windows 10/11.
- Le PC ne doit pas se mettre en veille ni se verrouiller (éteindre l'écran avec son bouton ne pose pas de problème).

## Avertissement

Ce projet est un exercice personnel de vision par ordinateur et d'automatisation. **L'utilisation d'un bot est contraire aux conditions d'utilisation du jeu** et peut entraîner une sanction du compte : chacun l'utilise sous sa propre responsabilité. Le projet n'est ni affilié à Netmarble ni approuvé par l'éditeur.

## Technologies

| | |
| --- | --- |
| Langage | Python 3 |
| Vision | YOLO11n (Ultralytics), ONNX Runtime, OpenCV, NumPy |
| Capture et contrôle | mss, API Win32 (ctypes) |
| Entraînement | PyTorch (CUDA), images fabriquées, garde-fou de validation |

## Organisation

```
0_LANCER.bat        Lance le bot (le seul fichier à ouvrir au quotidien)
INSTALLER.bat       Installe les modules Python (une seule fois)
TUTO.md             Installation pas à pas
_moteur/
├── bot_7ds.py      Logique du bot : décisions, sécurités, équipe, rapport
├── detecteur.py    Détecteur YOLO (ONNX) : renvoie les éléments vus à l'écran
├── detecteur_7ds.onnx   Détecteur entraîné
├── modele.pt       Même détecteur, au format d'entraînement
└── img/            Modèles d'image exacts (victoire, SKIP, défaite...)
outils/             Étiquetage, fabrication du jeu de données, réentraînement
docs/               Démo et schéma
```

## Contact

- LinkedIn : [amir-chouchane](https://www.linkedin.com/in/amir-chouchane)
- GitHub : [@Reiner916](https://github.com/Reiner916)
