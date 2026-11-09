# Étape 1 - Étiquetage automatique des captures : chaque image de référence (déjà validée sur les captures)
# est cherchée dans sa zone, avec sa tolérance. Chaque détection devient une boîte YOLO.
import cv2, numpy as np, os, json
ICI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ICI, 'modeles_ahk') + os.sep          # images de référence de la 1re version (AutoHotkey)

CLASSES = ['passer', 'skip', 'ok', 'ok_victoire', 'en_avant', 'choix_auto', 'terminer',
           'demarrer', 'aller', 'principal', 'journal', 'bulle', 'combat', 'cuisine', 'hud']

# zones en fractions [x1,y1,x2,y2]
Z = dict(TOUT=(0,0,1,1), HD=(.6,0,1,.25), COIN=(.9,0,1,.15), VICT=(.3,.75,.7,1), BAS=(.3,.85,.7,1),
         CENTRE=(.25,.3,.75,.9), QUETE=(.25,.3,.75,1), MENU=(.55,.9,.7,1), MONDE=(.1,.1,.85,.85),
         COMBAT=(.85,0,1,.08))
# (classe, fichier, zone, tolérance)
REFS = [
    ('passer','passer_dialogue','COIN',45), ('passer','passer_cine','COIN',40), ('passer','passer_blanc','COIN',40),
    ('passer','ult','BAS',25), ('skip','skip','COIN',45),
    ('ok','ok','CENTRE',60), ('ok','ok_2','CENTRE',60), ('ok','ok_3','CENTRE',50), ('ok_victoire','ok_victoire','VICT',60),
    ('en_avant','en_avant','TOUT',65), ('choix_auto','choix_auto','TOUT',50), ('choix_auto','choix_auto_2','TOUT',50),
    ('terminer','terminer','QUETE',65), ('demarrer','demarrer','QUETE',65), ('aller','aller','QUETE',65),
    ('principal','principal','QUETE',40), ('journal','journal','HD',55),
    ('bulle','bulle','MONDE',60), ('bulle','bulle_petite','MONDE',60), ('bulle','bulle_mini','MONDE',60), ('bulle','bulle_grande','MONDE',60),
    ('combat','combat','COMBAT',45), ('cuisine','cuisine','TOUT',50), ('hud','hud','MENU',30),
]

def load(n):
    t = cv2.imread(IMG + n + '.png').astype(np.int16)
    return t, ~np.all(t == [255, 0, 255], axis=2)
TPL = {f: load(f) for _, f, _, _ in REFS}

def trouve(S, t, m, reg, tol, k=60):
    """Toutes les positions où l'écart max (comme ImageSearch) <= tol. Pré-tri rapide par SQDIFF masqué."""
    x0, y0, x1, y1 = reg
    sub = S[y0:y1, x0:x1]
    h, w = t.shape[:2]
    if sub.shape[0] < h or sub.shape[1] < w: return []
    mask = np.repeat(m[:, :, None], 3, 2).astype(np.float32)
    r = cv2.matchTemplate(sub.astype(np.float32), t.astype(np.float32), cv2.TM_SQDIFF, mask=mask)
    r = np.nan_to_num(r, nan=1e18, posinf=1e18)
    out = []
    for i in np.argsort(r, axis=None)[:k]:
        y, x = np.unravel_index(i, r.shape)
        d = np.abs(sub[y:y+h, x:x+w] - t).max(2)[m].max()
        if d <= tol:
            out.append((x + x0, y + y0, w, h, int(d)))
    # supprime les doublons qui se chevauchent
    res = []
    for b in sorted(out, key=lambda b: b[4]):
        if all(abs(b[0]-c[0]) > b[2]//2 or abs(b[1]-c[1]) > b[3]//2 for c in res):
            res.append(b)
    return res

def etiqueter(chemin):
    S = cv2.imread(chemin).astype(np.int16)
    H, W = S.shape[:2]
    boites = []
    for cl, f, z, tol in REFS:
        zz = Z[z]
        reg = (int(zz[0]*W), int(zz[1]*H), int(zz[2]*W), int(zz[3]*H))
        for (x, y, w, h, d) in trouve(S, *TPL[f], reg, tol):
            # petites cibles : on agrandit un peu la boîte (min 28 px) pour que YOLO les voie
            cx, cy = x + w/2, y + h/2
            w2, h2 = max(w + 8, 28), max(h + 8, 28)
            boites.append(dict(c=cl, x=cx, y=cy, w=w2, h=h2, d=d, ref=f))
    # une même cible trouvée par plusieurs variantes -> on garde la meilleure
    fin = []
    for b in sorted(boites, key=lambda b: b['d']):
        if all(not (b['c'] == c['c'] and abs(b['x']-c['x']) < 20 and abs(b['y']-c['y']) < 20) for c in fin):
            fin.append(b)
    return W, H, fin

if __name__ == '__main__':
    srcs = [os.path.join(ICI, 'captures', f) for f in sorted(os.listdir(os.path.join(ICI, 'captures')))]
    tout = {}
    for i, f in enumerate(srcs):
        W, H, b = etiqueter(f)
        tout[f] = dict(W=W, H=H, boites=b)
        print(i, os.path.basename(f)[:12], [(x['c'], x['d']) for x in b], flush=True)
    json.dump(tout, open(os.path.join(ICI, 'etiquettes.json'), 'w'), indent=1)
