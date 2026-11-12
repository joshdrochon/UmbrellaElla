# Animation, tiling and audio review (Art Director and Asset Specialist, on demand)

Load this for any card that adds a flipbook, a tiling asset, or a sound.

## Flipbooks
- [ ] Judged in motion: a clip from a packaged or Standalone build at the gameplay camera, showing
      move → open → close → attack → hurt. Stills alone never approve a flipbook or umbrella-state art.
- [ ] Every frame keeps the same design: umbrella stripe count and handle, Ella's proportions, outline weight.
      No boiling outline. The umbrella never vanishes between frames.
- [ ] The bottom-center pivot does not drift. The opaque bounding box's bottom-center moves ≤ 2 px across the frames of every
      silhouette sheet with an `"anim"`, one-shots (Open, Close, Attack, Hit, Death) included (proposed, D-new-port-13).
      Measured by `sprite_check.py`. A sidecar may raise it with `"pivot_drift_max_px"` only with a `"pivot_drift_reason"`. Paste the PASS line.
- [ ] One pivot per asset across all its anims (idle and Open must not jump): `--import-report` fails a mixed set.
- [ ] Keyframes play in ascending `_NN` with holds as `frame_run`, never a repeated sprite (`--import-report`).
- [ ] Frame count and fps fit the `anims` row in `style.json`: the sidecar's `"anim"` for the sheet, `--import-report` for the `FB_` asset.
- [ ] A `_PH` silhouette version of this flipbook was played in L_Graybox and its frame count confirmed before final frames.
- [ ] Each flipbook maps to one C++ state (named in the asset brief). It says loop or one-shot, and what interrupts it.
- [ ] Gameplay never waits on a flipbook. No damage window, state change or invulnerability starts on a flipbook's end or a frame event.

## Tiling assets (paper background, landscape layers)
- [ ] Reviewed with at least 3 copies side by side in the engine. No visible seam. No obvious repeat pattern at 1080p.
- [ ] `sprite_check.py` with `"kind": "tile"` prints PASS: mean edge ΔE76 ≤ `seam_delta_e_max` (add `"tile_axes": "xy"` for paper that tiles both ways).

## Sounds
- [ ] `python3 tools/audio_check.py --scan Audio/Source` PASS pasted; rules in `pipeline/roles/audio.md`.
- [ ] Every sound that signals a state (owl windups, player hurt, umbrella tear) has a matching visual. The game is playable muted.
- [ ] Provenance row filled, like art.
