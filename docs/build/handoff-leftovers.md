# Handoff leftovers

Open items at handoff. These go into the HANDOFF "Follow-up list". The pipeline stops at handoff, so the team picks these up.

## artui2 (parked)
- In-game UI shots: `UIShotSubsystem` (`Private/Tests/UI`) with `-UIShotsMode=dc` saves the title screen for
  journey-complete, xp-ring, level-up and story-caption. Fix each step's Do/Ready so the widget is on screen when
  the shot is taken. There is no ui-spell-wheel shot; add one. Details: `docs/build/requests/artui2.md` on `area/artui2`.
- ui-credits and ui-story-text need the tutorial-style heading, gold rule and panel in `SFlowTextScreen`
  (artui's files). Apply it there.
