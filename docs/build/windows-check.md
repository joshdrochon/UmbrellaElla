# Windows check (teammate on a Windows PC)

The submission is a Windows Development package, and this Mac cannot build one. After each gate milestone (G1, G2,
G3, G4) or when the build lead asks, a teammate with Windows and UE 5.8.4 runs this and reports back.

## Steps (PowerShell, in your clone)
    git checkout main
    git pull
    git lfs pull
    tools\ue\build.ps1                         # must end: build exit: 0
    tools\ue\test.ps1                          # must end: PASS tests=<n> failed=0
    tools\ue\package.ps1                       # Development, submission target (workbench compiled out)
    tools\ue\smoke.ps1 <path to Packaged\Windows\UmbrellaElla.exe>
Then play it for two minutes with a gamepad: Start Game, fight the Keeper, pause (Continue, Settings, Quit), lose once
and retry, and if you can, win.

## Report back (paste into the team channel or docs/build/windows-reports.md on a branch)
- `git rev-parse --short HEAD` (the commit you built)
- the last line of build.ps1, test.ps1 and package.ps1
- the SMOKE_OK line from smoke.ps1 (with `input=ok gamepad=ok`, view/aspect and fps), or the first error
- anything that looked or played wrong: what you did, what you expected, what happened
- the zip path if package.ps1 made one (do not upload it yet; the packaging owner submits)

If a step fails: stop, paste its last 20 lines, and do not try to fix the code on main. The build lead routes it.

## HAZ-16 at 1920x1080 (D-new-haz16-agent-playtest)
This Mac clamps the viewport to 1728x1117 even offscreen, so the HAZ-16 agent play-test at 1920x1080 runs here, on Windows:
`python3 tools/build/agent_play.py --rule HAZ-16 --res 1920x1080` (debug off, healthy and low health). Attach the run log to the report.
