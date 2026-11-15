@echo off
REM Sincroniza el stock de LibrosUy (scrapers + planillas) y guarda la salida en backend\logs\.
REM Pensado para el Programador de tareas de Windows (ver run_scrapers.py y sync_sheets.py).
cd /d "%~dp0"
if not exist logs mkdir logs
set PYTHONIOENCODING=utf-8
"%~dp0venv\Scripts\python.exe" run_scrapers.py >> "logs\scrapers.log" 2>&1
"%~dp0venv\Scripts\python.exe" sync_sheets.py >> "logs\scrapers.log" 2>&1
