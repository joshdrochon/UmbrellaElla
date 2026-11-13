# Asset and data validation on Windows: runs the DataValidation commandlet on the project, fails on any error,
# and prints `validate: errors=N warnings=M` for the daily record. [VERIFY -run=DataValidation and its
# log lines on 5.8.4; the DataValidation plugin must be enabled, Technical Director's call]
. "$PSScriptRoot\common.ps1"
$Log = Join-Path $LogDir "validate-$Stamp-$PID.log"
& $Py @UERun run --timeout $UETimeout --log $Log -- `
  "$UERoot\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" $Project -run=DataValidation -unattended -nopause -nosplash -NullRHI -nosound -nocrashreports -log | Out-Null
$rc = $LASTEXITCODE
if ($rc -eq 124) { Write-Host "FAIL: validation timed out after $UETimeout s; log: $Log"; exit 124 }
$err = @(Select-String -Path $Log -Pattern "\bError:").Count
$warn = @(Select-String -Path $Log -Pattern "\bWarning:").Count
Write-Host "validate: errors=$err warnings=$warn  log: $Log  exit: $rc"
if ($rc -ne 0 -or $err -ne 0) { Write-Host "FAIL: data validation"; exit 1 }
exit 0
