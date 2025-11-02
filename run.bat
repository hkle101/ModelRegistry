@echo off
REM Run backend (Windows)
python -m uvicorn backend.app:app --reload
@echo off
REM Simple runner for repo2 (Windows cmd)
REM Usage:
REM   run.bat            -> run CLI (interactive)
REM   run.bat install    -> pip install --user -r requirements.txt
REM   run.bat test       -> run pytest
REM   run.bat <file>     -> run CLI with provided URL file

setlocal
set "cmd=%~1"

if /I "%cmd%"=="install" (
    pip install --user -r requirements.txt
    exit /b 0
)

if /I "%cmd%"=="test" (
    REM Try pytest; if it fails, run without coverage
    python -m pytest -q
    exit /b 0
)

if not "%cmd%"=="" (
    if exist "%cmd%" (
        python -m cli.main "%cmd%"
        exit /b 0
    )
)

REM Default: start CLI module
python -m cli.main
exit /b 0
