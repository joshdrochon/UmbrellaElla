# HANDOFF: <game> build (read this to pick up the build)

Copy this file to `HANDOFF.md` on `main`. The build lead updates it with every merge; `tools/kickoff.sh` in direct mode
(`docs/build/MODE`) reads it and writes each area's result back into its row.

Updated: <date> by <who>. Mode: `direct` (no GitHub cards, PRs or reviews; see README "Build modes").

## Area branches
| Area | Branch | Who has it | Status | Next step |
|---|---|---|---|---|
| move: <what it builds> | `area/move` | free | in progress | <the next slice> |
| arena: <what it builds> | `area/arena` | <name> | in progress | <the next slice> |
Rules kickoff follows: an area whose Status starts with `done` is skipped (a worker marks it by writing `AREA DONE` in
its status file), and so is one held by a person (Who has it is not `free`, `-` or empty); every other area, `merged`
ones included, is resumed from its branch. One person per area at a time.

## Area briefs
One `docs/build/areas/<name>.md` per area: what to build, done criteria, and a lane section kickoff and
`tools/area.sh` read (backticked paths; `{Public,Private}`, `**` and `except` work; later items in a bullet may be
relative to its first path):

    ## File lane (only these)
    - `Source/<Module>/{Public,Private}/Owl/**`, `Encounter/**`
    - `Content/<Game>/Keeper/**`, `docs/build/areas/<name>-status.md`, `docs/build/requests/<name>.md`

Files in no lane (Config/*.ini, the .uproject, *.Build.cs, Core contracts, this file) change on `main` only; an area
asks for them in `docs/build/requests/<name>.md`. Lanes must not overlap: two areas never own one file.

## Gates each merge into main must pass
Default (`tools/direct_build.py`): `tools/ue/build.sh` (`build exit: 0`), `tools/ue/test.sh` (`PASS`),
`module_check`, `manifest_check`, `feel_check`, `encounter_check` (`0 problem`), and `tools/build/visual_qa.py` on
merges touching Source/, Content/, Art/ or pipeline/art. No handoff tag without a passing `visual_qa.py` run on that commit. Other gates: one command per line in
`docs/build/gates.txt` (`mac:` / `win:` prefix, `{py}`, `command => text the output must contain`).

## Continue
    git pull
    tools/kickoff.sh            # Windows: tools\kickoff.ps1   (all unfinished areas, as many at once as fit)
    tools/area.sh <name>        # Windows: tools\area.ps1 <name>   (one area, interactive, your own agent)

## Follow-up list
- <decisions and minor review findings>
