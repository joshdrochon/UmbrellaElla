# com06test status
- Done: test `UmbrellaElla.Move.World.Com06OffClearsBeamAndBursts` (queued Small Blast bursts and a live Streamed Blast beam, flag off, step, assert empty queue, no beam pointer, no beam actor). Test-only setter `SetCom06OffForTest` on the emitter.
- Proved it can fail: commented out the burst reset + HideBeam in the flag-off branch of StepEmitter; test FAILED; restored; full suite PASS tests=248.
- Left: nothing.
