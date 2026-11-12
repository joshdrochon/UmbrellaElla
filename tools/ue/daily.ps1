# The daily integration build as one graph (Windows): clean-tree, build (non-unity: -DisableUnity -NoPCH -NoSharedPCH,
# same as build.ps1 -NonUnity), test, alone, validate, package,
# smoke every map, display runs, client-test, shipping-alive, then the tester package (workbench) (steps: tools\ue\daily-checklist.md). Stops at the first failing step, so a commit whose tests failed is never
# packaged or smoked. Prints one record line and appends it to Saved\Logs\pipeline\daily-records.txt.
# Usage: tools\ue\daily.ps1 [-AllowDirty]. Env as daily.sh. Steps and record format: tools\ue_run.py `daily`.
param([switch]$AllowDirty)
. "$PSScriptRoot\common.ps1"
$Allow = @(); if ($AllowDirty -or $env:ALLOW_DIRTY -eq "1") { $Allow = @("--allow-dirty") }
& $Py @UERun daily --shell ps1 @Allow
exit $LASTEXITCODE
