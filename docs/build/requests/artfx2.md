# artfx2 requests

## 1. Calibrate the vfx-* elements (check defect, blocks all 8 artfx2 pieces)
Triage verdict: check defect, not work. Evidence (Nov 13, after merging main and artslots):
- `art_judge.py element vfx-clock-beat` on my best sheets: sheet3 score 0.593 (offband ok), sheet4/sheet5 0.2 (offband gate, art_check --effect passes).
- min is 0.729, inherited from owl-bolt (`calibration.method: "inherits the thresholds of owl-bolt"`), never measured on vfx-clock-beat's own refs. Known-good input fails: the reference shots (d-red-shots, red-shot-sh10) score 0.0 against their own element in my earlier run.
- The 0.2 cap fires when `offband > 0.05` on a 24x24 downscale of the first frame; ink outline next to crimson averages to a dark red outside the allowed hue bands, so crisp ink lines (which the blind critic asks for) trip it.
Needed: run `art_judge.py calibrate` for vfx-clock-beat, vfx-keeper-strike, vfx-keeper-warning, vfx-keeper-recovery, vfx-clock-open, vfx-eye-exposed, vfx-departure, vfx-restoration (leave-one-out on their own refs, score_min/detail_min), and make the offband measure ignore dark ink pixels (L* <= 35, the `dark` share is already measured separately) with a test on a reference shot.
Until then more paint cannot pass; spend left unspent (14.41 of 33.82).

## 2. vfx-* calibration measured whole reference sheets, not shots (check defect, blocks all 8 pieces)
Request 1 is done, but the new bar cannot be met by any effect sprite. Measured Nov 13 (tools/art_judge.py signature):
- The vfx elements list whole Discord concept sheets (d-red-shots, d-clock-double-beat, d-talon-rake, study-keeper-red-shots) with no `cell`.
  Their signature is an opaque paper rectangle: mask 1.00, aspect 1.34-1.49, dark 0.11-0.14. A transparent sprite has mask 0.3-0.6 and aspect ~1.
  Two sheets with the same layout score each other 0.965 leave-one-out, so score_min came out 0.945 for vfx-clock-beat (0.93 for keeper-warning/strike).
  That is a sheet-layout match, not an effect look. A shot cut out of the sheet cannot reach it.
- Known-good input: the crops that exist already (discord-crops/red-shot.png, red-release.png, keyart-crops/owl-bolt.png) score each other 0.529-0.733.
  My clock-beat sheet5 scores 0.548 / 0.524 / 0.533 against them, i.e. a measurable, closeable gap.
Needed (references.json, not my lane): for the 8 artfx2 pieces (and any other vfx-* with sheet refs), put the shot crops (`discord-crop-red-shot`,
`discord-crop-red-release`, `owl-bolt` keyart crop) in `refs`, make the sheet refs `judge`-excluded for the silhouette score (or give them a `cell`/crop
on the shot), and rerun `art_judge.py calibrate`. Expected score_min about 0.71 (0.733 - 0.02).
Until then more paint cannot pass; spend left unspent.
