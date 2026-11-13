
## Keys after a click (Nov 13)
SFlowMenu now keeps focus itself: an active timer retakes focus onto the selected row whenever focus is on nothing or the game viewport, and Up/Down (arrows, W/S, D-pad, stick) move the selection inside OnKeyDown, so they work whatever holds focus. Covers Start, Pause, Settings stub, Defeated, Level-up. Not covered (other lanes' widgets): the full settings page and Journey Complete. Test: UmbrellaElla.Flow.MenuMouse.EmptyClickKeepsSelectionAndKeys (Flow suite 36/36 pass). Not tested: a real click in the window on Josh's Mac.

## Review fixes (Nov 13, review round 1)
Rule IDs: MOVE-09 (mouse click selects in menus), FLOW-34 (Start screen: Start Game selected on open, marker on the
selected row, control hint), FLOW-35 (Pause: click and keys choose). rule-status.csv rows updated with the tests below;
statuses unchanged (all three were already `built`). clause-proof.csv: MOVE-09 "mouse click selects in menus" ->
`UmbrellaElla.Flow.MenuMouse.ClickChoosesEachItem`.
Tests (Flow suite 36/36 PASS at 23a53d26): Flow.MenuMouse.FirstItemSelectedOnOpen, HoverSelects, ClickChoosesEachItem,
KeysAndPadStillChoose, MarkerLinesUpWithSelectedRow, EmptyClickKeepsSelectionAndKeys.
Captures, Start screen at 1600x900 (`RUN_RES=1600x900 tools/build/run_game.sh -UIShots=<dir>`; Saved/ is not committed):
- before: `Saved/menumouse/before/title.png` (09:35, the build before the first menumouse commit)
- after: `Saved/menumouse/after/title.png` (build 23a53d26)
`-SmokeShot` cannot take this shot: it waits for gameplay to start, so the run left the title and shot nothing.
What the captures show: the after shot adds the "Click or Enter to choose" hint bottom right. Both show Start Game lit,
because the -UIShots driver selects the first row itself; the old bug (nothing lit, the gold rule above read as the
marker) shows only without that driver, so the captures do not prove the fix. The tests do (selected on open, marker Y).
Also: focus keeper timer now runs every 0.1 s (KeepFocusIntervalSeconds), not every frame; GetLastOpened comment fixed.
Still open: Journey Complete clicks have no test; hint wording is fixed text, not read from the current bindings.
