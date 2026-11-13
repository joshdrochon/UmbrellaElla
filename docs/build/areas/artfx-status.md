# artfx status

## Slice 1 (Nov 12): VFX wiring, light policy, light shaft, placeholder sheets
Lane note: the brief's `Feedback/VFX/**` is the existing `Feedback/Vfx/` folder (case-insensitive disk). See `docs/build/requests/artfx.md`.

### Built (code)
| Rule ID | What | Where | Tests |
|---|---|---|---|
| VFX-02 | 48 effects in one table, each with its sheet, layer, timing and light; sheets imported as textures and shown on a camera-facing quad through `M_VFX_Sheet_PH`; a stand-in shape when a sheet is missing | `Feedback/Vfx/VfxCatalog`, `VfxSheetVisual`, `Art/Source/VFX/import_vfx.py` | `Feedback.VfxCatalogRules` |
| VFX-03 | Small Blasts release/travel/impact/fade; Streamed Blast startup/sustain (sized to the beam hitbox)/contact/stop; Twin Stars two release anchors and two heads; Needle channel/pulse/sliver/pierce and protected contact. Driven by the bus (`ProjectileSpawned`, `ProjectileContact`, `UmbrellaConfigChanged`) and the live beam actor | `UUmbrellaVfxDirectorSubsystem` | `Feedback.World.VfxWeaponWiring` |
| VFX-05 | Warning/strike/recovery for talon and the three casts; gust warning/release/travel/expiry; clock double beat (one per beat), opening/cover; part hit/break; stun, slow, exposed eye, blackout, restoration; departure. Read from the fight model each step, anchored on the model's head/claw/gust/clock positions. Safe pause and recovery start no damage-looking effect | `KeeperVfxRules`, director | `Feedback.VfxKeeperRules`, `Feedback.World.VfxKeeperWiring` |
| VFX-07, VFX-08 | Per-effect additive light overlay (sprites stay unlit) plus an unshadowed point light; local radius, effect colour, fades and leaves with the effect; on/off switch. This is the default of the open row D-new-sh10-vfx-lighting; the decision is still open | `VfxLightPolicy`, director | `Feedback.VfxLightAndShaftRules`, `Feedback.World.VfxIlluminationOnOff` |
| NAR-05 | Light shaft through Ella's position; umbra under the open umbrella follows her; folding closes the gap in 0.15 s and light passes below her. Looks only | `LightShaftRules`, director | `Feedback.VfxLightAndShaftRules`, `Feedback.World.VfxLightShaftAndUmbra` |
| VFX-11 | Acceptance in tests: each event shows its effect once, at its anchor, stops on retry/defeat/phase start; no double with the shared subsystem; concurrency cap and flash gap | all of the above | the five tests above |

No gameplay timing, collision or state is written by any of it (tests check the shot velocity, Ella's and the Keeper's position stay untouched).

### Art (all tracked `_PH`, nothing shipped)
- 28 sheets (8 x 1 cells of 128), Blender 5.2.1, `Art/Source/VFX/vfx_sheets.py` -> `Art/Source/VFX/Raw/*_PH.png`, imported to
  `Content/UmbrellaElla/Art/VFX/T_VFX_*_PH` with `M_VFX_Sheet_PH` and `M_VFX_Spill_PH`. Provenance: 28 rows, origin `placeholder`.
- No art loop pass exists for any sheet. `pipeline/art/references.json` has no judge element for these effects (request 4), so the
  official panel cannot open for them.
- Blind critic probe (one fresh Sonnet session per pair, Twin Star head against the `wand-shot` element, which describes the same gold star head):
  | Round | Change | Reference pair | Quality-bar pair | Calibration folders |
  |---|---|---|---|---|
  | 1 | flat emissive shapes, soft glow | reference wins: "soft airbrushed glow, no ink silhouette, etched line or paper grain" | not run | 2/2 right |
  | 2 | ink outline behind each shape, hatching engraved as ink, paper grain, no glow disc | ours wins | ours wins | 4/4 right |
  Round 2 is 1 session per pair, not a panel, so it is not a pass. The quality-bar reason faulted the bar image for being a concept
  sheet with a wand, which is a content reason, not a finish reason: I do not count that pair.
  The ink outline + engraved hatch + grain recipe is what moved the reference pair; it may help the artshots lane.

### Not done / not run
- VFX-11 evidence the GDD asks for and this lane could not produce: gameplay-scale screenshots or video, the illumination on/off
  capture, performance profile on target hardware, editable-source change -> reimport test on a device. Headless runs are `-nullrhi`.
- Sheet orientation on the quad (not mirrored, upright) is checked only by a rotation test, not by eye in a rendered frame.
- Art loop pass for any sheet (blocked by request 4 and by the `context` pair needing an in-engine capture).
- VFX-10 numerical budgets stay OPEN in the GDD; the cap (40 live effects) and flash gap (0.34 s) are this build's values.
- Reduced-flash toggle is not wired from Settings to the director (request 2).
- Blackout veil opacity (0.55) is my value; the GDD gives none.
