# ============================================================
#  7DS Grand Cross - bot mode histoire - version YOLO
#  Démarre tout seul dès que le jeu est ouvert.
#  F8 = pause / reprise   F9 = quitter   F6 = capture   F7 = position du "clic dans le vide"
#  F10 = diagnostic   F11 = enregistrer l'équipe (persos protégés)   F12 = quête principale / secondaire
#  Lancer avec LANCER.bat (droits administrateur, comme le jeu).
# ============================================================
import ctypes, ctypes.wintypes as wt, json, os, sys, time
from datetime import datetime
import numpy as np, cv2, mss

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
MODELE = os.path.join(ICI, "detecteur_7ds.onnx")
REGLAGES = os.path.join(ICI, "reglages.json")
JOURNAL = os.path.join(ICI, "journal.txt")
CAPTURES = os.path.join(ICI, "captures")
RAPPORT = os.path.join(ICI, "..", "rapport.txt")
PIDF = os.path.join(ICI, "bot.pid")

# ---------- Réglages ----------
SEUIL = 0.55          # confiance minimale d'une détection (0-1)
DELAI = 0.4           # s entre deux analyses
PAUSE_CLIC = 1.0      # s après un clic
PAUSE_EQUIPE = 1.2    # s après Choix auto
VIDE_TOUS = 2.0       # sans interface : un clic dans le vide toutes les 2 s
RELANCE_APRES = 5     # en ville sans action depuis 5 s -> reclic quête principale
RELANCE_TOUS = 12     # au plus une relance toutes les 12 s
MARCHE = 12           # après "Aller" ou une bulle : on laisse Meliodas marcher 12 s avant de relancer
VIDE_SECOURS = 30     # en ville sans rien depuis 30 s (relance faite) -> un clic dans le vide toutes les 10 s
ALERTE_RIEN = 15      # rien d'utile depuis 15 s -> journal + capture
STOP_RIEN = 60        # rien d'utile depuis 60 s -> arrêt
MEME_BOUTON_MAX = 4   # même bouton 4 fois de suite sans progrès -> arrêt
EMPRUNT_APRES = 2     # 2 échecs "personnage requis" -> emprunt du héros
LANCEMENTS_MAX = 4    # 4 échecs en 1 min -> arrêt
REPRENDRE_MAX = 2     # défaite : au plus 2 « Reprendre » gratuits par combat, puis arrêt
ATTENTE_FAILED = 5    # s pour laisser apparaître les boutons de l'écran FAILED (fondu)
REPRISES_MAX = 3      # avant d'abandonner, 3 tentatives de dégagement (clics dans le vide + relance quête)
CAPTURES_JOURS = 7    # les captures de plus de 7 jours sont effacées au démarrage
PLACER_REQUIS = True  # héros requis "étrangers" déplacés en case 4 puis 3 (les persos protégés restent)
QUETE_SUIVIE = 2      # 1 = quête principale (jaune, 1re case du journal) ; 2 = quête secondaire (2e case)

CLASSES = ['passer', 'skip', 'ok', 'ok_victoire', 'en_avant', 'choix_auto', 'terminer',
           'demarrer', 'aller', 'principal', 'journal', 'bulle', 'combat', 'cuisine', 'hud']
# ordre de priorité des boutons cliqués directement
BOUTONS = ['ok_victoire', 'skip', 'passer', 'terminer', 'demarrer', 'aller', 'principal']

# ---------- Windows : DPI, fenêtre, souris, touches ----------
u32 = ctypes.windll.user32
try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception: u32.SetProcessDPIAware()

def fenetre_active():
    """Fenêtre du jeu (titre '7DS', moteur Unity), même si une autre fenêtre est active."""
    h = u32.FindWindowW("UnityWndClass", "7DS") or u32.FindWindowW(None, "7DS")
    return h or u32.GetForegroundWindow()

def zone_client(hwnd):
    r = wt.RECT(); u32.GetClientRect(hwnd, ctypes.byref(r))
    p = wt.POINT(0, 0); u32.ClientToScreen(hwnd, ctypes.byref(p))
    return p.x, p.y, r.right, r.bottom

def cliquer(x, y):
    u32.SetCursorPos(int(x), int(y)); time.sleep(0.05)
    u32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.05)   # bouton gauche bas
    u32.mouse_event(0x0004, 0, 0, 0, 0)                     # bouton gauche haut

def glisser(x1, y1, x2, y2):
    u32.SetCursorPos(int(x1), int(y1)); time.sleep(0.15)
    u32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.35)          # appui long sur la carte
    for i in range(1, 16):                                         # glissement progressif
        u32.SetCursorPos(int(x1 + (x2 - x1) * i / 15), int(y1 + (y2 - y1) * i / 15)); time.sleep(0.03)
    time.sleep(0.3); u32.mouse_event(0x0004, 0, 0, 0, 0)           # lâcher

F6, F7, F8, F9, F10, F11, F12 = 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x7B
import threading, queue
TOUCHES = queue.Queue()
def _ecoute_touches():
    """Fil séparé : surveille F6-F10 toutes les 15 ms, même quand le bot est occupé à cliquer."""
    avant = {}
    while True:
        for vk in (F6, F7, F8, F9, F10, F11, F12):
            bas = bool(u32.GetAsyncKeyState(vk) & 0x8000)
            if bas and not avant.get(vk): TOUCHES.put(vk)
            avant[vk] = bas
        time.sleep(0.015)

# ---------- Détecteur YOLO (ONNX) ----------
import detecteur
from detecteur import detecter, sess
detecteur.SEUIL = SEUIL

# ---------- Combat : icône pause en haut à droite (comparaison d'image exacte, fiable à 100 %) ----------
_P = cv2.imread(os.path.join(ICI, "img", "combat.png")).astype(np.int16)
_PM = ~np.all(_P == [255, 0, 255], axis=2)
_PMK = np.repeat(_PM[:, :, None], 3, 2).astype(np.float32)
def combat_visible(img, tol=45):
    H, W = img.shape[:2]
    sub = img[0:int(0.08 * H) + _P.shape[0], int(0.85 * W):].astype(np.int16)
    r = cv2.matchTemplate(sub.astype(np.float32), _P.astype(np.float32), cv2.TM_SQDIFF, mask=_PMK)
    r = np.nan_to_num(r, nan=1e18, posinf=1e18)
    for i in np.argsort(r, axis=None)[:10]:
        y, x = np.unravel_index(i, r.shape)
        if np.abs(sub[y:y+_P.shape[0], x:x+_P.shape[1]] - _P).max(2)[_PM].max() <= tol: return True
    return False

# ---------- Écran "QUEST REWARD" (comparaison d'image, fiable à 100 %) ----------
_QR = cv2.imread(os.path.join(ICI, "img", "quest_reward.png"), 0)
def recompense_visible(img):
    H, W = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (1920, 1080)) if (W, H) != (1920, 1080) else g
    return cv2.matchTemplate(g[250:550, 700:1220], _QR, cv2.TM_CCOEFF_NORMED).max() > 0.8

# ---------- Écrans reconnus par comparaison d'image (OK vert VICTORY, SKIP, FAILED) ----------
_TPL = {n: cv2.imread(os.path.join(ICI, "img", n + ".png"), 0) for n in ("ok_vert", "skip", "failed", "reprendre_gratuit")}
_ZONE = {"ok_vert": ((700, 850, 1220, 1080), 0.9), "skip": ((1700, 60, 1920, 170), 0.65), "failed": ((600, 60, 1320, 330), 0.8),
         "reprendre_gratuit": ((700, 940, 1100, 1060), 0.8)}   # badge « Gratuit » du bouton Reprendre (écran FAILED)
def trouver(img, nom):
    """Centre (en pixels de l'image) du modèle 'nom' s'il est à l'écran, sinon None."""
    H, W = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if (W, H) != (1920, 1080): g = cv2.resize(g, (1920, 1080))
    (x0, y0, x1, y1), seuil = _ZONE[nom]; t = _TPL[nom]
    m = cv2.matchTemplate(g[y0:y1, x0:x1], t, cv2.TM_CCOEFF_NORMED)
    if m.max() < seuil: return None
    y, x = np.unravel_index(m.argmax(), m.shape)
    return ((x0 + x + t.shape[1] / 2) * W / 1920, (y0 + y + t.shape[0] / 2) * H / 1080)

# ---------- Journal : position de la quête à relancer ----------
def position_quete(img, jx, jy):
    """Point à cliquer (pixels de l'image) pour relancer la quête suivie : 1re ou 2e case du journal."""
    H, W = img.shape[:2]; sx, sy = W / 1920, H / 1080
    if QUETE_SUIVIE == 1: return jx - 95 * sx, jy + 55 * sy
    return jx - 80 * sx, jy + 118 * sy             # titre de la 2e case (sous "Mise à jour programmée")

# ---------- Écran d'équipe : bandeau "Héros requis" et persos protégés (comparaison d'image) ----------
CASES_X = [772, 897, 1022, 1147]          # centre des 4 cases du haut (écran 1920x1080) ; la 4e = SUB
CASE_Y = 380
_BAN = cv2.imread(os.path.join(ICI, "img", "heros_requis.png"), 0)
_PERSOS = {}
for _f in sorted(os.listdir(os.path.join(ICI, "img"))):
    if _f.startswith("perso_"):
        _PERSOS.setdefault(_f[6:].rsplit("_", 1)[0], []).append(cv2.imread(os.path.join(ICI, "img", _f), 0))

def analyse_equipe(img):
    """Pour chaque case : (requis ?, nom du perso protégé ou None)."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if g.shape[:2] != (1080, 1920): g = cv2.resize(g, (1920, 1080))
    res = []
    for cx in CASES_X:
        req = cv2.matchTemplate(g[276:318, cx-62:cx+62], _BAN, cv2.TM_CCOEFF_NORMED).max() > 0.6
        z = g[307:433, cx-53:cx+53]
        nom, best = None, 0.7
        for n, refs in _PERSOS.items():
            for r in refs:
                v = cv2.matchTemplate(z, r, cv2.TM_CCOEFF_NORMED).max()
                if v > best: nom, best = n, v
        res.append((bool(req), nom))
    return res

def recharger_persos():
    _PERSOS.clear()
    for f in sorted(os.listdir(os.path.join(ICI, "img"))):
        if f.startswith("perso_"):
            _PERSOS.setdefault(f[6:].rsplit("_", 1)[0], []).append(cv2.imread(os.path.join(ICI, "img", f), 0))

def enregistrer_equipe(img):
    """F11 sur un écran d'équipe : les 4 persos du haut deviennent les persos protégés (jamais déplacés)."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if g.shape[:2] != (1080, 1920): g = cv2.resize(g, (1920, 1080))
    dossier = os.path.join(ICI, "img")
    for f in os.listdir(dossier):
        if f.startswith("perso_"): os.remove(os.path.join(dossier, f))
    for k, cx in enumerate(CASES_X):
        cv2.imwrite(os.path.join(dossier, f"perso_case{k+1}_1.png"), g[315:425, cx-45:cx+45])
    recharger_persos()

def texte_equipe(eq):
    return " | ".join(f"{i+1}:{(n or '?')}{' (requis)' if r else ''}" for i, (r, n) in enumerate(eq))

# ---------- Outils ----------
def log(txt):
    ligne = f"{datetime.now():%H:%M:%S} {txt}"
    print(ligne)
    with open(JOURNAL, "a", encoding="utf-8") as f: f.write(ligne + "\n")

def capture(img, motif):
    os.makedirs(CAPTURES, exist_ok=True)
    f = os.path.join(CAPTURES, f"{datetime.now():%H%M%S}_{motif}.png")
    cv2.imwrite(f, img); return f

def menage_captures():
    if not os.path.isdir(CAPTURES): return
    limite = time.time() - CAPTURES_JOURS * 86400
    for f in os.listdir(CAPTURES):
        p = os.path.join(CAPTURES, f)
        try:
            if os.path.getmtime(p) < limite: os.remove(p)
        except Exception: pass

def lire_reglages():
    r = {"vide_x": 0.745, "vide_y": 0.464}
    try:
        lu = json.load(open(REGLAGES, encoding="utf-8"))
        if not (0 < lu.get("vide_x", 0.5) < 1 and 0 < lu.get("vide_y", 0.5) < 1):
            lu.pop("vide_x", None); lu.pop("vide_y", None)
        r.update(lu)
    except Exception: pass
    return r

def ecrire_reglages(r):
    json.dump(r, open(REGLAGES, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

def appliquer_reglages(r):
    global QUETE_SUIVIE, PLACER_REQUIS
    QUETE_SUIVIE = int(r.get("quete_suivie", QUETE_SUIVIE)); PLACER_REQUIS = bool(r.get("placer_requis", PLACER_REQUIS))

def assistant(r):
    """Premier lancement : 1 question (la quête), puis rappel de F11 pour l'équipe."""
    print("\n" + "=" * 70 + "\n  PREMIER LANCEMENT - 1 réglage (modifiable plus tard avec F12)\n" + "=" * 70)
    print("  Quelle quête le bot doit-il suivre ? (journal en haut à droite de l'écran du jeu)")
    print("    1 = la quête PRINCIPALE  (1re ligne, en jaune)  -> pour avancer dans l'histoire")
    print("    2 = la quête SECONDAIRE  (2e ligne, en bleu)   -> quand la 1re ligne affiche \"Mise à jour programmée\"")
    while True:
        c = input("  Tape 1 ou 2 puis Entrée : ").strip()
        if c in ("1", "2"): break
    r["quete_suivie"] = int(c); r.setdefault("placer_requis", True); ecrire_reglages(r)
    print("  OK, quête", "principale" if c == "1" else "secondaire", "enregistrée.\n")

def clignoter_console():
    h = ctypes.windll.kernel32.GetConsoleWindow()
    class FW(ctypes.Structure):
        _fields_ = [("cbSize", wt.UINT), ("hwnd", wt.HWND), ("dwFlags", wt.DWORD), ("uCount", wt.UINT), ("dwTimeout", wt.DWORD)]
    fw = FW(ctypes.sizeof(FW), h, 3 | 12, 5, 0)   # barre des tâches clignote (silencieux)
    u32.FlashWindowEx(ctypes.byref(fw))

# ---------- Bot ----------
class Bot:
    def __init__(self):
        self.actif = False; self.hwnd = 0
        self.reg = lire_reglages()
        self.stats = dict(debut=None, combats=0, victoires=0, recompenses=0, potions=0, equipes=0, reprises=0, defaites_reprises=0, arrets=[])
        self.dernier_rapport = time.time()
        self.reset()

    def reset(self):
        t = time.time()
        self.dernier_utile = self.derniere_alerte = self.dernier_vide = t
        self.derniere_relance = 0; self.dernier_combat = 0
        self.equipe_faite = False; self.essais_equipe = 0
        self.lancements = []; self.emprunt_fait = False
        self.dernier_bouton = ""; self.meme_bouton = 0
        self.bulles_ignorees = []      # [(x, y, jusqu'à)] bulles cliquées 3 fois sans effet
        self.derniere_bulle = None; self.clics_bulle = 0; self.t_bulle = 0
        self.placement_fait = False; self.t_en_avant = 0; self.t_potion = 0
        self.reprises = 0; self.dernier_journal = None
        self.t_marche = 0; self.hist_bulles = []      # [(x, y, t)] clics de bulles récents
        self.ok_apres_relance = 0; self.img = None
        self.reprendre_faits = 0; self.t_failed = 0      # défaite : « Reprendre » gratuits cliqués sur ce combat

    def ecran(self):
        x, y, w, h = zone_client(self.hwnd)
        with (mss.MSS() if hasattr(mss, 'MSS') else mss.mss()) as s:
            img = np.array(s.grab({"left": x, "top": y, "width": w, "height": h}))[:, :, :3]
        return img, x, y, w, h

    def stop(self, raison, img=None):
        self.actif = False
        log(f"STOP : {raison}")
        self.stats["arrets"].append(f"{datetime.now():%H:%M} {raison}"); self.rapport()
        if img is not None: capture(img, "stop")
        clignoter_console()
        print("\n>>> Bot arrêté. Corrige à la main puis F8 pour relancer.\n")

    def rapport(self):
        st = self.stats
        if not st["debut"]: return
        duree = int(time.time() - st["debut"]); h, m = duree // 3600, duree % 3600 // 60
        lignes = [f"RAPPORT DU BOT 7DS - {datetime.now():%d/%m %H:%M}",
                  f"Début : {datetime.fromtimestamp(st['debut']):%d/%m %H:%M}   Durée : {h} h {m:02d}",
                  f"Combats lancés : {st['combats']}   Victoires : {st['victoires']}   Récompenses de quête : {st['recompenses']}",
                  f"Potions d'endurance utilisées : {st['potions']}   Équipes réorganisées : {st['equipes']}   Reprises auto : {st['reprises']}",
                  f"Défaites reprises (Reprendre gratuit) : {st['defaites_reprises']}",
                  f"Arrêts : {len(st['arrets'])}"] + [f"  - {a}" for a in st["arrets"]]
        try: open(RAPPORT, "w", encoding="utf-8").write("\n".join(lignes) + "\n")
        except Exception: pass

    def placer_requis(self, img, ox, oy, w, h):
        """Héros requis qui ne sont pas des persos protégés -> cases de droite (4 puis 3)."""
        sx, sy = w / 1920, h / 1080
        eq = analyse_equipe(img); log(f"équipe : {texte_equipe(eq)}")
        for _ in range(2):
            etrangers = [k for k, (r, n) in enumerate(eq) if r and not n]
            # 1 requis -> case 4 (SUB) ; 2 requis -> le plus fort (le plus à gauche) en case 3 (reste au combat), l'autre en case 4
            cibles = [3] if len(etrangers) == 1 else [2, 3]
            mal_places = sorted(k for k in etrangers if k not in cibles)
            libres = [t for t in cibles if t not in etrangers]
            if not mal_places or not libres: return
            src, dst = mal_places[0], libres[0]
            glisser(ox + CASES_X[src] * sx, oy + CASE_Y * sy, ox + CASES_X[dst] * sx, oy + CASE_Y * sy)
            log(f"héros requis déplacé : case {src+1} -> case {dst+1}"); time.sleep(1.0)
            img, *_ = self.ecran(); eq2 = analyse_equipe(img)
            if not (eq2[dst][0] and not eq2[dst][1]):
                log(f"déplacement refusé par le jeu, équipe laissée telle quelle ({texte_equipe(eq2)})"); return
            eq = eq2; self.stats["equipes"] += 1

    def defaite(self, img, ox, oy, w, h, maint):
        """Écran FAILED : « Reprendre » s'il est gratuit (l'ennemi garde ses PV), au plus REPRENDRE_MAX fois ; sinon arrêt."""
        if maint - self.t_failed > 20: self.t_failed = maint               # nouvel écran FAILED
        if self.reprendre_faits >= REPRENDRE_MAX:
            return self.stop(f"Défaite : {REPRENDRE_MAX} reprises gratuites déjà utilisées, équipe trop faible ?", img)
        p = trouver(img, "reprendre_gratuit")
        if p:
            self.reprendre_faits += 1; self.stats["defaites_reprises"] += 1
            cliquer(ox + p[0], oy + p[1] + 12 * h / 1080)                  # bouton Reprendre, juste sous le badge
            log(f"défaite : clic Reprendre (gratuit, {self.reprendre_faits}/{REPRENDRE_MAX})")
            self.dernier_utile = maint; self.reprises = 0; self.t_failed = 0
            time.sleep(PAUSE_CLIC * 2); return
        if maint - self.t_failed < ATTENTE_FAILED: return                   # boutons encore en fondu : on attend
        return self.stop("Défaite (écran FAILED) : pas de reprise gratuite, équipe trop faible ?", img)

    def case_emprunt(self, img):
        """Case la plus à droite qui n'est pas occupée par un héros requis."""
        eq = analyse_equipe(img)
        for k in (3, 2, 1, 0):
            if not eq[k][0]: return k
        return 3

    def clic(self, nom, cx, cy, ox, oy):
        rapide = time.time() - getattr(self, "t_bouton", 0) < 20
        self.meme_bouton = self.meme_bouton + 1 if (nom == self.dernier_bouton and rapide) else 1
        self.dernier_bouton = nom; self.t_bouton = time.time()
        if self.meme_bouton > MEME_BOUTON_MAX and nom not in ("ok", "aller"):
            return self.stop(f"Boucle : '{nom}' cliqué {self.meme_bouton} fois d'affilée", self.img)
        cliquer(ox + cx, oy + cy)
        log(f"clic {nom}")
        maint = time.time()
        if not (nom == "aller" and self.meme_bouton > 2):      # 3e "Aller" d'affilée : plus compté comme progrès -> reprise auto
            self.dernier_utile = maint; self.reprises = 0
        if nom == "aller": self.t_marche = maint
        if nom == "ok_victoire": self.stats["victoires"] += 1; self.reprendre_faits = 0
        _, _, _, hh = zone_client(self.hwnd)
        if nom == "ok" and maint - self.t_en_avant < 5 and cy * 1080 / max(hh, 1) > 790:   # "Utiliser" de la popup potion (plus bas qu'un OK normal)
            self.stats["potions"] += 1; self.t_potion = maint; log("potion d'endurance utilisée")
        time.sleep(PAUSE_CLIC)

    def tour(self):
        if not u32.IsWindow(self.hwnd): return self.stop("Fenêtre du jeu introuvable")
        if u32.GetForegroundWindow() != self.hwnd: u32.SetForegroundWindow(self.hwnd)
        img, ox, oy, w, h = self.ecran(); self.img = img
        d = detecter(img)
        maint = time.time()
        a = lambda n: d.get(n, [None])[0]
        if a("journal"): self.dernier_journal = a("journal")[:2]
        if maint - self.dernier_rapport > 1800: self.dernier_rapport = maint; self.rapport()

        if a("cuisine"): return self.stop("Cuisine : choisis les ingrédients à la main", img)
        if trouver(img, "failed"): return self.defaite(img, ox, oy, w, h, maint)

        # 1) popups OK
        if a("ok"): return self.clic("ok", *a("ok")[:2], ox, oy)

        # 1a) OK vert de VICTORY et SKIP (comparaison d'image) - après les popups, car SKIP ouvre une confirmation
        p = trouver(img, "ok_vert") or (a("ok_victoire")[:2] if a("ok_victoire") else None)
        apres_relance = maint - self.derniere_relance < 4 and self.ok_apres_relance >= 2
        if p and (p[0] < 900 * w / 1920 or a("aller") or apres_relance):
            # popup "Une nouvelle aventure est disponible !" : OK vert + Aller jaune -> Aller
            # (ou : OK déjà cliqué 2 fois juste après une relance sans effet -> on tente le bouton de droite)
            al = a("aller")
            return self.clic("aller", *(al[:2] if al else (p[0] + 235 * w / 1920, p[1])), ox, oy)
        if p and maint - self.derniere_relance < 4: self.ok_apres_relance += 1
        p = trouver(img, "ok_vert")
        if p: return self.clic("ok_victoire", p[0], p[1], ox, oy)
        p = trouver(img, "skip")
        if p: return self.clic("skip", p[0], p[1], ox, oy)

        # 1b) écran QUEST REWARD : clic dans le vide pour le fermer
        if recompense_visible(img):
            cliquer(ox + w * self.reg["vide_x"], oy + h * self.reg["vide_y"]); log("clic vide (quest reward)")
            if maint - self.dernier_vide > 5: self.stats["recompenses"] += 1
            self.ok_apres_relance = 0
            self.dernier_utile = self.dernier_vide = maint; self.reprises = 0; time.sleep(PAUSE_CLIC); return

        # 2) écran d'équipe : Choix auto puis En avant !
        if a("en_avant"):
            ex, ey, _ = a("en_avant")
            if not self.equipe_faite:
                if a("choix_auto"):
                    self.clic("choix_auto", *a("choix_auto")[:2], ox, oy)
                else:
                    self.essais_equipe += 1
                    if self.essais_equipe < 4: return
                    # secours : position connue de Choix auto par rapport au centre de "En avant !"
                    cliquer(ox + ex - 202, oy + ey - 381); log("clic choix_auto (position de secours)")
                self.equipe_faite = True; self.essais_equipe = 0; self.placement_fait = False
                time.sleep(PAUSE_EQUIPE); return
            if PLACER_REQUIS and not self.placement_fait:
                self.placement_fait = True
                try: self.placer_requis(img, ox, oy, w, h)
                except Exception as e: log(f"placement des héros requis impossible : {e}")
                return
            self.lancements = [t for t in self.lancements if maint - t < 60]
            potion_recente = maint - self.t_potion < 60
            if len(self.lancements) >= LANCEMENTS_MAX:
                raison = ("Endurance : plus de potions ? (le combat ne se lance pas)" if potion_recente
                          else "Impossible de lancer le combat (personnage requis manquant)")
                return self.stop(raison, img)
            if len(self.lancements) >= EMPRUNT_APRES and not self.emprunt_fait and not potion_recente:
                k = self.case_emprunt(img)
                cliquer(ox + ex - 893, oy + ey - 208); time.sleep(0.8)   # héros emprunté (bas gauche)
                cliquer(ox + CASES_X[k] * w / 1920, oy + CASE_Y * h / 1080); time.sleep(0.8)
                log(f"emprunt du héros requis -> case {k+1} (la plus à droite sans héros requis)")
                self.emprunt_fait = True; return
            self.lancements.append(maint)
            self.clic("en_avant", ex, ey, ox, oy); self.t_en_avant = time.time(); self.reprendre_faits = 0
            self.equipe_faite = False; self.placement_fait = False
            return

        # 3) autres boutons
        for n in BOUTONS:
            if a(n): return self.clic(n, *a(n)[:2], ox, oy)

        # 4) combat
        if a("combat") or combat_visible(img):
            if maint - self.dernier_combat > 30: self.stats["combats"] += 1
            self.dernier_utile = self.dernier_combat = maint; self.reprises = 0; self.dernier_bouton = ""; self.ok_apres_relance = 0
            self.lancements = []; self.emprunt_fait = False
            return
        if maint - self.dernier_combat < 15:      # animation d'ult / changement de vague : on attend
            self.dernier_utile = maint; return

        # 5) surveillance
        rien = maint - self.dernier_utile
        if rien > STOP_RIEN:
            if self.reprises >= REPRISES_MAX:
                return self.stop(f"Rien trouvé à faire depuis {STOP_RIEN} s (après {REPRISES_MAX} reprises auto)", img)
            self.reprises += 1; self.stats["reprises"] += 1
            log(f"reprise auto {self.reprises}/{REPRISES_MAX} : clics dans le vide + relance de la quête"); capture(img, "reprise")
            for _ in range(2):
                cliquer(ox + w * self.reg["vide_x"], oy + h * self.reg["vide_y"]); time.sleep(1.2)
            if self.dernier_journal:
                jx, jy = self.dernier_journal; qx, qy = position_quete(img, jx, jy)
                cliquer(ox + qx, oy + qy); time.sleep(PAUSE_CLIC)
            self.dernier_utile = maint - ALERTE_RIEN; self.derniere_relance = maint; return
        if rien > ALERTE_RIEN and maint - self.derniere_alerte > ALERTE_RIEN:
            self.derniere_alerte = maint
            log(f"rien trouvé depuis {int(rien)} s -> capture"); capture(img, "rien")

        # 6) ville / carte / menus : jamais de clic dans le vide
        if a("journal") or a("hud"):
            self.bulles_ignorees = [b for b in self.bulles_ignorees if b[2] > maint]
            self.hist_bulles = [b for b in self.hist_bulles if maint - b[2] < 60]
            proche = lambda b, c, r=70: abs(b[0]-c[0]) < r and abs(b[1]-c[1]) < r
            libres = [b for b in d.get("bulle", []) if not any(proche(b, i) for i in self.bulles_ignorees)]
            if libres:
                bx, by, _ = libres[0]
                deja = [c for c in self.hist_bulles if proche((bx, by), c)]
                if deja and maint - deja[-1][2] < 5: return        # Meliodas marche peut-être vers la bulle : on lui laisse 5 s
                if len(deja) >= 4:                                  # 4 clics en 1 min au même endroit : fausse bulle, ignorée 2 min
                    self.bulles_ignorees.append((bx, by, maint + 120))
                    log(f"bulle ignorée 2 min (sans effet) en {int(bx)},{int(by)}")
                else:
                    self.dernier_bouton = ""
                    cliquer(ox + bx, oy + by); log("clic bulle")
                    self.hist_bulles.append((bx, by, maint)); self.t_marche = maint
                    # au-delà de 3 clics de bulles en 30 s, ça ne compte plus comme un progrès (la relance / reprise peut agir)
                    if sum(1 for c in self.hist_bulles if maint - c[2] < 30) <= 3:
                        self.dernier_utile = maint; self.reprises = 0
                    time.sleep(PAUSE_CLIC); return
            if a("journal") and rien > RELANCE_APRES and maint - self.derniere_relance > RELANCE_TOUS and maint - self.t_marche > MARCHE:
                self.derniere_relance = maint
                jx, jy, _ = a("journal"); qx, qy = position_quete(img, jx, jy)
                cliquer(ox + qx, oy + qy); log(f"relance quête {'principale' if QUETE_SUIVIE == 1 else 'secondaire'}")
                time.sleep(PAUSE_CLIC); return
            # secours : rien ne bouge malgré la relance (écran assombri, titre de chapitre...) -> clic dans le vide
            if rien > VIDE_SECOURS and maint - self.dernier_vide > 10:
                self.dernier_vide = maint
                cliquer(ox + w * self.reg["vide_x"], oy + h * self.reg["vide_y"]); log("clic vide (secours)")
            return

        # 7) pas d'interface : clic dans le vide
        if maint - self.dernier_vide > VIDE_TOUS:
            self.dernier_vide = maint
            cliquer(ox + w * self.reg["vide_x"], oy + h * self.reg["vide_y"]); log("clic vide")

    def diagnostic(self):
        hwnd = self.hwnd or fenetre_active()
        self.hwnd = hwnd
        img, *_ , w, h = self.ecran()
        t = time.time(); d = detecter(img); ms = (time.time() - t) * 1000
        print(f"\n--- Diagnostic : fenêtre {w}x{h}, analyse en {ms:.0f} ms ---")
        print(f"  combat (icône pause) : {'OUI' if combat_visible(img) else 'non'}")
        print(f"  quest reward : {'OUI' if recompense_visible(img) else 'non'}")
        if "journal" in d: print(f"  quête suivie ({QUETE_SUIVIE}) cliquée en : {tuple(int(v) for v in position_quete(img, *d['journal'][0][:2]))}")
        for n in ("ok_vert", "skip", "failed", "reprendre_gratuit"): print(f"  {n} : {'OUI' if trouver(img, n) else 'non'}")
        if "en_avant" in d: print(f"  équipe : {texte_equipe(analyse_equipe(img))}")
        for c in CLASSES:
            if c in d: print(f"  {c:12s} TROUVÉ  ({d[c][0][2]:.0%})")
        if not d: print("  rien reconnu")
        f = capture(img, "diag"); log(f"DIAG {sorted(d)} -> {os.path.basename(f)}")

def main():
    # un seul bot à la fois (sinon deux bots cliquent en même temps)
    ctypes.windll.kernel32.CreateMutexW(None, False, "7DS_bot_unique")
    if ctypes.windll.kernel32.GetLastError() == 183:
        input("Un bot tourne déjà dans une autre fenêtre : ferme celle-ci (Entrée)."); return
    try: open(PIDF, "w").write(str(os.getpid()))
    except Exception: pass
    menage_captures()
    print(__doc__ or "", "7DS bot prêt. Démarre tout seul. F8 = pause/reprise  F9 = quitter  F6 = capture  F7 = clic vide  F10 = diagnostic  F11 = enregistrer l'équipe  F12 = changer de quête")
    pv = sess.get_providers()
    print("Détecteur sur :", "carte graphique" if any(p in pv[0] for p in ("Dml", "CUDA")) else "processeur", pv)
    bot = Bot(); prochain = 0
    if "quete_suivie" not in bot.reg: assistant(bot.reg)
    appliquer_reglages(bot.reg)
    print("Quête suivie :", "PRINCIPALE (1re ligne du journal)" if QUETE_SUIVIE == 1 else "SECONDAIRE (2e ligne du journal)", "- F12 pour changer")
    if not _PERSOS:
        print("\n  !! Persos protégés pas encore enregistrés. Pour le faire (une seule fois) :")
        print("     dans le jeu, ouvre un ÉCRAN D'ÉQUIPE (celui avec le bouton \"En avant !\") avec tes 4 persos")
        print("     principaux en haut, puis appuie sur F11. Le bot ne déplacera jamais ces 4 persos.\n")
    else:
        print(f"Persos protégés : {len(_PERSOS)} enregistrés (F11 sur un écran d'équipe pour les changer)")
    threading.Thread(target=_ecoute_touches, daemon=True).start()
    # démarrage automatique dès que la fenêtre du jeu est trouvée (F8 ne sert plus qu'à pause / reprise)
    attente = 0
    while not (u32.FindWindowW("UnityWndClass", "7DS") or u32.FindWindowW(None, "7DS")):
        if attente % 15 == 0: print("En attente du jeu 7DS (lance-le, le bot démarrera tout seul)...")
        time.sleep(1); attente += 1
        while not TOUCHES.empty():
            if TOUCHES.get() == F9: print("Au revoir."); return
    for k in (3, 2, 1): print(f"Démarrage automatique dans {k} s..."); time.sleep(1)
    bot.hwnd = fenetre_active(); bot.reset(); bot.actif = True
    bot.stats["debut"] = time.time(); log("---- démarrage automatique ----")
    while True:
        appuis = []
        while not TOUCHES.empty(): appuis.append(TOUCHES.get())
        touche = lambda vk: vk in appuis
        if touche(F9):
            bot.rapport(); print("Au revoir. Rapport écrit dans rapport.txt")
            try: os.remove(PIDF)
            except Exception: pass
            return
        if touche(F8):
            bot.actif = not bot.actif
            if bot.actif:
                bot.hwnd = fenetre_active(); bot.reset()
                bot.stats["debut"] = bot.stats["debut"] or time.time()
                if u32.FindWindowW("UnityWndClass", "7DS") or u32.FindWindowW(None, "7DS"): log("---- démarrage ----")
                else: bot.actif = False; print("Jeu introuvable : lance 7DS puis refais F8.")
            else: log("pause (F8)")
        if touche(F7):
            hwnd = fenetre_active(); x, y, w, h = zone_client(hwnd)
            p = wt.POINT(); u32.GetCursorPos(ctypes.byref(p))
            vx, vy = round((p.x - x) / w, 3), round((p.y - y) / h, 3)
            if 0.02 < vx < 0.98 and 0.02 < vy < 0.98:
                bot.reg.update({"vide_x": vx, "vide_y": vy}); ecrire_reglages(bot.reg)
                print("Clic dans le vide enregistré :", vx, vy)
            else:
                print("F7 ignoré : la souris doit être posée DANS la fenêtre du jeu.")
        if touche(F6):
            bot.hwnd = bot.hwnd or fenetre_active(); img, *_ = bot.ecran(); print("Capture :", capture(img, "manuel"))
        if touche(F10): bot.diagnostic()
        if touche(F11):
            bot.hwnd = bot.hwnd or fenetre_active(); img, *_ = bot.ecran()
            if "en_avant" in detecter(img):
                enregistrer_equipe(img)
                print(">>> Équipe enregistrée : les 4 persos du haut ne seront jamais déplacés par le bot.")
            else:
                print(">>> F11 ignoré : ouvre d'abord un ÉCRAN D'ÉQUIPE (celui avec le bouton \"En avant !\"), puis refais F11.")
        if touche(F12):
            QUETE_SUIVIE_NV = 1 if QUETE_SUIVIE == 2 else 2
            bot.reg["quete_suivie"] = QUETE_SUIVIE_NV; ecrire_reglages(bot.reg); appliquer_reglages(bot.reg)
            print(">>> Quête suivie :", "PRINCIPALE (1re ligne)" if QUETE_SUIVIE == 1 else "SECONDAIRE (2e ligne)")
        if bot.actif and time.time() >= prochain:
            try: bot.tour()
            except Exception as e: log(f"erreur : {e}")
            prochain = time.time() + DELAI
        time.sleep(0.03)

if __name__ == "__main__":
    main()
