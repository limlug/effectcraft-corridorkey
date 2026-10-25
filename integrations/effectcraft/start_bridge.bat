@echo off
setlocal
set "RUNTIME_PYTHON=%~dp0..\..\venv\Scripts\python.exe"
if defined CORRIDORKEY_PYTHON set "RUNTIME_PYTHON=%CORRIDORKEY_PYTHON%"
set "ENTRY=%~dp0bridge.py"
if "%~1"=="--launch" set "ENTRY=%~dp0launch.py"
if exist "%RUNTIME_PYTHON%" (
  "%RUNTIME_PYTHON%" "%ENTRY%" %*
) else (
  python "%ENTRY%" %*
)
pause
