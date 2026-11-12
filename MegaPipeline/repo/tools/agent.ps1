# Start any agent CLI on a card, journaled (AGENTS.md section 1). Windows twin of tools/agent.sh.
#   tools\agent.ps1 <role> <card> <agent-cli> [args...]     e.g. tools\agent.ps1 gameplay-dev UE-12 claude
# Sets JAM_ROLE (a key of "roles" in pipeline/agent-ops/gates.json) and JAM_CARD, runs journal.py start and
# resume, runs the CLI, then writes a checkpoint that carries the next step forward and logs the session's tokens
# and cost (tools/spend_log.py; never changes the exit code). Exits with the CLI's code.
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Role,
    [Parameter(Mandatory = $true, Position = 1)][string]$Card,
    [Parameter(Mandatory = $true, Position = 2, ValueFromRemainingArguments = $true)][string[]]$Cli
)
$root = Split-Path -Parent $PSScriptRoot
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
if (-not $py) { Write-Error "agent.ps1: no Python 3.9 or newer (python.org; tick 'Add python.exe to PATH')"; exit 2 }
$roles = (Get-Content -Raw (Join-Path $root "pipeline/agent-ops/gates.json") | ConvertFrom-Json).roles
if (-not ($roles.PSObject.Properties.Name -contains $Role)) {
    Write-Error "agent.ps1: unknown role '$Role'; use a key of roles in pipeline/agent-ops/gates.json"
    exit 2
}
$env:JAM_ROLE = $Role
$env:JAM_CARD = $Card
if (-not $env:JAM_HOST) {
    $env:JAM_HOST = & $py -c "import hashlib,socket; print('host-' + hashlib.sha256(socket.gethostname().encode()).hexdigest()[:6])"
}
$journal = Join-Path $root "tools/journal.py"
& $py $journal start --role $Role --card $Card
if ($LASTEXITCODE -ne 0) { exit 2 }
& $py $journal resume --card $Card
$started = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss")
$exe = $Cli[0]
$rest = @()
if ($Cli.Count -gt 1) { $rest = $Cli[1..($Cli.Count - 1)] }
& $exe @rest
$code = $LASTEXITCODE
& $py $journal checkpoint --card $Card --note "agent CLI '$exe' exited $code (tools/agent.ps1)" | Out-Null
$model = if ($env:JAM_MODEL) { $env:JAM_MODEL } else { "unknown" }
& $py (Join-Path $root "tools/spend_log.py") log --from-agent-log --since $started --role $Role --card $Card --model $model
exit $code
