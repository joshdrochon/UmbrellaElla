# Task card template

One card = one GitHub issue = one branch = one PR. File it with the "Task card" issue form; this template
is the reference for what each field means. A card with an empty field is not ready.

```
ID:            UE-000
Title:         <verb + thing, e.g. "Umbrella open/close changes vertical velocity">
MVP item:      <number from docs/jam-brief.md, or "Stretch: <name>">
GDD ref:       <section + quote, ≤20 words, from the current GDD snapshot (docs/gdd/CURRENT names it); "none" for tooling cards>
               <tag: GDD RULE | DEFAULT (Dn) | HYPOTHESIS (Pn) | ILLUSTRATIVE; see pipeline/checklists/design-review.md>
GDD revision:  <the revision the card was written against, e.g. 1.3 (docs/gdd/CURRENT)>
Features:      <feature IDs from docs/feature-manifest.json, e.g. UMB-03; each must be implementation_authorized.
               "UMB-03 Hook only" = interface + flag at its manifest default, no behavior (OPEN or PROPOSED IDs only).
               "none" for tooling cards>
Player outcome: <"the player sees X, does Y, can tell why"; "none" for tooling cards>
Owner role:    <Gameplay Dev | Asset Specialist | Art Director | ...>
Reviewer role: <must differ from owner>
Human:         <teammate kickoff asks when the card is stuck>

Inputs:        <files/assets/specs that must already exist, with paths>
Context:       <what the code or asset next to Outputs does today, 1-2 lines with file:line; "new files only" if nothing exists yet>
Outputs:       <exact paths this card creates or changes>
File lane:     <glob this card may write, e.g. Source/UmbrellaElla/{Public,Private}/Movement/**, Content/UmbrellaElla/Art/Ella/**;
               "GitHub only" if it writes no files. Never "none" or "everything">
Do not touch:  <paths owned by other lanes; always includes Content/UmbrellaElla/Maps/** unless this is an integration card>
Out of scope:  <behaviors not to build, e.g. "no new animation states, no stretch mechanics"; the reviewer rejects them>
Used by:       <BPs, maps, widgets or components that read what this card changes, with the follow-up card (#<n> or UE-<n>);
               "none" if nothing outside this lane reads it>
Needs:         <build | tests | editor MCP | Windows packaging machine>; the agent states what it can run (AGENTS.md §1)
Binary locks:  <.uasset/.umap files to `git lfs lock` before editing; "none" if none>

Done when:     <each line checkable: a number with a unit, a test name, or a command with its result on the same line
               ("`tools/ue/smoke.sh` prints PASS"). "exits 0" without the command, or "eventually", fails check_card>
  - [ ] tools/ue/build.sh (or tools\ue\build.ps1) exits 0 and the log is attached
  - [ ] <automation test name> passes
  - [ ] <negative or blocked case test, e.g. owl outside the firing lane → no shot>
  - [ ] <PIE or packaged-build observation with screenshot/clip path>
  - [ ] package + SMOKE_OK (required if the card touches maps, Config/**, Build.cs, Target.cs, .uproject or path-loaded assets)
Evidence:      <where the logs/screenshots go: the PR body>

Budget:        <n> min agent + <n> min human, e.g. "90 min agent + 20 min human". Agent over 120 min or human over 60 min: split the card.
               The clock starts at the `doing` label. 60 min over: see AGENTS.md §6 (D-new-overrun)
Stop if:       2 failed attempts with the same error → set blocked, write the diagnosis, stop
Cut tier:      MVP | Stretch-1 | Stretch-2 | ...
Unknowns:      <Decision needed / Why it matters / Proposed test / Choice: test now, accept risk, or postpone>
```

Feature IDs and statuses: `docs/feature-manifest.json` (checked by `tools/manifest_check.py`). `check_card.py` fails a card
whose features are not authorized, and a card on an older GDD revision whose features changed since (`tools/gdd_impact.py`).

After (optional, below Used by; the form's After field): the cards that must merge first, `#<n>` or `UE-<n>`. `check_card.py --blocked-by` reads it.

Asset cards add the brief in `pipeline/templates/asset-brief.md`. Spikes use `pipeline/templates/spike-card.md`.
Readiness is checked with `pipeline/checklists/card-ready.md`.

States: `todo → doing → review → done`, plus `blocked`. Only the human named on the card
moves a card to `done`, and only after the reviewer role approved and the evidence is in the PR.

Session end without a PR: post the handoff comment from AGENTS.md §6 on this card.
A card closed without being done carries the label `cut` or `superseded` and a one-line reason.
