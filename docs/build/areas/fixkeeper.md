# Follow-up: keeper fixes (HANDOFF follow-ups). Branch area/fixkeeper. Read docs/build/worker-rules.md first.
Tasks, commit after each: (1) Core header `Source/UmbrellaElla/Public/Core/UmbrellaSourceIds.h` with the attack source
ids (GUST_Band, TALON_Rake, MECH_Front_Cast and the others the Encounter Director emits) as `static constexpr` TCHAR*
or FName getters; switch health (`Private/Health/**`) and keeper (`Private/Encounter/**`, `Private/Owl/**`) to it.
(2) The gust push goes through the motor: the Encounter Director broadcasts an event (e.g. WindEntered/WindExited with
SourceId GUST_Band, or a new request) and `UEllaMotorComponent` applies it; remove `AddActorWorldOffset` from the
director (one writer of position/velocity). (3) With OWL-35 off a final hit must not leave the fight Active with the
model halted. (4) The gust push uses world-scaled time like the model. Tests for each.
Lane: Core/UmbrellaSourceIds.h, Health/**, Encounter/**, Owl/**, Motor/** and their tests. Done: worker-rules DoD.
