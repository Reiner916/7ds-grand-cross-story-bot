@echo off
chcp 65001 >nul
rem ===== A lancer UNE SEULE FOIS : installe les modules Python du bot =====
rem Le detecteur - onnxruntime - n'existe pas encore pour Python 3.15 : on prend 3.14, 3.13, 3.12 ou 3.11
set PY=
for %%V in (3.14 3.13 3.12 3.11) do if not defined PY py -%%V --version >nul 2>&1 && set "PY=py -%%V"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY echo [!] Python est introuvable. Installe Python 3.14 en cochant "Add python.exe to PATH", puis relance INSTALLER.bat.
if not defined PY start https://www.python.org/downloads/release/python-31410/
if not defined PY pause
if not defined PY exit /b
%PY% --version
%PY% -m pip install --upgrade pip
%PY% -m pip install opencv-python numpy mss
rem Detecteur : sur la carte graphique si possible - DirectML - sinon sur le processeur
%PY% -m pip install onnxruntime-directml || %PY% -m pip install onnxruntime
set OK=
%PY% -c "import onnxruntime, cv2, numpy, mss" >nul 2>&1 && set OK=1
if defined OK (echo %PY%)>"%~dp0_moteur\python.txt"
echo.
if defined OK echo Installation terminee. Lance maintenant 0_LANCER.bat
if not defined OK echo [!] Ta version de Python est trop recente : le detecteur onnxruntime n'existe pas encore pour elle.
if not defined OK echo     Installe en plus Python 3.14 : la page va s'ouvrir, prends "Windows installer 64-bit",
if not defined OK echo     coche "Add python.exe to PATH", puis relance INSTALLER.bat.
if not defined OK start https://www.python.org/downloads/release/python-31410/
pause
