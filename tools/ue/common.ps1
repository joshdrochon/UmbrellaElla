# Shared settings for the Windows scripts. Commands follow pipeline/unreal/commands-and-packaging.md; [VERIFY] on 5.8.4.
# Timeouts, dirty-tree refusal, BUILD_INFO.txt and smoke-log checks live in tools/ue_run.py (same for .sh).
# Continue: under Windows PowerShell 5.1, "Stop" turns any stderr line from UBT/UAT into a fatal error.
$ErrorActionPreference = "Continue"
$Repo = (Resolve-Path "$PSScriptRoot\..\..").Path
$Project = if ($env:PROJECT) { $env:PROJECT } else { Join-Path $Repo "UmbrellaElla.uproject" }
$UERoot = if ($env:UE_ROOT) { $env:UE_ROOT } else { "C:\Program Files\Epic Games\UE_5.8" }
$UETimeout = if ($env:UE_TIMEOUT) { $env:UE_TIMEOUT } else { "7200" }  # seconds; a hung run is killed (exit 124)
$Py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$UERun = @("$Repo\tools\ue_run.py", "--root", $Repo)
$LogDir = Join-Path $Repo "Saved\Logs\pipeline"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
if (-not (Test-Path $Project)) { Write-Host "No project at $Project (Day-0 skeleton card creates it)"; exit 2 }
if (-not (Test-Path (Join-Path $UERoot "Engine"))) { Write-Host "UE_ROOT not found: $UERoot. Set UE_ROOT to your 5.8.4 install."; exit 2 }
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
