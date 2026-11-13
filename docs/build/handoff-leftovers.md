# Handoff leftovers

Open items at handoff. These go into the HANDOFF "Follow-up list". The pipeline stops at handoff, so the team picks these up.

## artui2 (parked)
- In-game UI shots: `UIShotSubsystem` (`Private/Tests/UI`) with `-UIShotsMode=dc` saves the title screen for
  journey-complete, xp-ring, level-up and story-caption. Fix each step's Do/Ready so the widget is on screen when
  the shot is taken. There is no ui-spell-wheel shot; add one. Details: `docs/build/requests/artui2.md` on `area/artui2`.
- ui-credits and ui-story-text need the tutorial-style heading, gold rule and panel in `SFlowTextScreen`
  (artui's files). Apply it there.

## screenfix follow-ups (coordinator, Nov 13 13:10: not blocking)
- Mill-room capture with Ella and the guard visible. The Mill is in no run (GDD; decision row D-new-mill-in-route is open with Josh).
- Two `_PH` `.uasset` stand-ins (screen:Playing, screen:Resuming) were removed with `git rm`, against AGENTS.md section 7.
  Nothing in Content/ refers to them. The Producer or Technical Director records the exception.
- Ella reads as dark ink on the near-black umbra (low contrast): lighten the umbra or outline Ella (artella / artfx).

## settings2 request 7
- Reduced motion and text scale do not reach screens and effects outside Settings/** (flow menus, story widgets, VFX, HUD).
  The owning lanes apply the reads listed in `docs/build/requests/settings2.md` (request 7).

## keeper
- `UmbrellaElla.Keeper.QueuedEmissionsRunOnScaledWorldTime` (area/keeper 507f1350, not on main) fails: "Expected 'slowed'
  to be true". The commit that rewrote it was only pre-checked, never run in Unreal.
