# Area: visuals (final art, animation, VFX and backgrounds)

Branch `area/visuals`. Read `docs/build/worker-rules.md` first. Split from `arena` Nov 12 14:05 (memory allows more workers).

## Rule IDs (G3, but placeholders that read well help every gate)
BG-02 .. BG-06, ART-05 .. ART-10, ANIM-02 .. ANIM-10, VFX-02 .. VFX-11.

## GDD sections
8 (Art, animation, VFX and audio: start screen and menu look, linked asset card, art-director brief, production state
coverage and replaceable art contracts, enemy prompts, environment inventory and prompts, weapon/Keeper/shot prompt
packs, prompt execution and review, Unreal VFX creation and integration). Art bar: `pipeline/art/art-bible.md`, the key
art and `pipeline/art/reference/`. Checks: `python3 tools/art_ref_check.py --help`, `tools/art_loop.py`,
`tools/art_check.py`, `tools/sprite_check.py`.

## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Feedback/**` except `Feedback/Audio/**` (arena keeps sound)
- `Source/UmbrellaElla/Private/Tests/Feedback/**` except `Tests/Feedback/Audio*`
- `Content/UmbrellaElla/Art/**`, `Art/Source/**`, `pipeline/art/**`, `tools/build/assets/art_*.py`,
  `docs/build/areas/visuals-status.md`, `docs/build/requests/visuals.md`

## What to build
- The Animation Presenter (`UEllaAnimPresenterComponent`, already there from arena) and presenters for the Keeper,
  enemies and shots: they read state through public getters and bus events only, show Paper2D flipbooks per state, and
  fall back to a visible neutral stand-in when art is missing. Never gameplay authority (CORE-04, CORE-05).
- Art generation through the pipeline tooling (`tools/assetgen.py`, `tools/art_loop.py`; keys live outside the repo,
  never print them). Each generated asset goes in `Content/UmbrellaElla/Art/<Asset>/` with a provenance row in
  `pipeline/art/provenance.csv`. A generated asset replaces a placeholder only when `tools/art_ref_check.py` /
  art_loop says it meets the reference bar; otherwise keep the placeholder and record the score.
- Backgrounds (BG-02..06): layered, looping, behind the play camera, never touching collision or wind.
- VFX (VFX-02..11): Niagara or Paper2D flipbook effects driven by bus events, synced to gameplay events, not to
  animation clocks.
- Gameplay never waits on art: do not change hitboxes, timing or velocity.

## Done
Worker-rules DoD, plus world tests: each presenter shows a stand-in with no art and the mapped flipbook with art, art
swaps never change collision sizes. Art checks recorded in your status file.
