# Package Win64 (only possible on Windows). The submission is this Development package (D25); -Shipping is optional.
# Refuses a dirty git tree unless -AllowDirty (or ALLOW_DIRTY=1). build-info writes BUILD_INFO.txt into the package
# and copies pipeline/submission/README.txt and LICENSE.txt next to the exe.
# Default: the submission target UmbrellaElla, workbench compiled out (D-new-workbench-debug); workbench-check must pass.
# -Workbench (or WORKBENCH=1): the tester target UmbrellaEllaWorkbench, never submitted (BuildCookRun -target= [VERIFY on 5.8.4]). Not with -Shipping.
param([switch]$Shipping, [switch]$AllowDirty, [switch]$Workbench)
. "$PSScriptRoot\common.ps1"
$Allow = @(); if ($AllowDirty -or $env:ALLOW_DIRTY -eq "1") { $Allow = @("--allow-dirty") }
$WB = if ($Workbench -or $env:WORKBENCH -eq "1") { "1" } else { "0" }
if ($WB -eq "1" -and $Shipping) { Write-Host "FAIL: -Workbench with -Shipping; the workbench is dev-only"; exit 2 }
& $Py @UERun clean-tree @Allow
if ($LASTEXITCODE -ne 0) { exit 1 }
# The commit is stamped at build start and compiled in (UmbrellaElla.Target.cs reads UMBRELLAELLA_BUILD_COMMIT into the
# game, which logs it in SMOKE_EFFECTIVE); BUILD_INFO gets the same value, never HEAD after the build (final-9 B H5).
$Commit = (& git -C $Repo rev-parse HEAD 2>$null); if (-not $Commit) { $Commit = "unknown" }
$Dirty = if (& git -C $Repo status --porcelain 2>$null) { "yes" } else { "no" }
$env:UMBRELLAELLA_BUILD_COMMIT = $Commit
$Target = "UmbrellaElla"
if ($WB -eq "1") { $Target = "UmbrellaEllaWorkbench" } else { & $Py @UERun workbench-check; if ($LASTEXITCODE -ne 0) { exit 1 } }
$Cfg = "Development"; $Extra = @()
if ($Shipping) { $Cfg = "Shipping"; $Extra = @("-nodebuginfo") }
$Log = Join-Path $LogDir "package-$Stamp-$PID.log"   # one log per run: the error and warning counts read it
# The tester package goes to its own folder, and each run starts from an empty one, so BUILD_INFO and the exe always
# belong to this run and a zip never holds two targets (final-7 dry run A M7).
$Out = if ($WB -eq "1") { Join-Path $Repo "Packaged-Workbench" } else { Join-Path $Repo "Packaged" }
if (Test-Path $Out) { Remove-Item -Recurse -Force $Out }
& $Py @UERun run --timeout $UETimeout --log $Log -- `
  "$UERoot\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun "-project=$Project" "-target=$Target" -noP4 -platform=Win64 `
  "-clientconfig=$Cfg" -build -cook -stage -pak -iostore -prereqs -archive "-archivedirectory=$Out" `
  -unattended -utf8output @Extra
$rc = $LASTEXITCODE
if (Select-String -Path $Log -Pattern "^Error:|LogCook: Error" -Quiet) { Write-Host "FAIL: errors in cook log $Log"; exit 1 }
$CookWarn = @(Select-String -Path $Log -Pattern "^Warning:|LogCook: Warning").Count
Write-Host "cook warnings: $CookWarn"   # daily fails if it rises [VERIFY pattern on 5.8.4]
$Now = (& git -C $Repo rev-parse HEAD 2>$null); if (-not $Now) { $Now = "unknown" }
if ($Now -ne $Commit) { Write-Host "FAIL: HEAD moved from $Commit to $Now during packaging; the binary is $Commit's. Package again."; $rc = 1 }
if ($Dirty -eq "no" -and (& git -C $Repo status --porcelain 2>$null)) { Write-Host "FAIL: the tree changed during packaging. Package again."; $rc = 1 }
if ($rc -eq 0) { & $Py @UERun build-info --out $Out --config $Cfg --target $Target --workbench $WB --commit $Commit; $rc = $LASTEXITCODE }
# One summary line; tools/check_pr.py reads exactly `package exit: <rc>  commit=<sha>  dirty=<yes|no>` (final-7 B H7, M8)
# and platform= (a card that asks for package.ps1 needs platform=Win64; final-9 A H5).
Write-Host "package exit: $rc  commit=$Commit  dirty=$Dirty  target=$Target  platform=Win64  log: $Log"
exit $rc
