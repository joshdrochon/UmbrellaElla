# winddraw status
- FLOW-25 (wind width and kinds): AWindCurrent draws a plane covering the whole usable box (`GetDrawnSize` vs `GetUsableSize`). Kind (Transport, Descent, Rescue; `KindFor`) picks the colour: `FieldColourFor` reads FieldTuning colours, Rescue has its own (`RescueFieldColour`), so a rescue current is not told apart from lift by direction alone.
- Material is the engine `BasicShapeMaterial` with a `Color` parameter. No painted gust texture is loaded yet (`T_VFX_Gust` is not in the code).
- Tests: `UmbrellaElla.Field.World.CurrentDrawsItsUsableWidth` (drawn size = usable size, resize redraws, kinds, and the three kinds draw distinct material colours).
- Left: painted gust art and opacity per kind; backdrop coverage (artslots); QA-36 playtest re-measure.
