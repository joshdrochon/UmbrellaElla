# fixmove status
Done (build exit 0, 210/210 tests, module_check 0, manifest_check 0):
- COM-06 Burst option: `SmallBurstCount` 1-5 (default 1), `SmallBurstSpacing` 0.08 s; emitter queues the extra shots, release cancels them. Tests: `UmbrellaElla.Move.SpellBurstRules`, `UmbrellaElla.Move.World.SmallBlastBurst`.
- COM-07 Streamed Blast beam actor: `AStreamBeamActor` grows 1200/s to 1400, width 14, stops at a solid blocker, damage 4 per tick at 10/s through the shot receivers (no pulse projectiles). Test: `UmbrellaElla.Move.World.StreamBeamActor`.
Left: beam art is a placeholder cube; startup/sustain/release art belongs to the art lanes. Burst has no input to change the count yet (tuning only).
