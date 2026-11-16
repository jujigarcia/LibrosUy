@echo off
REM Busca librerias nuevas en OpenStreetMap una vez por semana (quedan ocultas hasta revisarlas).
REM Pensado para el Programador de tareas de Windows (tarea "LibrosUy Nuevas Librerias").
cd /d "%~dp0"
if not exist logs mkdir logs
set PYTHONIOENCODING=utf-8
echo === %date% %time% ===>> "logs\nuevas_librerias.log"
"%~dp0venv\Scripts\python.exe" seed_stores.py >> "logs\nuevas_librerias.log" 2>&1
