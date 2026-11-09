# Détecteur YOLO (ONNX) partagé par le bot et les tests
import numpy as np, cv2, onnxruntime as ort, os
CLASSES = ['passer', 'skip', 'ok', 'ok_victoire', 'en_avant', 'choix_auto', 'terminer',
           'demarrer', 'aller', 'principal', 'journal', 'bulle', 'combat', 'cuisine', 'hud']
SEUIL = 0.55
SEUILS_CLASSE = {'combat': 0.30, 'bulle': 0.30, 'cuisine': 0.80}   # icône pause du combat : peu d'exemples, seuil plus bas (0 faux positif vérifié)
MODELE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "detecteur_7ds.onnx")
sess = ort.InferenceSession(MODELE, providers=ort.get_available_providers())
ENTREE = sess.get_inputs()[0]
TAILLE = ENTREE.shape[2] if isinstance(ENTREE.shape[2], int) else 960

def detecter(img):
    """Renvoie {classe: [(cx, cy, confiance), ...]} en pixels de l'image."""
    h, w = img.shape[:2]
    r = TAILLE / max(h, w)
    nh, nw = int(round(h * r)), int(round(w * r))
    toile = np.full((TAILLE, TAILLE, 3), 114, np.uint8)
    toile[:nh, :nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    x = toile[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
    sortie = sess.run(None, {ENTREE.name: x})[0][0]          # (4+nc, N)
    sortie = sortie.T
    scores = sortie[:, 4:]
    cl = scores.argmax(1); conf = scores.max(1)
    seuil = np.array([SEUILS_CLASSE.get(c, SEUIL) for c in CLASSES], np.float32)
    garde = conf >= seuil[cl]
    b, cl, conf = sortie[garde, :4], cl[garde], conf[garde]
    res = {}
    if len(b):
        boites = [[float(cx - bw/2), float(cy - bh/2), float(bw), float(bh)] for cx, cy, bw, bh in b]
        for i in np.array(cv2.dnn.NMSBoxes(boites, conf.tolist(), 0.0, 0.45)).flatten():
            cx, cy = b[i][0] / r, b[i][1] / r
            if CLASSES[cl[i]] == 'bulle':
                cy += 0.18 * b[i][3] / r      # vise le corps de la bulle, pas la petite flèche au-dessus (non cliquable)
            res.setdefault(CLASSES[cl[i]], []).append((cx, cy, float(conf[i])))
    for k in res: res[k].sort(key=lambda t: -t[2])
    return res

