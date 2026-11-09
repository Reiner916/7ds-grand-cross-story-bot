@echo off
chcp 65001 >nul
rem ===== Bot 7DS : double-clic ici pour lancer le bot =====
rem Le jeu tourne en administrateur : le bot doit l'etre aussi pour pouvoir cliquer.
net session >nul 2>&1 || (powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b)
cd /d "%~dp0_moteur"
where py >nul 2>nul && (set PY=py) || (set PY=python)
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
  echo [!] Le bot n'a pas pu demarrer. As-tu lance INSTALLER.bat une fois ?
)
pause
