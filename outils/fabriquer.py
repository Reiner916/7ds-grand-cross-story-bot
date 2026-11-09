# Étape 2 - Fabrique le jeu de données YOLO : vraies captures + écrans synthétiques (copier-coller de vrais boutons)
import json, os, random, shutil, cv2, numpy as np
random.seed(7); np.random.seed(7)
from etiqueter import CLASSES
ICI = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(os.path.join(ICI, 'etiquettes.json')))
D = os.path.join(ICI, 'donnees')
shutil.rmtree(D, ignore_errors=True)
for p in ['images/train', 'images/val', 'labels/train', 'labels/val']: os.makedirs(f'{D}/{p}')

EXCLUS = ['220502', '222507', '222513', '222600', '222634', '222521', '220510']   # étiquettes incomplètes
TEST = ['57527055', '549f54eb', '222929', '8037fec4', '220633', 'da9604b9']  # jamais vus
cle = lambda f: os.path.basename(f)[:8].replace('_', '')[:8]
def est(f, liste): return any(os.path.basename(f).startswith(k) for k in liste)

train = [f for f in E if not est(f, EXCLUS + TEST)]
test = [f for f in E if est(f, TEST)]

def ecrire(nom, img, boites, part):
    H, W = img.shape[:2]
    cv2.imwrite(f'{D}/images/{part}/{nom}.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    with open(f'{D}/labels/{part}/{nom}.txt', 'w') as fh:
        for b in boites:
            fh.write(f"{CLASSES.index(b['c'])} {b['x']/W:.6f} {b['y']/H:.6f} {b['w']/W:.6f} {b['h']/H:.6f}\n")

# vraies captures
for f in train: ecrire('r_' + cle(f), cv2.imread(f), E[f]['boites'], 'train')
for f in test:  ecrire('t_' + cle(f), cv2.imread(f), E[f]['boites'], 'val')

# patchs (bouton + un peu de fond réel), pris uniquement sur les captures d'entraînement
patchs = []
for f in train:
    img = cv2.imread(f); H, W = img.shape[:2]
    for b in E[f]['boites']:
        m = 6
        x1, y1 = int(b['x'] - b['w']/2 - m), int(b['y'] - b['h']/2 - m)
        x2, y2 = int(b['x'] + b['w']/2 + m), int(b['y'] + b['h']/2 + m)
        x1, y1, x2, y2 = max(x1, 0), max(y1, 0), min(x2, W), min(y2, H)
        patchs.append(dict(c=b['c'], img=img[y1:y2, x1:x2].copy(), x=b['x'], y=b['y'], w=b['w'], h=b['h'], m=m))
print('patchs', len(patchs))
# les classes rares sont tirées plus souvent
from collections import Counter
nb = Counter(p['c'] for p in patchs)
poids = np.array([1 / nb[p['c']] for p in patchs]); poids /= poids.sum()

def teinte(p):
    hsv = cv2.cvtColor(p, cv2.COLOR_BGR2HSV).astype(np.int16)
    hsv[:, :, 0] = (hsv[:, :, 0] + random.randint(0, 179)) % 180
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

N = 260
for k in range(N):
    base = random.choice(train)
    img = cv2.imread(base).copy(); H, W = img.shape[:2]
    boites = [dict(b) for b in E[base]['boites']]
    for _ in range(random.randint(1, 3)):
        p = patchs[np.random.choice(len(patchs), p=poids)]
        s = random.uniform(0.7, 1.35) if p['c'] == 'bulle' else random.uniform(0.9, 1.1)
        pi = cv2.resize(p['img'], None, fx=s, fy=s)
        if p['c'] == 'bulle' and random.random() < 0.6: pi = teinte(pi)
        pi = np.clip(pi.astype(np.float32) * random.uniform(0.85, 1.15), 0, 255).astype(np.uint8)
        ph, pw = pi.shape[:2]
        # position proche de l'originale (l'interface du jeu bouge peu), bulle n'importe où dans le monde
        if p['c'] == 'bulle':
            cx, cy = random.uniform(0.15, 0.8) * W, random.uniform(0.2, 0.8) * H
        else:
            cx, cy = p['x'] + random.uniform(-120, 120), p['y'] + random.uniform(-60, 60)
        x1, y1 = int(np.clip(cx - pw/2, 0, W - pw)), int(np.clip(cy - ph/2, 0, H - ph))
        img[y1:y1+ph, x1:x1+pw] = pi
        nx, ny = x1 + pw/2, y1 + ph/2
        # retire les boîtes recouvertes
        boites = [b for b in boites if not (abs(b['x'] - nx) < (b['w'] + pw)/2 and abs(b['y'] - ny) < (b['h'] + ph)/2)]
        boites.append(dict(c=p['c'], x=nx, y=ny, w=p['w']*s, h=p['h']*s))
    ecrire(f's_{k:03d}', img, boites, 'train')

# PASSER : seulement les lettres claires, collées sur des fonds variés au coin haut-droit
pp = [p for p in patchs if p['c'] == 'passer' and p['y'] < 100]
for k in range(80):
    base = random.choice(train); img = cv2.imread(base).copy(); H, W = img.shape[:2]
    boites = [dict(b) for b in E[base]['boites'] if not (b['x'] > 1700 and b['y'] < 100)]
    p = random.choice(pp); pi = p['img']; ph, pw = pi.shape[:2]
    g = cv2.cvtColor(pi, cv2.COLOR_BGR2GRAY)
    m = cv2.dilate((g > 150).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)[:, :, None]
    x1 = int(p['x'] - pw/2 + random.randint(-15, 15)); y1 = int(np.clip(p['y'] - ph/2 + random.randint(-5, 5), 0, H - ph))
    x1 = int(np.clip(x1, 0, W - pw))
    zone = img[y1:y1+ph, x1:x1+pw].astype(np.float32)
    img[y1:y1+ph, x1:x1+pw] = (pi * m + zone * (1 - m)).astype(np.uint8)
    boites.append(dict(c='passer', x=x1 + pw/2, y=y1 + ph/2, w=p['w'], h=p['h']))
    ecrire(f'p_{k:03d}', img, boites, 'train')

open(f'{D}/data.yaml', 'w').write(f"path: {D}\ntrain: images/train\nval: images/val\nnames:\n" +
                                  ''.join(f"  {i}: {c}\n" for i, c in enumerate(CLASSES)))
print('train', len(os.listdir(f'{D}/images/train')), 'val', len(os.listdir(f'{D}/images/val')))
