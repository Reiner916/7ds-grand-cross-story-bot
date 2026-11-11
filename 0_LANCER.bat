@echo off
chcp 65001 >nul
rem ===== Bot 7DS : double-clic ici pour lancer le bot =====
rem Le jeu tourne en administrateur : le bot doit l'etre aussi pour pouvoir cliquer.
net session >nul 2>&1 || (powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b)
cd /d "%~dp0_moteur"
rem Meme Python qu'INSTALLER.bat : celui note dans python.txt, sinon 3.14 / 3.13 / 3.12 / 3.11, sinon python
set PY=
if exist python.txt set /p PY=<python.txt
for %%V in (3.14 3.13 3.12 3.11) do if not defined PY py -%%V --version >nul 2>&1 && set "PY=py -%%V"
if not defined PY set PY=python
title 7DS bot
if exist bot.pid (
  set /p VIEUX=<bot.pid
  call taskkill /PID %%VIEUX%% /T /F >nul 2>&1
  del bot.pid >nul 2>&1
)
echo === Lancement du bot : il demarre tout seul, F8 = pause ou reprise ===
%PY% bot_7ds.py
if errorlevel 1 (
  echo.
  echo [!] Le bot n'a pas pu demarrer avec %PY%.
  echo     Relance INSTALLER.bat et attends le message Installation terminee, puis relance 0_LANCER.bat.
)
pause
