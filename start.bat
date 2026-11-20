@echo off
set PLMS_ROOT=%~dp0
"%PLMS_ROOT%.venv\Scripts\python.exe" "%PLMS_ROOT%src\PrintLabelMS\__main__.py" "%PLMS_ROOT%settings.json"
