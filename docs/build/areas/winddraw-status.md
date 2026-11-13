# winddraw status
- FLOW-25 (wind width and kinds): AWindCurrent draws a plane covering the whole usable box; kind (Transport, Descent, Rescue) picks tint and opacity (FieldTuning). Loads T_VFX_Gust if painted, else stand-in via M_VFX_Spill_PH.
- Test: UmbrellaElla.Field.World.DrawnWidthMatchesUsable (drawn = usable width and height for three kinds). Build 0, Field and BrokenMill tests PASS, module_check clean for these files.
- Left: backdrop coverage (artslots); QA-36 playtest re-measure; painted gust art.
