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
