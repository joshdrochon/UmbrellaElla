# Area: move (Ella movement and the basic shot)

Branch `area/move`. Read `docs/build/worker-rules.md` first.

## Rule IDs
G1 first: MOVE-04, MOVE-05, MOVE-06, MOVE-07, MOVE-11, MOVE-13, MOVE-14, MOVE-15, MOVE-18, MOVE-19, MOVE-20, MOVE-21,
MOVE-22, CORE-04, CORE-05, UMB-05, COM-05, COM-06, COM-10.
Later (G3): MOVE-12, MOVE-16, COM-07, COM-08, COM-09, COM-11 (the four Director's Cut spells, unlocks 1/10/20/30 and
the spell wheel input; the wheel UI belongs to `flow`, you expose the selection state and events).

## GDD sections
3 (Controls at a glance, Mechanic cards: Action states and movement, Health/absorption/weapons, Default controls and
input behavior, Shared player contract, Four spell mechanics, Weapon scope), 9 (Numeric parameters: movement and weapon
rows). Feel: `docs/feel-spec.md`, `pipeline/feel/feel.json`; gate `python3 tools/feel_check.py` must stay 0 problems.

## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Input/**`, `Motor/**`, `Umbrella/**`, `Attack/**`
- `Source/UmbrellaElla/Private/Tests/Move/**`, `Private/Tests/Shared/**` (you create the shared world-test helper
  other areas will reuse: transient world, spawn Ella, tick N frames at a fixed delta)
- `Content/UmbrellaElla/Input/**` except `Input/Menu/**`; `tools/build/assets/input_*.py` (editor scripts that make
  IA_*/IMC_Default)
- `pipeline/feel/**`, `docs/build/areas/move-status.md`, `docs/build/requests/move.md`

## What to build
- Input Adapter: IMC_Default at priority 0 with IA_Shoot, IA_Absorb, IA_Hop, IA_DashBack, IA_DashForward, IA_Ride,
  IA_Trim (keyboard + gamepad defaults from MOVE-05..MOVE-08). Assets via a committed editor Python script, or built in
  C++ at runtime if assets are impractical (say which in your status file). It maps holds to requested actions only.
- Umbrella State: the four-state action model (rise, shoot-fall, absorb-fall, free fall when both held) plus hop, dash
  (back/forward), ride, trim; one `UENUM` changed by one function; tests that forbidden combos cannot happen.
- Player Motor: the only writer of velocity. Rise/fall speeds, trim, dash, hop, current riding (WIND-03 currents are
  `arena`'s volumes: they broadcast WindEntered/WindExited on the event bus with the current's force in `Value`/`Detail`;
  you react to those events), lift scaled by health (UMB-05: listen to PlayerHealthChanged), bounds.
- Attack Emitter: Small Blasts, unlimited, fired only while dropping (shoot-fall), always to +X, cadence and damage from
  your tuning, via `AUmbrellaProjectile::Fire` with `EUmbrellaShotKind::PlayerBlast`. No ammo.
- Ella is visible: until `arena` lands the flipbooks, nothing to do; the AnimPresenter is theirs.

## Done
Worker-rules "Definition of done", plus world tests: rising with nothing held, shoot-fall emits shots to +X only while
dropping, absorb-fall state, both held = free fall with no shooting, dash and hop change velocity as tuned, at 1/30,
1/60 and 1/120 s deltas. `tools/feel_check.py` 0 problems.
