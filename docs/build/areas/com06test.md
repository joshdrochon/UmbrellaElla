# Follow-up: COM-06-off test. Branch area/com06test (from area/fixmove). Read docs/build/worker-rules.md first.
Write a world test that fails if turning COM-06 off mid-stream leaves a live beam actor or queued burst shots: start a
Streamed Blast with bursts queued, switch the flag off (the test-only setter pattern used in the keeper area, or a request
if none exists for COM_06), step the emitter, assert no beam actor remains and the burst queue is empty. Prove the test
can fail: break the fix on purpose (comment out the HideBeam/clear in StepEmitter), see it fail, restore. Lane:
Source/UmbrellaElla/Private/Tests/Move/**, Attack/** (a test-only setter only). Done: worker-rules DoD.
