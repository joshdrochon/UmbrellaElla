# artella requests (to the build lead)

## 1. The `context` pair makes a first pass impossible inside this lane (tools/art_loop.py, not my lane)
- What: `art_loop.py panel` lists `context` as missing for every Ella piece ("no in-engine capture made after the
  piece: import it and run the smoke"). The area brief says a piece is imported only after it passes. So no Ella piece
  can pass today, whatever the reference and quality-bar panels answer.
- Second problem: the context pair puts the whole game screenshot against the key art. That verdict depends on the
  scene, the Keeper and the shots (other lanes), not on the Ella sprite.
- Decision needed (Josh or lead; this is a bar question, so I am not choosing):
  - (a) the lead imports a candidate that has passed `reference` + `quality_bar` + the deterministic checks as a
    tracked `_PH`, runs the smoke, and the context panel runs on that capture; or
  - (b) context is judged once for the `scene` piece only, not per element piece.
- My lean: (a). It keeps the bar as written and only fixes the order of steps.
- Until answered: I run the `reference` and `quality_bar` panels and the deterministic checks, and keep every piece `_PH`.
