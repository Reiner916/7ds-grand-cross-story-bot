# Tuto : installer et lancer le bot (10 minutes)

Pas besoin de connaître l'informatique : suis les étapes dans l'ordre.

## 1. Installer Python (une seule fois)

1. Va sur **https://www.python.org/downloads/** et clique sur le gros bouton jaune **Download Python**.
2. Ouvre le fichier téléchargé.
3. **Important :** en bas de la première fenêtre, coche **« Add python.exe to PATH »**, puis clique sur **Install Now**.

## 2. Télécharger le bot

1. En haut de cette page GitHub, clique sur le bouton vert **Code**, puis **Download ZIP**.
2. Fais un clic droit sur le fichier ZIP → **Extraire tout**. Mets le dossier où tu veux (par exemple sur le Bureau).

## 3. Installer le bot (une seule fois)

Dans le dossier du bot, double-clique sur **`INSTALLER.bat`**. Une fenêtre noire s'ouvre et installe ce qu'il faut (1 à 3 minutes). Attends le message **« Installation terminée »**, puis ferme la fenêtre.

## 4. Régler le jeu

- Langue du jeu : **français**
- Résolution : **1920 × 1080** (dans les options graphiques du jeu)

## 5. Lancer le bot

1. Lance le jeu et va dans la ville (l'écran avec le journal des quêtes en haut à droite).
2. Double-clique sur **`0_LANCER.bat`** et clique sur **Oui** quand Windows demande l'autorisation.
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
- Le matin, ouvre **`rapport.txt`** : il résume la nuit (combats, victoires, arrêts).

## Problèmes fréquents

| Problème | Solution |
| --- | --- |
| « Python est introuvable » | Réinstalle Python en cochant bien **« Add python.exe to PATH »**. |
| Le bot ne démarre pas | Lance d'abord **`INSTALLER.bat`**, puis **`0_LANCER.bat`**. |
| Le bot ne clique pas | Accepte la demande d'autorisation (le jeu tourne en administrateur, le bot aussi). |
| Le bot clique à côté | Vérifie la résolution du jeu : **1920 × 1080**. |
| Le bot s'arrête | Normal sur une défaite, la cuisine ou plus de potions : regarde la fin de la fenêtre noire, corrige à la main, puis **F8** pour relancer. |
| Le bot déplace tes meilleurs persos | Refais l'étape 6 (**F11** sur un écran d'équipe). |

Le bot automatise **environ 90 à 95 % du mode histoire** : certaines quêtes spéciales (cuisine, mini-jeux) et les combats trop durs demandent un coup de main.
