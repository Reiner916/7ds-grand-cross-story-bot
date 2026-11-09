@echo off
chcp 65001 >nul
rem ===== A lancer UNE SEULE FOIS : installe les modules Python du bot =====
where py >nul 2>nul && (set PY=py) || (set PY=python)
%PY% --version >nul 2>&1 || (
  echo [!] Python est introuvable.
  echo     Installe-le depuis https://www.python.org/downloads/ en cochant "Add python.exe to PATH",
  echo     puis relance INSTALLER.bat.
  start https://www.python.org/downloads/
  pause & exit /b
)
%PY% --version
%PY% -m pip install --upgrade pip
%PY% -m pip install opencv-python numpy mss
rem Detecteur : sur la carte graphique si possible (DirectML), sinon sur le processeur
%PY% -m pip install onnxruntime-directml || %PY% -m pip install onnxruntime
%PY% -c "import onnxruntime, cv2, numpy, mss; print(); print('Installation terminée. Lance maintenant 0_LANCER.bat')" || (echo [!] Probleme d'installation : envoie une capture de cette fenetre.)
pause
