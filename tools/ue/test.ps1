# Run UmbrellaElla automation tests headless on Windows, then check the report (not the exit code).
# -Filter <full test name> runs one test alone (gate isolation check in qa-build.md).
# Tests that write files write under Saved\UmbrellaEllaTests and delete them. Leftovers from a crashed run are
# removed before the run; any file left there after the run fails it. Save slots and GameUserSettings.ini
# are hashed before the run; any change after it fails (state-check).
param([int]$Baseline = 0, [string[]]$Require = @(), [string]$TestMap = "", [switch]$Bootstrap,
      [string]$MaxRuleSeconds = "", [string]$Filter = "UmbrellaElla")
. "$PSScriptRoot\common.ps1"
$Report = Join-Path $Repo "Saved\Automation"
$Log = Join-Path $LogDir "test-$Stamp.log"
if (Test-Path $Report) { Remove-Item -Recurse -Force $Report }
$Scratch = Join-Path $Repo "Saved\UmbrellaEllaTests"
if (Test-Path $Scratch) { $n = @(Get-ChildItem -Recurse -File $Scratch).Count; Write-Host "reset: removed $n leftover file(s) in $Scratch"; Remove-Item -Recurse -Force $Scratch }
$State = Join-Path $LogDir "test-$Stamp-$PID-state-before.txt"
& $Py @UERun state-list --out $State   # [VERIFY the editor itself leaves GameUserSettings.ini alone on 5.8.4]
& $Py @UERun run --timeout $UETimeout --log $Log -- `
  "$UERoot\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" $Project "-ExecCmds=Automation RunTests $Filter;Quit" `
  "-TestExit=Automation Test Queue Empty" "-ReportExportPath=$Report" -unattended -nopause -nosplash -NullRHI -nocrashreports -log | Out-Null
if ($LASTEXITCODE -eq 124) { Write-Host "FAIL: editor timed out after $UETimeout s; log: $Log"; exit 124 }
$args2 = @("$Report\index.json")
if ($Bootstrap) { $args2 += "--bootstrap" } else { $args2 += @("--baseline", "$Baseline") }   # card 0.3 only
if ($Require.Count -gt 0) { $args2 += "--require"; $args2 += $Require }
if ($MaxRuleSeconds) { $args2 += @("--max-rule-seconds", $MaxRuleSeconds) }
if ($TestMap) { $args2 += @("--test-map", $TestMap) }   # daily build: pipeline\qa\test-map.md
$WMap = Join-Path $Repo "pipeline\qa\test-map.md"
if (Test-Path $WMap) { $args2 += @("--world-map", $WMap) }   # (world) marks always count (final-10 A H4)
& $Py "$Repo\tools\check_automation_report.py" @args2
$rc = $LASTEXITCODE
if ((Test-Path $Scratch) -and @(Get-ChildItem -Recurse -File $Scratch).Count -gt 0) {
  Write-Host "FAIL: tests left file(s) in $Scratch (each test deletes what it writes)"; Get-ChildItem -Recurse -File $Scratch | Select-Object -First 20 | ForEach-Object { Write-Host "  $($_.FullName)" }; exit 1
}
& $Py @UERun state-check --before $State
if ($LASTEXITCODE -ne 0) { exit 1 }
exit $rc
