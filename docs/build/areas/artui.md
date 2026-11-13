# Art loop: every UI screen to the bar. Branch area/artui. Read docs/build/worker-rules.md first.
Gap (Josh's screenshot, Nov 12): the Defeated screen is default flat UMG (navy fill, plain sans, lilac pills), nowhere
near the bar. Only "menu-screen" is an art-loop piece; Defeated, Settings, Credits, purchase, level-up, pause and HUD had
no visual bar check.
1. Make the bar unskippable first: every shipped screen is an art-loop piece. Add an element per screen to
   pipeline/art/references.json (title, pause, settings, credits, defeated/retry, win story text, journey complete,
   purchase, level-up, tutorial, HUD clock, XP ring), each judged against the title-screen reference
   (references.json `title-screen`, layout and style; title text "Umbrella Ella The Stolen Hour" per D-new-title-text)
   and the bar images. Add a check (tools/ui_check.py subcommand, wired into its `ci`) that fails when a C++ widget class
   or screen under Source/UmbrellaElla/**/UI/** or Flow/** has no matching element, so a new screen cannot skip the bar.
   Test it: a fake screen with no element must fail.
2. One shared UI style module (Source/UmbrellaElla/Public|Private/UI/Style/**): paper ground, ink lettering in the
   title-screen reference's look, readable gamepad/keyboard focus states, text >= 18 px inside the 16:9 view; fonts and
   textures made in Blender or procedurally (Blender only, D-new-art-blender) with provenance rows. Apply it to every
   screen (edit only the widget build/paint code of each screen; no behaviour changes).
3. Loop each screen as a piece: capture it in-engine from your worktree (smoke -SmokeShot or an editor capture of the
   screen), run the deterministic checks (tools/screen_check.py, tools/art_check.py, tools/ui_check.py ci), then the blind
   panel (tools/art_loop.py blind/panel/verdict, fresh critic sessions, --disallowedTools Bash Edit Write) against the
   title-screen reference and the bar images. Loop until every screen passes. Critic sanity before any stuck call: the
   reference vs itself must be SAME, a known-bad (the current flat UMG screen) must lose, the critic agrees with itself.
Lane: UI/Style/**, the paint/layout code of the widgets in Flow/**, UI/**, Settings/**, Story/** (UI only), tools/ui_check.py,
pipeline/art/references.json (screen elements only), Art/Source/UI/**, Content/UmbrellaElla/UI/**, tests. No gameplay.

Image model: read docs/build/art-image-model.md; it applies once the lead says Spend OK.
