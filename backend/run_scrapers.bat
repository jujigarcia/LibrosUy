@echo off
REM Corre todos los scrapers de LibrosUy y guarda la salida en backend\logs\.
REM Pensado para el Programador de tareas de Windows (ver README / run_scrapers.py).
cd /d "%~dp0"
if not exist logs mkdir logs
set PYTHONIOENCODING=utf-8
"%~dp0venv\Scripts\python.exe" run_scrapers.py >> "logs\scrapers.log" 2>&1
