# Réentraîne le détecteur 7DS sur la carte graphique, puis met à jour le bot.
import os, shutil, sys
from datetime import datetime
ICI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_moteur")   # le bot (détecteur, modele.pt, donnees)
DS = os.path.join(ICI, "donnees")
BOT = ICI
SAUV = os.path.join(ICI, "sauvegardes")
CLASSES = ['passer', 'skip', 'ok', 'ok_victoire', 'en_avant', 'choix_auto', 'terminer',
           'demarrer', 'aller', 'principal', 'journal', 'bulle', 'combat', 'cuisine', 'hud']
EPOQUES = int(sys.argv[1]) if len(sys.argv) > 1 else 10

def main():
    import torch
    from ultralytics import YOLO
    gpu = torch.cuda.is_available()
    print("Carte graphique :", torch.cuda.get_device_name(0) if gpu else "INTROUVABLE")
    if not gpu:
        print("La carte graphique n'est pas utilisée (ce serait ~2 h) : entraînement annulé. Lance INSTALLER.bat."); sys.exit(1)

    with open(os.path.join(DS, "data.yaml"), "w", encoding="utf-8") as f:
        f.write(f"path: {DS}\ntrain: images/train\nval: images/val\nnames:\n" + "".join(f"  {i}: {c}\n" for i, c in enumerate(CLASSES)))

    YOLO(os.path.join(ICI, "modele.pt")).train(
        data=os.path.join(DS, "data.yaml"), imgsz=960, epochs=EPOQUES, batch=8, workers=4, cache='ram', amp=True,
        device=0, fliplr=0.0, mosaic=1.0, scale=0.3, translate=0.1, hsv_h=0.015,
        close_mosaic=3, lr0=0.002, warmup_epochs=0, project=os.path.join(ICI, "runs"), name="ft",
        exist_ok=True, plots=False, verbose=False)

    best = os.path.join(ICI, "runs", "ft", "weights", "best.pt")
    # garde-fou : le nouveau détecteur doit faire au moins aussi bien que l'ancien sur les captures de contrôle
    # captures de contrôle = toutes les VRAIES captures (pas les écrans fabriqués)
    import glob, re
    vraies = [f for f in glob.glob(os.path.join(DS, "images", "*", "*.jpg"))
              if not re.match(r"^(s_|p_|v_p|[a-z0-9]+_s\d)", os.path.basename(f))]
    open(os.path.join(DS, "controle.txt"), "w").write("\n".join(vraies))
    with open(os.path.join(DS, "controle.yaml"), "w", encoding="utf-8") as f:
        f.write(f"path: {DS}\ntrain: controle.txt\nval: controle.txt\nnames:\n" + "".join(f"  {i}: {c}\n" for i, c in enumerate(CLASSES)))
    print(f"\nContrôle sur {len(vraies)} vraies captures...")
    def score(pt):
        m = YOLO(pt).val(data=os.path.join(DS, "controle.yaml"), imgsz=960, device=0, batch=4, plots=False, verbose=False)
        return float(m.box.map50), float(m.box.map)
    ancien, nouveau = score(os.path.join(ICI, "modele.pt")), score(best)
    msg = f"Contrôle : ancien {ancien[0]:.3f}/{ancien[1]:.3f}  nouveau {nouveau[0]:.3f}/{nouveau[1]:.3f}"
    print("\n" + msg)
    with open(os.path.join(ICI, "journal_entrainement.txt"), "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%d/%m %H:%M} {len(vraies)} vraies captures - {msg} -> "
                + ("REFUSÉ" if nouveau[0] < ancien[0] - 0.02 else "installé") + "\n")
    if nouveau[0] < ancien[0] - 0.02:      # mAP50 sur les vraies captures : 2 points de marge (le reste fluctue trop)
        shutil.rmtree(os.path.join(ICI, "runs"), ignore_errors=True)
        print("\nLe nouveau détecteur est MOINS BON : l'ancien est conservé (rien n'a changé).")
        sys.exit(2)
    os.makedirs(SAUV, exist_ok=True)
    shutil.copy(os.path.join(ICI, "modele.pt"), os.path.join(SAUV, "modele_precedent.pt"))
    shutil.copy(best, os.path.join(ICI, "modele.pt"))
    onnx = YOLO(best).export(format="onnx", imgsz=960)
    cible = os.path.join(BOT, "detecteur_7ds.onnx")
    if os.path.exists(cible): shutil.copy(cible, os.path.join(SAUV, "detecteur_precedent.onnx"))
    shutil.copy(onnx, cible)
    shutil.rmtree(os.path.join(ICI, "runs"), ignore_errors=True)
    try: os.remove(os.path.join(ICI, "a_entrainer"))
    except Exception: pass
    print("\nOK : nouveau détecteur installé (l'ancien est gardé dans _moteur\\sauvegardes).")


if __name__ == '__main__':   # obligatoire sous Windows (chargement des images en parallèle)
    main()
