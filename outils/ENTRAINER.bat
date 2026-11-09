@echo off
chcp 65001 >nul
rem Reentraine le detecteur (carte graphique NVIDIA conseillee). Reserve aux curieux : le bot fonctionne sans.
where py >nul 2>nul && (set PY=py) || (set PY=python)
%PY% -c "import torch, ultralytics" 2>nul || (
  %PY% -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
  %PY% -m pip install ultralytics onnx onnxslim
)
cd /d "%~dp0"
%PY% entrainer_gpu.py %1
pause
