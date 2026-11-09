# Étape 3 - Amélioration continue : ajoute au jeu de données les écrans où le bot s'est trompé.
#
# 1. Le bot prend une capture à chaque blocage (_moteur/captures).
# 2. On note dans exemples.json ce qu'il aurait dû voir :
#      {"153012_rien.png": [["bulle", 973, 363, 56, 60]],      <- classe, centre x, centre y, largeur, hauteur (pixels)
#       "160457_manuel.png": []}                              <- [] = contre-exemple : rien à cliquer ici
# 3. Ce script ajoute ces captures + des variantes fabriquées (l'objet collé ailleurs, à une autre taille,
#    une autre luminosité). Ensuite ENTRAINER.bat réentraîne le détecteur sur la carte graphique, et le
#    nouveau n'est installé que s'il fait au moins aussi bien que l'ancien sur les vraies captures (garde-fou).
import cv2, json, numpy as np, os, random, sys
ICI = os.path.dirname(os.path.abspath(__file__))
MOTEUR = os.path.join(ICI, "..", "_moteur")
sys.path.insert(0, MOTEUR)
from detecteur import CLASSES, detecter
CAPTURES, DS = os.path.join(MOTEUR, "captures"), os.path.join(MOTEUR, "donnees")
VARIANTES = 60
random.seed(0)

def ecrire(nom, img, boites):
    H, W = img.shape[:2]
    os.makedirs(os.path.join(DS, "images", "train"), exist_ok=True); os.makedirs(os.path.join(DS, "labels", "train"), exist_ok=True)
    cv2.imwrite(os.path.join(DS, "images", "train", nom + ".jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    with open(os.path.join(DS, "labels", "train", nom + ".txt"), "w") as f:
        for c, x, y, w, h in boites:
            f.write(f"{CLASSES.index(c)} {x/W:.6f} {y/H:.6f} {max(w, 28)/W:.6f} {max(h, 28)/H:.6f}\n")

def reperes(img):
    """Les repères toujours présents (barre de menu, journal) sont étiquetés par le détecteur actuel."""
    d = detecter(img)
    return [(c, *d[c][0][:2], *((300, 50) if c == "hud" else (120, 40))) for c in ("hud", "journal") if c in d]

exemples = json.load(open(os.path.join(ICI, "exemples.json"), encoding="utf-8"))
from datetime import datetime
lot = datetime.now().strftime("e%m%d%H%M")
patchs, fonds = [], []
for k, (fichier, boites) in enumerate(exemples.items()):
    img = cv2.imread(os.path.join(CAPTURES, fichier)); boites = [tuple(b) for b in boites]
    ecrire(f"{lot}_{k:03d}", img, boites + reperes(img)); fonds.append(img)
    for c, x, y, w, h in boites:
        patchs.append((c, img[int(y-h/2-6):int(y+h/2+6), int(x-w/2-6):int(x+w/2+6)].copy(), w, h, x, y))
for n in range(VARIANTES if patchs else 0):
    fond = random.choice(fonds).copy(); H, W = fond.shape[:2]
    c, p, w, h, x0, y0 = random.choice(patchs)
    s = random.uniform(0.7, 1.4) if c == "bulle" else random.uniform(0.95, 1.05)
    p = np.clip(cv2.resize(p, None, fx=s, fy=s).astype(np.float32) * random.uniform(0.85, 1.15), 0, 255).astype(np.uint8)
    ph, pw = p.shape[:2]
    cx, cy = (random.uniform(.15, .8) * W, random.uniform(.15, .8) * H) if c == "bulle" else (x0 + random.uniform(-20, 20), y0 + random.uniform(-8, 8))
    x1, y1 = int(np.clip(cx - pw/2, 0, W - pw)), int(np.clip(cy - ph/2, 0, H - ph)); fond[y1:y1+ph, x1:x1+pw] = p
    ecrire(f"{lot}_s{n:03d}", fond, [(c, x1 + pw/2, y1 + ph/2, w*s, h*s)] + reperes(fond))
print(f"{len(exemples)} captures + {VARIANTES if patchs else 0} variantes ajoutées. Lance ENTRAINER.bat pour réentraîner.")
