# Art priority (Josh, Nov 13)

Every art loop works its pieces top-down in this order, and when capacity frees up the next loop goes to the highest
piece nobody owns. Piece ids are the art-loop pieces in `docs/build/art-inventory.csv`.

| Rank | What | Pieces | Loop |
|---|---|---|---|
| 1 | Ella's states | ella-up-open, ella-attack, ella-shield, ella-closed | artella |
| 2 | The Keeper | owl, keeper-wing, keeper-talon, keeper-clock, keeper-damage, keeper-mech-front, keeper-mech-middle, keeper-mech-rear, keeper-departure | artkeeper, artkeeper2 |
| 3 | Backdrop and skyline (every scene shows it) | skyline, paper, scene, bg-base, bg-atmosphere, bg-land, bg-water, bg-architecture, bg-clock, bg-clock-water-wind, bg-start-end | artscene, artscene2 |
| 4 | Title screen and HUD | ui-title, ui-hud-clock, ui-xp-ring | artui, artui2 |
| 5 | Ella's main shots and the most frequent effects | wand-shot, owl-bolt, bolt-hit, yellow-shot, stream-beam, vfx-gold-impact, vfx-gold-fade, vfx-gust, vfx-gust-puff, vfx-keeper-warning, vfx-keeper-strike, vfx-clock-beat | artshots, artfx, artfx2 |
| 6 | Regular enemies (Sundial first) | enemy-sundial, enemy-armillary, enemy-repeater, enemy-courier, enemy-floodstrider | artenemy, artenemy2 |
| 7 | Everything else | the remaining UI screens, rarer effects and states (ella-motion, ella-down, ella-hurt, ella-transition, umbrella, umbrella-repair, ella-condition, world-*, menu-screen, the other vfx-*, wind-lines, wind-zone) | the owning loop |
