# artshots status (worker, 12 Nov)

Nothing ships yet. Every piece is still a tracked `_PH` (no `.artloop.json`, no provenance row, no import script).

## What exists
- `tools/build/assets/art_shots.py <piece> --scale N --out-dir Art/Source/<Asset>/Raw/StillN` renders a piece through
  Blender with the shared planner (look, palette). `art_shots_blender.py` holds my builders (shared `stand_ins.py` untouched):
  `shot_red`, `shot_gold`, `burst_red`, `wind_lines`, `wind_zone`; palette-exact graded layers, per-pixel grain,
  engraved hatch, geometry ink outline (Freestyle off: its AA edges blow `off_style`).
- Renders: `Art/Source/{OwlBolt,WandShot,BoltHit,WindLines,WindZone}/Raw/Still*/`.

## Deterministic checks (art_check sprite rules, screen_check, art_ref_check)
| piece | result | note |
|---|---|---|
| owl-bolt | PASS (score 0.744 / min 0.729, off_style 0.019) | 4x render (640x320); at 1x the AA edges fail off_style |
| wand-shot | PASS (0.698 / 0.334) | same builder, gold family |
| bolt-hit | FAIL | detail 0.32 < detail_min 0.362 (score capped to 0.2); lifting detail with grain/ink lines pushes off_style past 0.02 |
| wind-lines | FAIL | art_check passes; ref score 0.2 (detail 0.24 < 0.408) |
| wind-zone | FAIL | art_check passes; detail 0.09 < detail_min 0.421 |

## Blind panel (owl-bolt, rounds 1 to 5, `art_loop.py panel`, 12 Sonnet critics per round)
Round 1 rust-cross placeholder look; 2 pixel blob; 3 to 5 palette-exact vector with hatch and grain. Calibration 10 to 11/12.
Verdict each round: reference still wins in most sessions. Same gap every round: "flat vector fills, no etched line or paper
texture, serrated head not one sharp point, tail too long / loose squares". Progress: critics stopped calling it a blob and
started picking ours over the old rust needle. Not yet unanimous ours/SAME, so no pass.

## Blockers
1. `context` pair: the panel needs an in-engine capture made after the piece (import, then smoke screenshot). No piece can
   pass without it; that needs the build lead's package/smoke. Import script not written until a piece clears the other pairs.
2. Calibration (for the lead, not loosened): wind-zone `detail_min` 0.421 is above its only reference's own detail (0.099), and
   wind-lines/wind-zone `score_min` are "not measurable" defaults (0.582) that a stroke sprite cannot reach by shape alone.
   Suggest re-measuring those two elements. Critic itself looks sane (rust needle is picked against, calibration 10/12).

## Next
owl-bolt: single sharper head (one point, not stacked teeth), shorter tail, visible etched interior line work; re-run panel.
Then bolt-hit detail, then wind pieces once their calibration is fixed.

## Round 6 (after merge of main 4ed1d35, critic-packet fix): owl-bolt re-run, earlier rounds treated as invalid
- Panel on Still4 (best render), 12 critics, packet now flattens transparent renders onto paper: reference/quality-bar picked over ours in
  9 of 12 real folders (ours 2, SAME 0-1). Gap every time: flat vector fills, no etched line or paper grain; head reads as a jagged
  double-saw not one clean point; tail ends in loose squares. Same gap as rounds 3-5, so the old evidence was not the cause.
- Critic sanity: calibration folders 23/24 right (reference vs itself = SAME, known-bad = loses). Critic is sane; ours genuinely fails.
- Tried: etched ink slivers from the head along each spike (Still6). Visually almost no change; not re-panelled (would not pass).
- Still blocked as before: `context` pair needs an in-engine capture; bolt-hit/wind-lines/wind-zone fail deterministic checks
  (wind calibration numbers are the lead's to re-measure, see Blockers above).
- Next real step: a shaded (radial/gradient) shell with a bounded glow mask and finer etched hatch, not more line slivers.

## 12 Nov evening (Fable worker): engraved-print technique, critics on Opus
Nothing ships yet. All five stay tracked `_PH`. Critic sessions now run `claude-opus-5-5` (main's rule for critics;
the brief still says Sonnet; Opus is the stricter of the two, calibration 10 to 12 of 12 per round).

New builder: `tools/build/assets/art_shots_etch.py <piece> <out.png> [seed] --blend <file> --mul 2` (Blender, through
`ue_slot.sh`). The piece is a tone field cut through a hand-cut line screen into the GDD ramp (ink, shadow, shell, hot,
core), with a broken ink contour and a bounded stippled light. Every opaque pixel is one ramp colour. 8x masters.

| piece | panel folder | render | art_ref (min) | panel: ours wins | gap in the losses |
|---|---|---|---|---|---|
| owl-bolt | owl9 | GP9 (flat polygons) | 0.766 (0.729) | 2 of 12 | flat vector fills, no etched line, no paper grain, tail too long |
| owl-bolt | owl10 | E11 | 0.790 | 7 of 12 | flat untextured ground; tail longer than head; uniform machine stripes |
| owl-bolt | owl11 | E12 (hand-cut lines, cross-hatch, full ink contour) | 0.817 | 8 of 12 | flat ground; long saw-tooth body |
| owl-bolt | owl12 | E13 (compact body) | 0.823 | 9 of 12 (red-shot crop 3/3, d-red-shots 3/3, double-beat 2/3, quality bar 1/3) | flat ground (3), no bounded glow (2), tail (1) |
| wand-shot | wand4 | GP3 | 0.699 (0.334) | 3 of 6 (reference 3/3, quality bar 0/3) | no ink line work, no paper grain, flat ground |
| wand-shot | wand5 | E6 | 0.687 | 3 of 6 (reference 3/3, quality bar 0/3) | flat ground; flat colour bands in the star |
| bolt-hit | hit1 | E3 | 0.678 (0.666) | 4 wins + 1 SAME of 9 (quality bar 0/3) | flat ground; long beam tail; posterized fills |
Deterministic checks (art_ref_check, screen_check, art_check sprite colour rules) pass on every render in the table.

### Critic sanity (three tests, evidence under `Saved/panel/sanity*`, not committed)
1. Reference as the entry (red-shot crop vs the quality bar, 3 sessions): the bar wins 3 of 3 ("flat vector fills, no
   etched line or paper grain"). A team reference does not have to beat the top bar, so no defect by itself.
2. The quality bar's own red shot, cut out and flattened like ours, vs its own sheet (3 sessions): the cut-out wins 2,
   loses 1 ("cropped so tight no paper is left"). The critic does not reject an isolated shot as such.
3. Ground test: wand-shot E6 composited on the team paper tile (`SKY_StarPaper_Tile.png`) vs the quality bar, same
   seeds as wand5: 1 win, 2 losses, and no session names the ground any more (flat ground: 0 of 3, all three name it).
Verdict: work and check both. Work: remaining gaps are real (hatching inside the wand star, tail lengths) and are being
fixed. Check defect (packet): our transparent sprite is flattened on a flat cream ground while every reference sits on
its own textured paper, and most remaining losses name that ground. Request with the diff: `docs/build/requests/artshots.md`.

### Blockers (unchanged)
- `context` pair: needs an in-engine capture after import (lead's package and smoke). No piece can pass before that.
- wind-zone `detail_min` fix (area/artcal 7ad7ebd) is not on this branch yet.

## 13 Nov: Gemini rollout (blocked on key)
Merged main. Prompts for owl-bolt, bolt-hit, wand-shot written and reviewed by a fresh Art Director session
(`Art/Source/<Asset>/prompt.md`, `prompt-review.md`; its corrected prompt, used word for word, is `prompt.final.txt`).
Review changes: no ink outline (light contour), no painted glow (light is a separate layer), sparse hatch only, tail per reference.
Open for the lead: one call = one frame; how the loop frames are made (scale/thin the peak frame) is decided after the panel.
BLOCKED: `tools/assetgen.py image` refuses, `GEMINI_API_KEY is not set` in this shell. Worker rules forbid me reading
`~/.umbrella-ella.env`. Spend so far by me: 0. Next: run the three calls (about $0.42; commands in prompt.final.txt, 21:9/1:1/21:9, 2K,
`--element effects`), `assetgen clean --chroma 00FF00`, art_ref_check, panel.

## 13 Nov: Gemini painted (gemini-3-pro-image-preview, 2K, $0.139 each, 3 calls = $0.42; shared spend 3.209 of 33.82)
Calls from `prompt.final.txt`, outputs `Art/Source/<Asset>/Paint/g1.png`. The default model (2.5 flash) refuses `--image-size`; pass `--model gemini-3-pro-image-preview`.
Post: `assetgen clean --chroma 00FF00 --grow 1`, then `tools/build/assets/art_shots_fit.py` (Blender: crop, scale to 0.9 of canvas, snap each pixel to the GDD ramp with 0.1 tone jitter as grain) -> `g1_fit.png`.
Deterministic (art_loop.measure): owl-bolt PASS 0.732, wand-shot PASS 0.664, bolt-hit PASS 0.688 (art_check, screen_check, art_ref_check all pass).
Triage: unsnapped paint drifts off palette (off_style 0.11 to 0.25): ours (post), fixed by snap. Hard snap flattened bolt-hit detail (0.2 cap): ours, fixed by jitter. Next: blind panel.

## 13 Nov: Gemini panel round 1 (after merging area/artinventory; critics Opus, panels Saved/panel/{owlG2,wandG2,hitG2}, not committed)
| piece | art_ref_check | panel | gap |
|---|---|---|---|
| owl-bolt | FAIL 0.595 (min 0.729; was 0.732 before the merge) | reference wins; quality bar 1/3 ours, reference 2/3; calibration 8/12 | flat posterized fills, no etched line or paper grain |
| wand-shot | PASS 0.664 | reference wins (round 6) | star is glossy gradient, no near-black etched linework; calibration 6/6 |
| bolt-hit | FAIL 0.651 (min 0.666; was 0.688) | refused: calibration 7/9, rerun needed | not judged |
No piece passes. Still blocked on the `context` pair (needs an in-engine capture after import).
Triage open: the score drop on owl-bolt/bolt-hit followed the inventory merge (references.json now 100 entries, new min/closest ref). Verdict "check changed, not our pixels": g1_fit.png bytes are unchanged. Not yet tested on a known-good input; the lead's art_ref_check owner should confirm the new owl-bolt min 0.729 still holds with the added refs.
Next: bolt-hit panel rerun; add etched dark linework to the paintings (prompt gap on both shots), one more Gemini call each if the lead keeps Spend OK.

## 13 Nov: art_ref_check triage and etched-ink repaints (merged main e10efbd9)
Check triage: verdict "check holds, earlier drop was the old reference set". On the merged main (refs=d1afca932485): the reference
images clear their own min (discord-crop-red-shot 1.0, d-red-shots 1.0, d-clock-double-beat 0.965 vs owl-bolt min 0.729; bolt-hit
discord-crop-red-release 0.686 vs min 0.666), and the unchanged g1_fit.png scores owl-bolt 0.732 (PASS) and bolt-hit 0.688 (PASS) again.
No check defect now; the 0.595/0.651 readings came from the pre-fix set in area/artinventory (89debfe6 fixed it on main).
Repaint (ours, prompt): critics' gap was no near-black etched linework. v2 asked for bold ink: art_ref_check FAIL (owl 0.2: dark-ink blends
at the 24x24 downscale read as off-band maroon, offband 0.127 > 0.05; dark share 0.50 vs refs ~0.2). v3 thin ink 1.5 px, v4 also slim
shadow facets, dark tones under a quarter: owl g4 PASS 0.744, wand g3 PASS 0.583, bolt-hit g3 PASS 0.685 (Art/Source/<Asset>/prompt.v*.txt, Paint/g*_fit.png).
Lesson: ink-heavy art must keep the dark share near the references or art_judge's value/offband terms fail it. art_shots_fit.py gained an ERODE arg
(ink thinning); not used on the candidates (it flattens the ink look). Spend by me this session: about $0.97 (shared 7.72 of 33.82). Panels: Saved/panel/{owlG3,wandG3,hitG3}.
