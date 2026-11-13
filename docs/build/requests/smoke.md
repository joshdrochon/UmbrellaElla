# Requests from the smoke area

## 1. `Failed to load` in every packaged smoke (blocks a clean PASS)
Packaged Mac log line: `LogAudio: Display: No default SoundConcurrencyObject specified (or failed to load).`
`tools/ue_run.py` SMOKE_BAD_BROAD counts it (pattern `Failed to load`, case-insensitive), so smoke FAILs on it.
Either fix (both outside the smoke lane, build lead's choice):
- `tools/ue/smoke-allow.txt`: add `D<n> | LogAudio: Display: No default SoundConcurrencyObject` (needs a decision row; engine text, harmless), or
- `Config/DefaultEngine.ini`: set a default SoundConcurrency asset in `[/Script/Engine.AudioSettings]`.

## 2. Smoke fps limits need a quiet machine
`SMOKE_MIN_FPS=55` / `SMOKE_MAX_FRAME_MS=33` failed here (32 to 38 fps) while the machine load average was 10 to 25 (parallel workers).
Re-run the smoke on a quiet machine before trusting the fps verdict.
