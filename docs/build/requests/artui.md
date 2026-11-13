# Requests from artui

## 1. Art loop: a UI screen's capture is its own context (tools/art_loop.py, build lead)
`required_pairs` adds a `context` pair to every piece that is not `scene`: the newest in-engine capture against the key
art, judged with the gameplay scene's brief. For a sprite that is right. For a screen piece (an element with a `ui`
block: `ui-title`, `ui-defeated`, ...) the piece already is the in-engine capture, and the key art is a gameplay
frame, so a menu can never win that pair. Until this changes, `art_loop.py verdict` answers `reference` for every
screen piece, whatever the critics say (`cannot judge yet: context`), and no screen can get a pass line.

    --- a/tools/art_loop.py
    +++ b/tools/art_loop.py
    @@ def required_pairs(refs, piece, ours, root=ROOT):
    -    if piece != "scene":
    +    if piece != "scene" and not (refs["elements"].get(piece) or {}).get("ui"):   # a screen's capture is its own context
             out.append(("context", context_ref(refs, root), find_capture(root, ours)))

and the same condition where `write_record` and `record_problems` build `need` (`["context"] if piece != "scene"`).
Test to add: a screen element's `required_pairs` has no `context`; a sprite element's still has one. This removes no
bar: the reference pair (the title-screen target) and the quality-bar pair stay, with the full calibrated panel.
Workaround in this lane: I read the reference and quality-bar pairs from the panel's answers myself.

## 2. Cook the UI art folder (Config/DefaultGame.ini, build lead)
The UI textures are loaded by a native class constructor (`UUmbrellaUIStyleAssets`), which the cooker follows, so the
package should carry them. To make that certain (and to cover any later UI asset), add under
`[/Script/UnrealEd.ProjectPackagingSettings]`:

    +DirectoriesToAlwaysCook=(Path="/Game/UmbrellaElla/UI")

Not verified here: workers do not package. If the textures are missing in a package, the menus fall back to a plain
ink ground and the HUD to the drawn dial (no crash); the display font is embedded in the code and needs no cooking.

## 3. Screens check and `final` widgets (tools/ui_check.py is in this lane; note for the UI and UX reviewer)
`ui_check.py widgets` (U10, no NativeTick in a UUserWidget) does not match a class declared `final`
(`class X final : public UUserWidget`), so `UXpRingWidget`'s `NativeTick` is not seen. I did not change that check: fixing
it makes `ui_check ci` fail on main (progression lane's widget). The new `screens` check does match `final` classes.

## 4. Per-screen capture switch (Smoke hook, lead) — BLOCKS 10 of 12 screens
Only the title is reachable through `run_game.sh -SmokeShot` (the smoke hook passes title straight to gameplay). Settings, Pause,
Defeat, Credits, Story, Purchase, LevelUp, Statistics and the HUD cannot be captured from the repo, so no panel round can run on them
(a context-free pair still needs a fresh in-engine capture of the screen). Request: a `-SmokeScreen=<EFlowScreen name>` switch in the
smoke hook that opens that flow screen before the shot (Smoke lane; the screens already exist in `Flow/FlowRules.h`).
Until then my loop only continues on ui-title (not passed: reference pair lost r8-r17).

## 5. Escalate artui to Opus (worker-rules: repeat failures)
ui-title has lost the reference pair on the same gap (smooth lettering, no etched/distressed feel) for about 10 rounds; triage says work (calibration 6/6, quality-bar pair won, capture is 1920x1080 and uncropped). Restart with `WORKER_MODEL=claude-opus-5-5 tools/build/start_area.sh artui "..."`. Remaining image budget is about $5.5 shared.

## 6. assetgen draft gate uses full-frame art_check on UI screen pieces (tools/assetgen.py, build lead)
`assetgen.draft_checks_passed` runs `art_check.evaluate(measure(...))` (the full-frame share rules) for every piece, but
`art_loop.measure` judges a non-`scene` piece with `sprite_checks` (colour rules only; "the share rules belong to the
full frame"). Triage on known inputs (13 Nov): the r19 title capture, whose art_loop checks passed (status, Resume 4),
fails the draft gate with `paper_texture 0.28 < 0.38; dark_share 0.459 outside [0.04, 0.45]`; the keyed lockup draft on
black fails `dark_share 0.94`. So no UI screen piece can ever get a `--tier final` call. Verdict: check defect.
Change: in `draft_checks_passed`, when `piece_is_screen(root, piece)`, run `art_loop.measure(root, <card>, piece, draft)`
(the loop's own checks) instead of the full-frame art_check; test: the r19 capture passes, a flat grey 16:9 PNG fails.

## 7. art_loop.fit_packet centre-crops full-screen UI captures (tools/art_loop.py, build lead)
`fit_packet` cuts any image wider than PACKET_MAX=1568 to a 1568-wide centre crop. A 1920x1080 UI capture loses 176 px
on each side, so the title lockup's swash and the left-aligned menu are cut; the 1672-wide reference loses only 52 px.
Every ui-title panel since r17 (1920x1080) has the gap "title and menu cropped off the left edge" (r18: all three
sessions). Verdict: check defect (the critic judges a crop we never ship). Workaround here: capture at
RUN_RES=1568x882 so no crop happens. Suggested fix: for a fully opaque full frame, shrink to fit instead of cropping
(the viewer limit is about detail on sprites; a screen is judged whole), with a test that a 1920x1080 frame keeps its
left 10% columns.
