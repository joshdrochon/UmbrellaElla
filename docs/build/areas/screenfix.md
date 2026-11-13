# Area: screenfix

Started by the build lead from this brief (2026-11-12). It is the definition of done.

Area screenfix, top priority. The agent play-tester (area/agentplay, docs/build/areas/agentplay-status.md 'Findings on the game as rendered') shows the game is unreadable on screen in a real render: (1) with no light, the lit placeholder cubes (Ella, guard, enemies) render black, only the HUD clock and a dim light shaft show; (2) with a light, a large grey tiled surface covers the room, so Ella and the guard can't be seen at their positions. Fix the game, not the hook:
- Level lighting: the shipped map(s) and route must light gameplay actors (or the stand-ins and art slots use unlit materials, consistent with the 2D art style); decide by what the art bible and artslots' unlit slot material do, and make it the same everywhere.
- Draw order: backdrop layers (UUmbrellaBackdropSubsystem, the paper tile that now spans all 9 stages) must sit behind gameplay at every camera position; find what puts the grey tiled surface in front (depth, translucency sort, camera-facing plane) and fix it.
- Proof: a real render capture (RUN_RES=1280x720 tools/build/run_game.sh -SmokeShot=...) of the Mill room with no hook light where Ella and the guard are visible; add a world test that gameplay actors are in front of every backdrop layer, and a screen check (tools/screen_check.py or art_check) that fails on a mostly-black or mostly-flat frame.
Put the captures under pipeline/art/proof/screenfix/. Targeted tests only. Merge main first. Commit after each fix, then stop.
