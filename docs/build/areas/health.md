# Area: health (shots, absorbing yellow, health, damage, lives and the clock HUD)

Branch `area/health`. Read `docs/build/worker-rules.md` first.

## Rule IDs
G1 first: SURV-05, SURV-07, FLOW-30, FLOW-31, FLOW-32, FLOW-33, plus the Projectile Service (all shots in the game) and
the clock HUD with health and life hands (MVP item 4: 3 hits x 3 lives, damage 1 / 1.25 / 1.5, yellow heals).
Later: none (progression moved to the `progression` area, Nov 12 14:10). Lead call: arena walls and ceiling block
PlayerShot/EnemyShot; the Projectile Service destroys a shot on any blocking hit.

## GDD sections
3 (Health, absorption and weapons; Shared player contract), 4 (Gameplay systems, Progression system card, Director's
Cut progression baseline), 7 (HUD/clock parts of Menus, settings and accessibility), 9 (health/damage numbers).

## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Projectile/**` (the Core seam headers there are yours to extend, not rename),
  `Health/**`, `Defense/**`, `UI/**` (except `UI/Menus/**`, `UI/Progression/**`, `UI/Story/**`)
- `Source/UmbrellaElla/Private/Tests/Health/**`, `Private/Tests/Projectile/**`
- `Content/UmbrellaElla/UI/HUD/**`, `docs/build/areas/health-status.md`, `docs/build/requests/health.md`

## What to build
- Projectile Service: `AUmbrellaProjectile` motion (X/Z), radius collision on the PlayerShot/EnemyShot channels,
  lifetime, contact routing: call `IUmbrellaShotReceiver::ReceiveShot` on the hit actor, then on its components; a
  Consumed result destroys the shot. Player shots never hit Ella; enemy shots never hit the Keeper. Broadcast
  ProjectileSpawned/ProjectileContact. A visible placeholder (engine sphere or sprite: red, yellow, player colors).
- Health (`UUmbrellaHealthComponent`, implements IUmbrellaShotReceiver): 3 hits x 3 lives, damage scale by the
  GDD rule, post-hit protection, red shots damage, broadcast PlayerHealthChanged, LifeLost, PlayerDefeated (the last
  life; FLOW-31). Health never moves Ella or reloads anything.
- Absorb (`UAbsorbReceiverComponent`): during absorb-fall (read `UUmbrellaStateComponent` through a public getter;
  if it is not there yet, listen to UmbrellaConfigChanged events) yellow shots are absorbed and heal (SURV-07);
  broadcast CatchAttempt/CatchSucceeded/CatchFailed.
- `AUmbrellaHUD` + C++ widget: one clock HUD with health and life hands, inside the 16:9 view, readable text >= 18 px.

## Done
Worker-rules DoD, plus rule tests for damage scaling and life loss, world tests: a red shot costs one hit, three hits
cost a life, the last life broadcasts PlayerDefeated once, a yellow shot during absorb-fall heals and is consumed, a
yellow shot outside absorb-fall does not heal, player shots pass through Ella.
