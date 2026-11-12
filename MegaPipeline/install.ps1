# Windows twin of MegaPipeline/install.sh (same options: --apply, --update, --update --apply).
#   powershell -File MegaPipeline\install.ps1 --update           # dry run: one line per change
#   powershell -File MegaPipeline\install.ps1 --update --apply   # replaces pipeline files, backs up what it replaces
$py = $null
foreach ($name in @("python3", "python", "py")) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if (-not $cmd) { continue }
    & $cmd.Source -c "import sys" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $py = $cmd.Source; break }
}
if (-not $py) {
    Write-Host "install: Python 3 is not installed. Install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then run this again."
    exit 2
}
& $py (Join-Path $PSScriptRoot "install.py") @args
exit $LASTEXITCODE
