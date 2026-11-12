# Compile the editor target on Windows. -NonUnity runs the stricter non-merged build.
param([switch]$NonUnity)
. "$PSScriptRoot\common.ps1"
$Log = Join-Path $LogDir "build-$Stamp.log"
$Extra = @(); if ($NonUnity) { $Extra = @("-DisableUnity", "-NoPCH", "-NoSharedPCH") }
& $Py @UERun run --timeout $UETimeout --log $Log -- `
  "$UERoot\Engine\Build\BatchFiles\Build.bat" UmbrellaEllaEditor Win64 Development "-Project=$Project" -WaitMutex @Extra
$rc = $LASTEXITCODE
$warn = (Select-String -Path $Log -Pattern "warning C|: warning" -SimpleMatch:$false).Count
$Mode = if ($NonUnity) { "nonunity" } else { "unity" }
# One summary line; tools/check_pr.py reads exactly `build exit: <rc>  mode=<unity|nonunity>  commit=<sha>` (dry run A H3).
$Commit = (& git -C $Repo rev-parse HEAD 2>$null); if (-not $Commit) { $Commit = "unknown" }   # ties the line to the PR head (final-7 B H7)
Write-Host "build exit: $rc  mode=$Mode  commit=$Commit  warnings: $warn  log: $Log"
exit $rc
