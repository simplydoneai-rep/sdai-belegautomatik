@echo off
rem Startet die Demo "Beleg rein - Buchungsvorschlag raus" auf diesem PC (keine KI-Kosten).
rem Danach im Browser oeffnen: http://127.0.0.1:8077
cd /d "%~dp0"
echo Demo startet ... (beim ersten Start ca. 10 Sekunden fuer die Texterkennung)
start "" http://127.0.0.1:8077
backend\.venv\Scripts\python.exe -m uvicorn app.api.demo:app --app-dir backend --host 127.0.0.1 --port 8077
pause
