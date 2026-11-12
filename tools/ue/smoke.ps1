# Smoke a packaged build: run it with -SmokeQuitAfter=15, then check exit code, SMOKE_OK, fps and the
# SMOKE_BAD log patterns in tools\ue_run.py (any > 0 fails), and fail on any new Saved\Crashes folder.
# Usage: tools\ue\smoke.ps1 -Exe <packaged game .exe> [-Res 1280x720 -Window windowed|fullscreen] [-Alive]
# Env as smoke.sh: SMOKE_TIMEOUT, SMOKE_MAP, SMOKE_GAME_MAP, SMOKE_MIN_FPS (55), SMOKE_RES, SMOKE_WINDOW,
# SMOKE_MIN_TEXT_PX (18), SMOKE_MAX_FRAME_MS (33), SMOKE_MAX_LOAD_MS (10000), SMOKE_REQUIRE_INPUT (1), SMOKE_REQUIRE_GAMEPAD (1), SMOKE_SECTION, SMOKE_RESTART_CYCLES,
# SMOKE_NO_PLAYER_MAPS (default: pipeline\qa\no-player-maps.txt), SMOKE_ALIVE_SECONDS (15), SMOKE_CRASH_DIRS (;-separated), SMOKE_MODE=alive. -Alive = no-log run (alive at 15 s,
# closed by WM_CLOSE, exit 0); use it on Shipping only if D-new-smoke picks a Shipping smoke.
# SMOKE_MAX_BOOT_S (alive: first window within N s, 0 = off), SMOKE_FORCE_CRASH=1 (passes -SmokeCrash; card 0.6).
# Every run passes -SmokeShot=<png>: smoke-log runs art_check.py and screen_check.py on that default-build screenshot
# (either FAIL fails the smoke) and checks view=/aspect= (16:9) and debugdraw=0. SMOKE_FORCE_NO_ASPECT=1 passes
# -SmokeNoAspectLock, SMOKE_FORCE_DEBUGDRAW=1 passes -SmokeDebugDraw: proof runs that must FAIL (card 0.6).
# SMOKE_ZIP=<gate zip> (the exe is from that zip, unzipped: a passing run appends its LAUNCH record line). The game's
# SMOKE_EFFECTIVE line is checked by tools\bake_preset.py effective against baked.json and the manifest (final-9 B C1).
param([Parameter(Mandatory = $true)][string]$Exe, [string]$Res = $env:SMOKE_RES, [string]$Window = $env:SMOKE_WINDOW,
      [switch]$Alive)
$ErrorActionPreference = "Continue"
$Repo = (Resolve-Path "$PSScriptRoot\..\..").Path
$Py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$UERunPy = "$Repo\tools\ue_run.py"
$Timeout = if ($env:SMOKE_TIMEOUT) { $env:SMOKE_TIMEOUT } else { "120" }
$MinFps = if ($env:SMOKE_MIN_FPS) { $env:SMOKE_MIN_FPS } else { "55" }
$MinText = if ($env:SMOKE_MIN_TEXT_PX) { $env:SMOKE_MIN_TEXT_PX } else { "18" }
$MaxMs = if ($env:SMOKE_MAX_FRAME_MS) { $env:SMOKE_MAX_FRAME_MS } else { "33" }
$MaxLoad = if ($env:SMOKE_MAX_LOAD_MS) { $env:SMOKE_MAX_LOAD_MS } else { "10000" }
if (-not (Test-Path $Exe)) { Write-Host "usage: smoke.ps1 -Exe <packaged game executable>"; exit 2 }
$LogDir = Join-Path $Repo "Saved\Logs\pipeline"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$GameLog = Join-Path $LogDir ("smoke-game-" + (Get-Date -Format "yyyyMMdd-HHmmss") + "-$PID.log")
$OutLog = $GameLog -replace '\.log$', '-stdout.log'
$Info = Split-Path -Parent $Exe
for ($i = 0; $i -lt 5 -and -not (Test-Path (Join-Path $Info "BUILD_INFO.txt")); $i++) { $Info = Split-Path -Parent $Info }
if (-not (Test-Path (Join-Path $Info "BUILD_INFO.txt"))) { $Info = Split-Path -Parent $Exe }
$InfoFile = Join-Path $Info "BUILD_INFO.txt"
$Crash = @($Info, "$env:LOCALAPPDATA\UmbrellaElla\Saved")   # [VERIFY crash folder on 5.8.4]
if ($env:SMOKE_CRASH_DIRS) { $Crash += $env:SMOKE_CRASH_DIRS -split ';' }
$Snap = $GameLog -replace '\.log$', '-crashes-before.txt'
& $Py $UERunPy crash-list @Crash --out $Snap
$Shot = $GameLog -replace '\.log$', '-shot.png'
$GameArgs = @("-SmokeShot=$Shot"); $Expect = @("--min-fps", $MinFps, "--max-frame-ms", $MaxMs, "--max-load-ms", $MaxLoad, "--shot", $Shot)
if ($env:SMOKE_NO_PLAYER_MAPS) { $Expect += @("--no-player-maps", $env:SMOKE_NO_PLAYER_MAPS) }
if ($env:SMOKE_REQUIRE_INPUT -eq "0") { $Expect += "--no-input-check" }
if ($env:SMOKE_REQUIRE_GAMEPAD -eq "0") { $Expect += "--no-gamepad-check" }
if ($env:SMOKE_GAME_MAP) { $GameArgs += "-SmokeMap=$($env:SMOKE_GAME_MAP)" }
if ($env:SMOKE_FORCE_CRASH -eq "1") { $GameArgs += "-SmokeCrash" }   # [VERIFY -SmokeCrash in the card 0.6 hook]
if ($env:SMOKE_FORCE_NO_ASPECT -eq "1") { $GameArgs += "-SmokeNoAspectLock" }
if ($env:SMOKE_FORCE_DEBUGDRAW -eq "1") { $GameArgs += "-SmokeDebugDraw" }
if ($env:SMOKE_SECTION) { $GameArgs += "-SmokeSection=$($env:SMOKE_SECTION)"; $Expect += @("--expect-section", $env:SMOKE_SECTION) }
if ($env:SMOKE_RESTART_CYCLES -and $env:SMOKE_RESTART_CYCLES -ne "0") {
  $GameArgs += "-SmokeRestartCycles=$($env:SMOKE_RESTART_CYCLES)"; $Expect += @("--restart-cycles", $env:SMOKE_RESTART_CYCLES)   # [VERIFY]
}
if ($env:SMOKE_EXPECT_RES -and -not $Res) { $Expect += @("--expect-res", $env:SMOKE_EXPECT_RES) }   # 1080p fallback check
if ($Res) {
  if (-not $Window) { $Window = "windowed" }
  $X, $Y = $Res -split 'x'
  $GameArgs += @("-ResX=$X", "-ResY=$Y", "-$Window")   # [VERIFY -ResX/-ResY/-windowed/-fullscreen]
  $Expect += @("--expect-res", $Res, "--expect-win", $Window, "--min-text-px", $MinText)
}
if ($Alive -or $env:SMOKE_MODE -eq "alive") {
  $AliveS = if ($env:SMOKE_ALIVE_SECONDS) { $env:SMOKE_ALIVE_SECONDS } else { "15" }
  $BootS = if ($env:SMOKE_MAX_BOOT_S) { $env:SMOKE_MAX_BOOT_S } else { "0" }
  & $Py $UERunPy alive --seconds $AliveS --max-boot-s $BootS --log $OutLog -- $Exe -unattended @GameArgs
  $rc = $LASTEXITCODE
} else {
  & $Py $UERunPy run --timeout $Timeout --log $OutLog -- `
    $Exe -SmokeQuitAfter=15 -log "-abslog=$GameLog" -unattended @GameArgs | Out-Null   # -abslog [VERIFY]
  $run = $LASTEXITCODE
  $Logs = @($OutLog); if (Test-Path $GameLog) { $Logs += $GameLog }
  Write-Host "smoke logs: $($Logs -join ' ')"
  if (Test-Path $InfoFile) { $c = (Select-String -Path $InfoFile -Pattern '^commit=(.+)$').Matches[0].Groups[1].Value; $Expect += @("--expect-commit", $c) }
  if ($env:SMOKE_MAP) { $Expect += @("--expect-map", $env:SMOKE_MAP) }
  if (Test-Path $InfoFile) { $w = Select-String -Path $InfoFile -Pattern '^workbench=(.+)$'; if ($w) { $Expect += @("--expect-workbench", $w.Matches[0].Groups[1].Value) } }   # D-new-workbench-debug
  & $Py $UERunPy --root $Repo smoke-log @Logs --exit-code $run @Expect
  $rc = $LASTEXITCODE
  & $Py "$Repo\tools\bake_preset.py" --root $Repo effective @Logs
  if ($LASTEXITCODE -ne 0) { $rc = 1 }
}
& $Py $UERunPy crash-check --before $Snap @Crash
$cr = $LASTEXITCODE
if ($rc -ne 0 -or $cr -ne 0) { exit 1 }
if ($env:SMOKE_ZIP -and -not ($Alive -or $env:SMOKE_MODE -eq "alive")) {
  & $Py $UERunPy --root $Repo launch-record --zip $env:SMOKE_ZIP --exe $Exe @Logs
  if ($LASTEXITCODE -ne 0) { exit 1 }
}
exit 0
