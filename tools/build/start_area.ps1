# Start (or continue) one area worker on Windows with Claude Code, in that area's worktree.
# Usage: powershell -File tools\build\start_area.ps1 -Area move [-Extra "..."]
param([Parameter(Mandatory=$true)][ValidateSet("move","keeper","health","flow","arena","enemies","progression","story")][string]$Area, [string]$Extra = "")
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
$Base = Join-Path (Split-Path $Root -Parent) "UmbrellaElla-areas"
$Wt = Join-Path $Base $Area
New-Item -ItemType Directory -Force -Path (Join-Path $Base "logs") | Out-Null
if (-not (Test-Path $Wt)) {
  git -C $Root fetch -q origin
  git -C $Root rev-parse -q --verify "refs/remotes/origin/area/$Area" *> $null
  if ($LASTEXITCODE -eq 0) { git -C $Root worktree add $Wt -B "area/$Area" "origin/area/$Area" }
  else { git -C $Root worktree add $Wt -b "area/$Area" main }
}
$Prompt = @"
You are the '$Area' area worker for Umbrella Ella (UE 5.8.4), on Windows. Your worktree is $Wt on branch area/$Area.
Read docs/build/worker-rules.md, then docs/build/areas/$Area.md, and docs/build/areas/$Area-status.md if it exists.
Use tools\ue\build.ps1 and tools\ue\test.ps1 (no slot lock on Windows). Build your area to its definition of done:
G1 Rule IDs first, then the later list. Commit after each working slice (git -c core.hooksPath=NUL commit).
Push your branch after each commit: git push origin area/$Area. Never touch main or another lane. $Extra
"@
Set-Location $Wt
claude -p $Prompt --permission-mode bypassPermissions --model claude-opus-5-5 *>> (Join-Path $Base "logs\$Area.log")
