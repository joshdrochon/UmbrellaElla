# audioimport status (2026-11-12)
Imported with `tools/build/assets/audioimport_plan.py` (plan) then `audioimport_import.py` (editor, exit 0). Rule: take has a blind-critic pass on
its bytes (or a person approval) and is not a tracked placeholder. All Content/UmbrellaElla/Audio .uasset were made writable first; I checked
all 64 planned assets exist and were rewritten (the editor logs nothing on a silent read-only failure, so the check is by mtime).
- Imported: 64 takes, 24 sounds. Targeted test `UmbrellaElla.Audio`: PASS tests=4.
- Not imported, tracked placeholders: 35 takes (stay placeholders).
- Not imported, no critic record on current bytes: 86 takes in 64 sounds (older flat cues and earlier takes stay). They pass audio_check but nobody judged them. Need the critic (Audio lane).
- Missing files: 35 of 140 live rows (P0: 25, P1: 10). Owner in sound-list.csv is `Audio` for all; no snd lane made them, so the audio lane generates them:
  UmbrellaOpen UmbrellaClose HopWhoosh DashWhoosh GustCatch WindExit AbsorbStart AbsorbLoop AbsorbStop ShieldHeal UmbrellaRepair UmbrellaCreak
  LowHealthLoop LifeLost Restart SafeLanding EllaBump GustEnd TalonRecovery CastReturn StunZap StunRecover ClockOpen ClockClose TimeSlowStart
  TimeSlowEnd EyeExpose BlackoutStart BlackoutEnd EncounterStart PhaseChime CourierWithdraw ShutterOpen BellowsRecover CheckpointReached
- `audio_check.py --scan Audio/Source`: FAIL errors=40 = 25 missing P0 files + 15 placeholder/critic conflicts (below). The 10 missing P1 rows are not errors.
- Conflict found: 15 takes (HitProtected, MechanismBreak, ShutterClose, SmallBlastImpact, WingsBreak) are marked `placeholder` in provenance but the
  critic record passes those exact bytes (SNDHIT rounds 2-3). The check fails on it. I left them placeholders and did not import them. Fix is
  `pipeline/audio/build/promote.sh <Id>` (Audio lane), then re-run the plan and import.
