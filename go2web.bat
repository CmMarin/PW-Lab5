@echo off
set VENV_PYTHON="%~dp0.venv\Scripts\python.exe"
if exist %VENV_PYTHON% (
    %VENV_PYTHON% "%~dp0go2web.py" %*
) else (
    python "%~dp0go2web.py" %*
)
