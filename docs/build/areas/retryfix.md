# Area: retryfix

Started by the build lead from Josh's 14 Nov bug report. It is the definition of done.

- D-new-retry-reload: on the Defeated screen, Retry (click or Enter) restarts the encounter from its beginning in both modes: full
  health, the Keeper at its first phase, every projectile and beam (AimedBeamActor) cleared. Reopening the map is fine.
- Proof: with real input, after a defeat Retry reaches Playing at full health with the Keeper at phase 1 within 2 s.
