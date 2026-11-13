# Requests from artshots

## 1. Art-loop packet: flatten a transparent entry on the team paper, not a flat colour (tools/art_loop.py)
`flatten_on_ground` puts our sprite on one flat cream colour (`PACKET_GROUND`); every reference sits on its own textured
paper. Opus critics name the "flat, untextured ground" in most remaining losses (owl12: 3 of 3 losses; wand5: 3 of 3;
hit1: 4 of 4). Test: wand-shot E6 on `pipeline/art/reference/Test_Assets/SKY_StarPaper_Tile.png`, same seeds: nobody
names the ground, 1 of 3 wins (flat ground: 0 of 3). Not a loosening: the game draws the sprite on that paper.

    -        g = PACKET_GROUND
    -        flat = [[tuple((c * a + gc * (255 - a)) // 255 for c, gc in zip(px[:3], g)) + (255,) for px in row
    -                 for a in (px[3],)] for row in rows]
    +        pw, ph, paper = read_png(os.path.join(ROOT, "pipeline/art/reference/Test_Assets/SKY_StarPaper_Tile.png"))
    +        flat = [[tuple((c * px[3] + gc * (255 - px[3])) // 255 for c, gc in zip(px[:3], paper[y % ph][x % pw]))
    +                 + (255,) for x, px in enumerate(row)] for y, row in enumerate(rows)]

Needs a test in `tests/test_art_loop.py` (a transparent entry comes out with more than one ground colour).

## 2. `context` pair: first capture
No piece can pass without an in-engine capture made after the piece, and import is allowed only after a pass. Lead to
say how the first capture is made (my lean: I commit the import script once a piece clears every other pair; the lead
imports, runs the smoke, and I run the `context` sessions on that screenshot).

## 3. Calibration pair for wand-shot is unstable
The crude image for wand-shot is the rust-cross bolt; against the pale `wand-star` sheet critics sometimes pick the
crude one (wand3 session c3: 3 runs, 3 misses), so the session is refused whatever it says about ours. A crude gold
pulse in `tests/fixtures/art/crude/` for `wand-shot` would fix it.

## 4. references.json: `discord-crop-red-release` does not list card 0.10b
`art_ref_check --card 0.10b --element bolt-hit` therefore scores bolt-hit only against the two whole sheets (fill share
of the bounding box). The stored `score_min` was measured the same way, so it is consistent, but the crop is never used.
