# artfx2 requests

## 1. Calibrate the vfx-* elements (check defect, blocks all 8 artfx2 pieces)
Triage verdict: check defect, not work. Evidence (Nov 13, after merging main and artslots):
- `art_judge.py element vfx-clock-beat` on my best sheets: sheet3 score 0.593 (offband ok), sheet4/sheet5 0.2 (offband gate, art_check --effect passes).
- min is 0.729, inherited from owl-bolt (`calibration.method: "inherits the thresholds of owl-bolt"`), never measured on vfx-clock-beat's own refs. Known-good input fails: the reference shots (d-red-shots, red-shot-sh10) score 0.0 against their own element in my earlier run.
- The 0.2 cap fires when `offband > 0.05` on a 24x24 downscale of the first frame; ink outline next to crimson averages to a dark red outside the allowed hue bands, so crisp ink lines (which the blind critic asks for) trip it.
Needed: run `art_judge.py calibrate` for vfx-clock-beat, vfx-keeper-strike, vfx-keeper-warning, vfx-keeper-recovery, vfx-clock-open, vfx-eye-exposed, vfx-departure, vfx-restoration (leave-one-out on their own refs, score_min/detail_min), and make the offband measure ignore dark ink pixels (L* <= 35, the `dark` share is already measured separately) with a test on a reference shot.
Until then more paint cannot pass; spend left unspent (14.41 of 33.82).
