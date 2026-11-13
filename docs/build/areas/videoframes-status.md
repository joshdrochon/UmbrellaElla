# videoframes status (2026-11-13)

Cut only (lead: no build, no editor in this lane). The stand-ins lane imports in its own editor session.
All 17 clips cut at 24 frames: `video_to_strip.py --counts 24 --grid-cols 6` (12 fps extract, 540 px, same keying and
feet-anchor registration as the idle), then cropped to the union alpha box (+4 px) and re-gridded 6 per row.
Grid sheets are all under 8192 px wide. Each piece has `<piece>_N24_grid.png`, `<piece>_N24_grid.sprite.json`
(silhouette, 24 frames, cell, fps, loop, pivot bottom-centre), a preview GIF, the source mp4 and provenance rows
(origin: generated in jam, fal Veo 3.1 Fast clip cut into frames, stand-in, not passed). No pass record written.
Folder: `pipeline/art/proof/videoframes/<piece>/`. Import: `tools/build/assets/import_art_candidate.py`, like the idle grid.

| Piece | Grid cell | fps | Target slot (art_slots.py) | Texture |
|---|---|---|---|---|
| ella-down | 397x527 | 6.0 | ella-state:Down | T_Ella_Down |
| ella-hurt | 499x533 | 7.38 | ella-state:Hurt | T_Ella_Hurt |
| ella-transition | 341x528 | 7.78 | ella:mode-transition | T_Ella_Transition |
| wand-shot | 445x185 | 12.0 | shot:gold | T_WandShot |
| owl-bolt | 503x134 | 7.78 | shot:red | T_OwlBolt |
| bolt-hit | 707x599 | 13.09 | shot:red-impact | T_BoltHit |
| gold-impact | 972x544 | 15.16 | vfx-sheet:VFX_GoldImpact | T_VFX_GoldImpact |
| clock-beat | 558x411 | 8.47 | vfx-sheet:VFX_ClockBeat | T_VFX_ClockBeat |
| armillary-attack/hurt/turn | 515x427, 719x409, 409x420 | 6.0, 9.93, 6.55 | enemy:ArmillaryLauncher:Female | T_Enemy_ArmillaryLauncher_Female |
| repeater-attack/hurt/turn | 385x424, 631x410, 351x423 | 7.02, 9.6, 6.0 | enemy:EscapementRepeater:Female | T_Enemy_EscapementRepeater_Female |
| sundial-attack/hurt/turn | 366x408, 476x417, 254x408 | 7.02, 9.93, 6.0 | enemy:SundialCaster:Female | T_Enemy_SundialCaster_Female |

## Notes for the importer
- Enemy slots are one texture per enemy, not per state: attack, hurt and turn have no drawing slot of their own. Cut, not imported; the stand-ins lane picks (lean: attack into the slot texture, the other two stay in proof).
- gold-impact and wand-shot: the full clip has empty tail frames (sparks only), so the cut uses a 2.5 s trim (`*-trim.mp4`, kept beside the source). bolt-hit uses `bolt-hit-trim.mp4` (the cut one).
- The loop window picks the end frame closest to frame 0, so one-shot clips (hurt, attack, gold-impact) lose their tail: source frames used = loop_end+1 (see `<piece>.report.json`). `loop` in the sprite.json is true for all; set it false for one-shots when importing.
- Skipped on purpose: artvideo/ella-idle.mp4 (stand-ins lane) and artella/preview/*_preview.mp4 (previews).
- Not run: build, capture, PRECHECK (no editor/build in this lane by lead's order). Imported: 0 of 17.
