# Tuto : installer et lancer le bot (10 minutes)

Pas besoin de connaître l'informatique : suis les étapes dans l'ordre.

## 1. Installer Python (une seule fois)

1. Va sur **https://www.python.org/downloads/release/python-31410/** et, tout en bas, clique sur **Windows installer (64-bit)**.
   Prends bien **Python 3.14** : la toute dernière version (3.15) n'est pas encore compatible avec le bot.
2. Ouvre le fichier téléchargé.
3. **Important :** en bas de la première fenêtre, coche **« Add python.exe to PATH »**, puis clique sur **Install Now**.

> 💡 Si l'installation du bot échoue plus tard (étape 3), ta version de Python est peut-être trop récente : installe **Python 3.14** avec le lien de l'étape 1, puis relance `INSTALLER.bat`.

## 2. Télécharger le bot

1. En haut de cette page GitHub, clique sur le bouton vert **Code**, puis **Download ZIP**.
2. Fais un clic droit sur le fichier ZIP → **Extraire tout**. Mets le dossier où tu veux (par exemple sur le Bureau).

## 3. Installer le bot (une seule fois)

Dans le dossier du bot, double-clique sur **`INSTALLER.bat`** (pas besoin du mode administrateur). Une fenêtre noire s'ouvre et installe ce qu'il faut (1 à 3 minutes). Attends le message **« Installation terminée »**, puis ferme la fenêtre.

> 🛡️ Si Windows affiche **« Windows a protégé votre ordinateur »**, clique sur **Informations complémentaires**, puis **Exécuter quand même**. C'est normal pour un fichier téléchargé.

C'est fait une fois pour toutes : ensuite, tu n'utilises plus que `0_LANCER.bat`.

## 4. Régler le jeu

- Langue du jeu : **français**
- Résolution : **1920 × 1080** (dans les options graphiques du jeu)

## 5. Lancer le bot

1. Lance le jeu et va dans la ville (l'écran avec le journal des quêtes en haut à droite).
2. **Fais un clic droit** sur **`0_LANCER.bat`** → **Exécuter en tant qu'administrateur**, puis clique sur **Oui**. ⚠️ Obligatoire : le jeu tourne en administrateur, sans ça le bot ne peut pas cliquer.
3. **Première fois seulement :** la fenêtre noire te demande quelle quête suivre. Tape **1** pour la quête principale (l'histoire), puis Entrée.
4. Le bot démarre tout seul au bout de 3 secondes.

## 6. Enregistrer ton équipe (une seule fois, très important)

Le bot doit savoir quels sont **tes 4 meilleurs persos**, pour ne jamais les sortir de l'équipe.

1. Dans le jeu, ouvre un **écran d'équipe** : c'est l'écran avec le bouton **« En avant ! »** en bas, juste avant un combat.
2. Mets tes **4 persos les plus forts** dans les 4 cases du haut.
3. Appuie sur **F11**. La fenêtre noire affiche « Équipe enregistrée ».

## Les touches

| Touche | Ce qu'elle fait |
| --- | --- |
| **F8** | Mettre en pause / relancer |
| **F9** | Arrêter le bot |
| **F11** | Enregistrer ton équipe (sur un écran d'équipe) |
| **F12** | Changer de quête : principale ↔ secondaire |
| **F6** | Prendre une capture d'écran (pour montrer un problème) |

## Quand l'histoire principale est finie

Quand la 1re ligne du journal affiche **« Mise à jour programmée »**, appuie sur **F12** : le bot suit alors la **2e ligne** du journal (la quête secondaire, en bleu).

## Pour laisser tourner la nuit

- Mets la mise en veille du PC sur **Jamais** (Paramètres → Système → Alimentation).
- Tu peux **éteindre l'écran** avec son bouton, ça ne gêne pas le bot.
- Ne verrouille pas la session (pas de Windows + L).
- Le matin, tu peux ouvrir **`rapport.txt`** (à côté de `0_LANCER.bat`) : il résume la nuit (combats, victoires, arrêts). C'est juste pour information.

## Problèmes fréquents

| Problème | Solution |
| --- | --- |
| « Python est introuvable » | Réinstalle Python en cochant bien **« Add python.exe to PATH »**. |
| Le bot ne démarre pas | Lance d'abord **`INSTALLER.bat`**, puis **`0_LANCER.bat`**. |
| Le bot ne clique pas | Relance **`0_LANCER.bat`** avec un clic droit → **Exécuter en tant qu'administrateur**. |
| Le bot clique à côté | Vérifie la résolution du jeu : **1920 × 1080**. |
| Le bot s'arrête | Normal sur une défaite, la cuisine ou plus de potions : regarde la fin de la fenêtre noire, corrige à la main, puis **F8** pour relancer. |
| Le bot déplace tes meilleurs persos | Refais l'étape 6 (**F11** sur un écran d'équipe). |

Le bot automatise **environ 90 à 95 % du mode histoire** : certaines quêtes spéciales (cuisine, mini-jeux) et les combats trop durs demandent un coup de main.
