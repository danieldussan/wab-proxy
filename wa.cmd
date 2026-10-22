@echo off
rem Lanzador para Windows (CMD y PowerShell):  wa <comando>      (por ejemplo: wa dashboard)
rem Si no hay Python instalado, descarga una copia portable en .python\ (sin administrador).
setlocal
cd /d "%~dp0"
set "PY=.python\python.exe"
if exist "%PY%" goto run
for %%C in (python py) do (
  %%C -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1 && (set "PY=%%C" & goto run)
)
echo Primera vez: descargando Python portable ^(unos 10 MB, sin instalar nada^)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\get-python.ps1"
if errorlevel 1 (
  echo No pude descargar Python. Instalalo desde https://www.python.org/downloads/ y vuelve a intentarlo.
  exit /b 1
)
set "PY=.python\python.exe"
:run
"%PY%" wa.py %*
exit /b %errorlevel%
