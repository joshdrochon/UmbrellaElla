# One command for the whole jam loop, Claude Code or Codex (a human runs it, never an agent):
#   tools\kickoff.ps1                 no options: pipeline version, connection check, then start with the agent found
#   tools\kickoff.ps1 --agent codex   (or claude) to choose; --check for the check only
#   tools\kickoff.ps1 --max-cards 5   bounded run (KICKOFF_MAX_CARDS): stops once 5 cards merged or got blocked
#   tools\kickoff.ps1 --until G1      only the G1 path (KICKOFF_UNTIL); its package step runs on the Mac
# Windows twin of tools/kickoff.sh; the logic is in tools/kickoff.py (same arguments).
$kick = Join-Path $PSScriptRoot "kickoff.py"
if (-not (Test-Path $kick)) {
    Write-Host "kickoff: the pipeline is not installed here ($kick is missing). Fix: type 'git pull origin main' in the repo folder, then run tools\kickoff.ps1 again."
    exit 2
}
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
if (-not $py) {
    Write-Host "kickoff: Python 3.9 or newer is not installed. Install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then run tools\kickoff.ps1 again."
    exit 2
}
# Windows paths stop at 260 characters unless git is told otherwise; kickoff's worktrees
# (.pipeline\worktrees\<branch>\...) go deeper, and agent sessions run plain git in them.
$top = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null)
if ($top) { & git -C $top config core.longpaths true 2>$null | Out-Null }
& $py $kick @args
exit $LASTEXITCODE
