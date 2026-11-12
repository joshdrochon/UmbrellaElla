#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Attack/SpellRules.h"
#include "Core/UmbrellaPlayMode.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "AttackEmitterComponent.generated.h"

class UEnhancedInputComponent;
class UUmbrellaStateComponent;

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

	int32 GetShotsFired() const { return ShotsFired; }
	const FUmbrellaShotSpec& GetLastShot() const { return LastShot; }

	/** Raised when the equipped spell changes (the wheel UI and HUD listen). */
	FOnEquippedSpellChanged& OnEquippedSpellChanged() { return EquippedChanged; }

protected:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	void FireVolley();
	void Equip(EUmbrellaSpell Spell);
	void OpenWheel();
	void CloseWheel();

	UPROPERTY(Transient)
	TObjectPtr<UUmbrellaStateComponent> UmbrellaState;

	FOnEquippedSpellChanged EquippedChanged;
	FUmbrellaShotSpec LastShot;
	EUmbrellaSpell Equipped = EUmbrellaSpell::SmallBlasts;
	EUmbrellaSpell WheelPreview = EUmbrellaSpell::SmallBlasts;
	EUmbrellaSpell HeldKey = EUmbrellaSpell::Count;
	EUmbrellaPlayMode PlayMode = EUmbrellaPlayMode::StartGame;
	float Countdown = 0.0f;
	float StreamHeldSeconds = 0.0f;
	float KeyHeldSeconds = 0.0f;
	int32 DirectorLevel = 0;
	int32 ShotsFired = 0;
	bool bWheelOpen = false;
	bool bWheelLockedState = false;
};
