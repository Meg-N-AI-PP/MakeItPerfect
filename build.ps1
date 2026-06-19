# Builds a portable single-file SentenceTool.exe into the dist\ folder.
# Usage:  .\build.ps1
$ErrorActionPreference = "Stop"

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Installing dependencies..."
& $python -m pip install --quiet --upgrade pip
& $python -m pip install --quiet -r requirements.txt pyinstaller

Write-Host "Building executable..."
& $python -m PyInstaller --noconfirm --clean SentenceTool.spec

Write-Host ""
Write-Host "Done. Portable app: dist\SentenceTool.exe"
Write-Host "Run it, open Settings (gear icon), paste your OpenAI API key, then Start."
