<!-- tools/check_pr.py fails this PR if a required section is empty. -->
## Task
Part of #<issue>. Card ID: UE-___  Owner role: ___  Reviewer role: ___
<!-- Link form is open decision D-new-port-1. Default: "Part of #<issue>" (the human on the card closes it after the
     packaged-build check). Alternative: "Closes #<issue>" (merge closes the card). tools/check_pr.py accepts both. -->

## What changed
<files and assets, one line each>

## Done-when checks
<copy the card's Done-when list; tick only what you ran and observed>
- [ ]

## Evidence
commit=<sha> engine=5.8.4 config=<Development|Shipping|none> host=<win|mac> run=<PIE|Standalone|packaged|none>
<build log tail, test output, screenshot or clip paths. "Not run" is allowed if you say why.
Changes maps, Config/**, *.Build.cs, *.Target.cs or .uproject: the package script's `package exit: 0  commit=<sha>  dirty=no ...`
line and the smoke output (tools/ue/smoke.sh / smoke.ps1 print the game's SMOKE_OK log line as is; paste the whole output).
Touches Source/: the `build exit: 0  mode=nonunity  commit=<sha> ...` line as printed (NONUNITY=1 tools/ue/build.sh, build.ps1 -NonUnity)
and the check_automation_report.py result line (PASS  tests=N failed=0  commit=<sha>). Every commit= is the header commit:
after a new push, run them again. A claim like "all good" fails check_pr.
A failure the card's Done-when asks for on purpose (MustFail, a planted plant, SMOKE_FORCE_CRASH) goes under a line
`PLANTED FAIL: <what>`, up to the next blank line; any other FAIL line fails check_pr.
A changed .uasset/.umap needs the card's human to open it: `EDITOR CHECK: by=<name> opened=<path>[,<path>] ok`.
Last line: developer-tested (PIE), developer-tested (packaged) or QA-verified in build <sha> (qa-build.md).>

## Not done / risks
<one line each, each with a link (issue #N, decision row, or URL). Write "none" only if true.>
Could not read: <card Inputs or cited docs you could not open (missing, LFS pointer, no access), or "none". Build nothing that rests only on one>
Next: <next role and exact step after this PR, or "none">

## Binary assets touched
<.uasset/.umap paths and whether you held the LFS lock. "none" if none.>

## GDD impact
<only if this PR changes docs/gdd/ or docs/feature-manifest.json: paste `python3 tools/gdd_impact.py <old> <new>`
(docs/gdd/README.md). Otherwise delete this section.>

## Journal
<paste the output of `python3 tools/journal.py export --card UE-___` (AGENTS.md section 6)>
