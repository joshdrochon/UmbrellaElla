#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Attack/SpellRules.h"
#include "Attack/SpellPresentation.h"
#include "Core/UmbrellaPlayMode.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "AttackEmitterComponent.generated.h"

class UEnhancedInputComponent;
class UUmbrellaStateComponent;
class AStreamBeamActor;
class AAimedBeamActor;
struct FAttackTuning;
struct FMotorTuning;

DECLARE_MULTICAST_DELEGATE_OneParam(FOnEquippedSpellChanged, EUmbrellaSpell);

/**
 * Attack Emitter: the equipped spell, unlimited, fixed right, only while dropping (shoot-fall). Start Game has only
 * Small Blasts; Director's Cut has the four, unlocked by level. Fires through AUmbrellaProjectile::Fire. No ammunition,
 * no stored energy. Owns the selection state and the spell wheel state; the wheel UI belongs to the flow lane. Lane a.
 */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UAttackEmitterComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UAttackEmitterComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);

	/** Test seam: advance the emitter by a fixed delta without a world tick. */
	void StepEmitter(float DeltaSeconds);

	/** Flow sets the mode; Progression sets the Director's Cut level. Neither equips anything by itself. */
	void SetPlayMode(EUmbrellaPlayMode Mode);
	void SetDirectorLevel(int32 Level);

	EUmbrellaSpell GetEquippedSpell() const { return Equipped; }
	EUmbrellaPlayMode GetPlayMode() const { return PlayMode; }
	int32 GetDirectorLevel() const { return DirectorLevel; }

	/** Only an unlocked spell can be equipped. */
	bool CanEquip(EUmbrellaSpell Spell) const;

	/** Equip a spell; ignored when it is locked. */
	void SelectSpell(EUmbrellaSpell Spell);

	/** Next (+1) or previous (-1) unlocked spell. */
	void CycleSpell(int32 Direction);

	/** Spell key (1-4 / right-stick direction): a flick equips at once; holding past the wheel time opens the wheel. */
	void PressSpellKey(EUmbrellaSpell Spell);
	void ReleaseSpellKey(EUmbrellaSpell Spell);

	/** The wheel pauses gameplay while open; release confirms the previewed spell. */
	bool IsWheelOpen() const { return bWheelOpen; }
	EUmbrellaSpell GetWheelPreview() const { return WheelPreview; }

	/** Current Streamed Blast beam length (0 unless streaming). */
	float GetStreamLength() const;

	/** The live Streamed Blast beam actor, or null when not streaming. */
	AStreamBeamActor* GetBeam() const { return Beam; }

	/** Aimed shot (D-new-aimed-shot): seconds Shoot has been held toward the next beam (0 when not charging). */
	float GetAimChargeSeconds() const { return AimHeldSeconds; }

	/** True while a held Shoot is charging a beam (Small Blasts, shooting fall, off cooldown, none fired this hold). */
	bool IsAimCharging() const;

	/** The aimed beam on screen, or null. */
	AAimedBeamActor* GetAimedBeam() const { return AimedBeam; }

	/** Seconds the current aimed beam has been on screen (0 when none). */
	float GetAimedBeamAge() const { return AimedBeam ? AimedBeamAge : 0.0f; }

	/** Aimed beams fired so far. */
	int32 GetAimedBeamsFired() const { return AimedBeamsFired; }

	/** Burst shots still waiting to leave . */
	int32 GetPendingBurstShots() const { return PendingBurstDelays.Num(); }

	/** Tests pass their own tuning copy by const reference; the class default is never written. */
	void SetTuningOverride(const FAttackTuning& InTuning) { TuningOverride = &InTuning; }
	void ClearTuningOverride() { TuningOverride = nullptr; }
	void SetMotorTuningOverride(const FMotorTuning& InTuning) { MotorOverride = &InTuning; }

	/** Test only: behave as if the burst-shot feature flag were switched off (the flag table is a constant). */
	void SetCom06OffForTest(bool bOff) { bCom06OffForTest = bOff; }

	int32 GetShotsFired() const { return ShotsFired; }
	const FUmbrellaShotSpec& GetLastShot() const { return LastShot; }

	/** Body family for the equipped spell (RegularFall or the shoulder-braced ShoulderFall). Presentation reads it. */
	EUmbrellaBodyPose GetBodyPose() const { return SpellPresentationRules::BodyPoseFor(Equipped); }

	/** Canopy cycle as it is now: Small Blasts snap open on each actual emission, then cock back to folded-ready. */
	EUmbrellaCanopyPhase GetCanopyPhase() const { return Canopy.Phase; }

	/** Canopy pulses shown so far (one per Small Blasts emission). */
	int32 GetCanopyPulses() const { return Canopy.Pulses; }

	/** The four spells as the wheel shows them now: locked ones carry their unlock-level label. */
	TArray<FSpellWheelEntry> GetWheelEntries() const;

	/** Raised when the equipped spell changes (the wheel UI and HUD listen). */
	FOnEquippedSpellChanged& OnEquippedSpellChanged() { return EquippedChanged; }

protected:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

private:
	const FAttackTuning& ActiveTuning() const;
	const FMotorTuning& ActiveMotor() const;
	FVector SizedMuzzle(const FAttackTuning& Tuning) const;
	const FMotorTuning* MotorOverride = nullptr;
	/** Borrowed from the caller (a test); must outlive its use. */
	const FAttackTuning* TuningOverride = nullptr;
	void FireVolley();
	void ShowBeam(const FAttackTuning& Tuning);
	void HideBeam();
	void StepAimedShot(float DeltaSeconds, const FAttackTuning& Tuning);
	void FireAimedBeam(const FAttackTuning& Tuning);
	void HideAimedBeam();
	FVector AimedMuzzle(const FAttackTuning& Tuning) const;
	void Equip(EUmbrellaSpell Spell);
	void OpenWheel();
	void CloseWheel();

	UPROPERTY(Transient)
	TObjectPtr<UUmbrellaStateComponent> UmbrellaState;

	UPROPERTY(Transient)
	TObjectPtr<AStreamBeamActor> Beam;

	UPROPERTY(Transient)
	TObjectPtr<AAimedBeamActor> AimedBeam;

	float AimHeldSeconds = 0.0f;
	float AimedBeamAge = 0.0f;
	float AimCooldownLeft = 0.0f;
	int32 AimedBeamsFired = 0;
	bool bAimFiredThisHold = false;

	TArray<float> PendingBurstDelays;
	FOnEquippedSpellChanged EquippedChanged;
	FUmbrellaShotSpec LastShot;
	FCanopyCycleState Canopy;
	EUmbrellaSpell Equipped = EUmbrellaSpell::SmallBlasts;
	EUmbrellaSpell WheelPreview = EUmbrellaSpell::SmallBlasts;
	EUmbrellaSpell HeldKey = EUmbrellaSpell::Count;
	EUmbrellaPlayMode PlayMode = EUmbrellaPlayMode::StartGame;
	float Countdown = 0.0f;
	float StreamHeldSeconds = 0.0f;
	float KeyHeldSeconds = 0.0f;
	int32 DirectorLevel = 0;
	int32 ShotsFired = 0;
	bool bCom06OffForTest = false;
	bool bWheelOpen = false;
	bool bWheelLockedState = false;
};
