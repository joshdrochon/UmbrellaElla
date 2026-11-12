# One-command launcher: a fresh agent session for one role on one card. A human runs it, never an agent.
#   tools\start_session.ps1 <role> <card> [--dry-run] [extra claude args...]   e.g. tools\start_session.ps1 gameplay-dev UE-12
# Windows twin of tools/start_session.sh; the logic is in tools/start_session.py.
# Python before 3.15 writes piped output (an agent's tool calls) in the ANSI code page, so a tool printing a doc's
# arrow or dash crashes; UTF-8 mode reaches every python this session starts.
if (-not $env:PYTHONUTF8) { $env:PYTHONUTF8 = "1" }
# The Windows Store puts a fake python3 on PATH that only opens the Store: try each name and keep the one that runs.
$py = $null
foreach ($name in @("python3", "python", "py")) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if (-not $cmd) { continue }
    & $cmd.Source -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $py = $cmd.Source; break }
}
if (-not $py) { Write-Error "start_session.ps1: no Python 3.9 or newer (python.org; tick 'Add python.exe to PATH')"; exit 2 }
& $py (Join-Path $PSScriptRoot "start_session.py") @args
exit $LASTEXITCODE
