# PowerShell run script for backend scaffold
python -m uvicorn backend.app:app --reload
<#
Simple runner for repo2 (PowerShell)
Usage:
  .\run.ps1            -> run CLI (interactive)
  .\run.ps1 install    -> pip install -r requirements.txt
  .\run.ps1 test       -> run pytest
  .\run.ps1 <file>     -> run CLI with provided URL file
#>

param([string]$cmd)

if ($cmd -eq 'install') {
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    exit 0
}

if ($cmd -eq 'test') {
    python -m pytest -q
    exit 0
}

if ($cmd -and (Test-Path $cmd)) {
    python -m cli.main $cmd
    exit 0
}

# Default: run CLI
python -m cli.main
exit 0
