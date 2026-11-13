# Area: storyinventory

Started by the build lead from this brief (2026-11-12). It is the definition of done.

Lead: new lane (Josh). The story bar counts only the lines in pipeline/story/lines.csv (the story critic's input; critic.sh story judges every line there, tools/story_check.py checks them). Find every piece of player-facing text the game ships and make sure the story critic and story_check judge it:
1. Inventory all shipped player text: grep Source for FText/LOCTEXT/NSLOCTEXT/TEXT shown to the player and data/config/assets that hold text: Start Game's flow story pages, tutorials and prompts, menus, settings, purchase and level-up text, HUD labels, credits, Journey Complete statistics, Director's Cut lines, defeat/victory, sound-label dev text excluded (dev-only, F9). For each: id, where it lives, the exact text, screen.
2. Add every shipped line to pipeline/story/lines.csv in its format (keep existing rows and ids).
3. tools/build/story_inventory.py: a check that FAILs for any shipped player text not in lines.csv (and for a lines.csv row whose text differs from the source). Wire it into tools/build/quality_gate.py as blocking no-new-FAIL, with a test.
4. Run tools/story_check.py on the new set (don't run the paid critic panel; the gate's story critic runs on merge). Report in your status, as the last line: TOTAL=<lines> BEFORE=<old count> NEW=<added> PASSED=<lines with a recorded critic pass>, and per screen counts.
Targeted tests only. Merge main first. Commit, stop.
