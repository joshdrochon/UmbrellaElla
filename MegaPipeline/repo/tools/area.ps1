# Resume one area of the build from its branch, on your own machine (a human runs it, never an agent):
#   tools\area.ps1                  HANDOFF.md and every area's branch
#   tools\area.ps1 <name>           check out area/<name>, merge main in, guard the lane, start your agent with the brief
#   tools\area.ps1 <name> --done    merge main in, check the lane, merge the area into main, print the push command
# Options: --agent claude|codex|none, --prompt. Windows twin of tools/area.sh; the logic is in tools/area.py.
$area = Join-Path $PSScriptRoot "area.py"
if (-not (Test-Path $area)) {
    Write-Host "area: tools\area.py is missing here. Fix: type 'git pull origin main' in the repo folder, then run tools\area.ps1 again."
    exit 2
}
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
    Write-Host "area: Python 3.9 or newer is not installed. Install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then run tools\area.ps1 again."
    exit 2
}
# Unreal content paths run deep; Windows git stops at 260 characters unless told otherwise.
$top = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null)
if ($top) { & git -C $top config core.longpaths true 2>$null | Out-Null }
& $py $area @args
exit $LASTEXITCODE
