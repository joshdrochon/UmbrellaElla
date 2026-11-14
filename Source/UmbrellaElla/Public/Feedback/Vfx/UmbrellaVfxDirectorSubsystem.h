#pragma once

#include "CoreMinimal.h"
#include "Attack/SpellRules.h"
#include "Feedback/Vfx/KeeperVfxRules.h"
#include "Subsystems/WorldSubsystem.h"
#include "Umbrella/UmbrellaAction.h"
#include "UmbrellaVfxDirectorSubsystem.generated.h"

class AActor;
class AUmbrellaProjectile;
class UPointLightComponent;
class UStaticMeshComponent;
struct FUmbrellaEvent;
struct FVfxArtRow;

namespace UmbrellaVfxDirectorConst
{
	/** Most effects alive at once. One-shots beyond it are dropped; held state effects (warnings, veils) never are. */
	static constexpr int32 MaxLive = 40;
#if !UE_BUILD_SHIPPING
	/** Art capture only (-VfxDemo=<Key>): where the replayed effect sits, relative to Ella. */
	static constexpr float DemoOffsetX = 150.0f;
	static constexpr float DemoOffsetZ = 30.0f;
	/** Art capture only: wall seconds into the demo when the scene (no UI) is written to Saved/Screenshots. */
	/** Zoomed capture (label it 'zoomed'): ortho width 1920 -> 480 is a camera 4x closer; the effect keeps its own size. */
	static constexpr float DemoZoomedOrthoWidth = 480.0f;
	static constexpr float DemoShotSeconds = 4.0f;
	/** Art capture only: the sheet cell the demo effect holds while shown (the bright, readable beat of a doubled four-frame sheet). */
	static constexpr int32 DemoHoldFrame = 2;
	/** Art capture only: the paper-coloured quad behind the demo effect (the key art's ground), so the context crop is not a black graybox. */
	inline const FLinearColor DemoBackdropColour(0.16f, 0.13f, 0.11f, 1.0f);
	static constexpr float DemoBackdropDepth = 5.0f;
	static constexpr float DemoBackdropWidth = 3000.0f;
	static constexpr float DemoBackdropHeight = 1800.0f;
	/** The demo replays its effect only when a key is set and none of that key is live. */
	inline bool ShouldPlayDemo(const FName DemoKey, const int32 LiveOfKey)
	{
		return !DemoKey.IsNone() && LiveOfKey == 0;
	}
#endif
	/** A held effect whose state never ends is cleared after this long, so nothing can stay up forever. */
	static constexpr float MaxHeldSeconds = 20.0f;
	/** Size of an effect that covers the whole view (blackout, slow, restoration). */
	static constexpr float ScreenCover = 6000.0f;
	/** The beam art's bright core fills this fraction of its cell height; the quad is sized so the core matches the hitbox. */
	static constexpr float BeamCoreFraction = 0.5f;
	/** "Long ago": before any beat or flash. */
	static constexpr float NeverSeconds = -1000.0f;
	static constexpr int32 ShaftParts = 3;
	/** Light above Ella: a faint shaft, not a solid bar (visualqa: at 1.0 it read as a cream placeholder bar on the dark frame). */
	static constexpr float ShaftAboveOpacity = 0.3f;
}

/** One live effect. Plain bookkeeping; the actor is the only world object. */
struct FVfxLiveEffect
{
	int32 Serial = 0;
	FName Key;
	const FVfxArtRow* Row = nullptr;
	TWeakObjectPtr<AActor> Actor;
	TWeakObjectPtr<AActor> Follow;
	bool bFollows = false;
	FVector FollowOffset = FVector::ZeroVector;
	bool bKeeperAnchored = false;
	EKeeperVfxAnchor Anchor = EKeeperVfxAnchor::Body;
	float StartClock = 0.0f;
	TWeakObjectPtr<UPointLightComponent> Light;
	TWeakObjectPtr<UStaticMeshComponent> Spill;
	float LightIntensity = 0.0f;
	float SpillOpacity = 0.0f;
};

/** A player shot the effects follow from release to impact or fade. */
struct FVfxTrackedShot
{
	TWeakObjectPtr<AUmbrellaProjectile> Shot;
	EUmbrellaSpell Spell = EUmbrellaSpell::SmallBlasts;
	FVector LastLocation = FVector::ZeroVector;
	int32 TravelSerial = 0;
	bool bConsumed = false;
};

/**
 * The effect director: the four weapons' effects, the Keeper's state effects, and the light shaft with the umbrella's
 * umbra. It listens to the event bus and reads public state; it never writes gameplay state, adds no collision and
 * keeps its own clock from game time, so pause and slow apply to effects exactly as they do to play. Art lane (artfx).
 */
UCLASS()
class UMBRELLAELLA_API UUmbrellaVfxDirectorSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** True for the bus events this director shows (player shots and Keeper events); the shared-combat subsystem skips them. Pure. */
	static bool IsDirectorEvent(const FUmbrellaEvent& Event);

	/** Advance every effect by DeltaSeconds of game time. Tick calls it; tests call it directly. */
	void StepEffects(float DeltaSeconds);

	/** Start an effect at a place, optionally following an actor. Returns its serial, or 0 when nothing was shown. */
	int32 Play(FName Key, const FVector& Location, AActor* Follow);

	/** Stop every live effect with this key. */
	void Stop(FName Key);

	/** Stop everything (retry, defeat, reset). */
	void StopAll();

	int32 GetPlayCount(FName Key) const;
	int32 GetLiveCount(FName Key) const;
	int32 GetLiveTotal() const { return Live.Num(); }
	int32 GetDroppedCount() const { return DroppedCount; }
	int32 GetFlashDimmedCount() const { return FlashDimmedCount; }
	FVector GetLastLocation(FName Key) const;
	AActor* GetLiveActor(FName Key) const;

	/** Nearby-surface light: switch every effect's light and overlay on or off (the on/off comparison). */
	void SetIlluminationEnabled(bool bEnabled);
	bool IsIlluminationEnabled() const { return bIllumination; }

	/** Accessibility: dim flashing lights. Whatever owns the setting calls this. */
	void SetReducedFlash(bool bReduced) { bReducedFlash = bReduced; }
	bool IsReducedFlash() const { return bReducedFlash; }

	EUmbrellaSpell GetEquippedSpell() const { return Equipped; }
	EUmbrellaAction GetEllaAction() const { return EllaAction; }
	float GetUmbraOpenness() const { return UmbraOpenness; }
	/** Light shaft parts: 0 = shaft above Ella, 1 = shaft below her, 2 = umbra. */
	AActor* GetShaftPart(int32 Index) const;

protected:
	virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override;

private:
	void HandleProjectileSpawned(const FUmbrellaEvent& Event);
	void HandleProjectileContact(const FUmbrellaEvent& Event);
	void HandleConfigChanged(const FUmbrellaEvent& Event);
	void HandleBossTargetHit(const FUmbrellaEvent& Event);
	void HandleBossTelegraph(const FUmbrellaEvent& Event);
	void HandleBossPartDestroyed(const FUmbrellaEvent& Event);
	void HandleReset(const FUmbrellaEvent& Event);

	void StepShots();
	void StepStream();
	void StepNeedleChannel();
	void StepKeeper();
	void StepShaft(float DeltaSeconds);
	void StepLive();

	int32 PlayAnchored(FName Key, EKeeperVfxAnchor Anchor);
	void StopSerial(int32 Serial);
	void StopFamilyHeld();
	void DestroyEffect(FVfxLiveEffect& Effect) const;
	FVfxLiveEffect* FindSerial(int32 Serial);
	FVector KeeperAnchorLocation(EKeeperVfxAnchor Anchor) const;
	AActor* FindElla();
	AActor* FindActorNamed(FName Id) const;

	TArray<FDelegateHandle> Handles;
	TArray<FVfxLiveEffect> Live;
	TArray<FVfxTrackedShot> Shots;
	TMap<FName, int32> PlayCounts;
	TMap<FName, FVector> LastLocations;
	TWeakObjectPtr<AActor> Ella;
	TWeakObjectPtr<AActor> ShaftActors[UmbrellaVfxDirectorConst::ShaftParts];
	FKeeperVfxSnapshot KeeperBefore;
	FVector LastContactLocation = FVector::ZeroVector;
	FVector StreamEnd = FVector::ZeroVector;
	EUmbrellaSpell Equipped = EUmbrellaSpell::SmallBlasts;
	EUmbrellaAction EllaAction = EUmbrellaAction::Rise;
#if !UE_BUILD_SHIPPING
	/** Art capture only: -VfxDemo=<Key> replays that effect beside Ella whenever none is live, so a smoke shot shows it. */
	FName DemoKey = NAME_None;
	double DemoStartSeconds = -1.0;
	bool bDemoShotTaken = false;
	TWeakObjectPtr<AActor> DemoBackdrop;
	void StepDemo();
	FVector DemoCentre(const AActor* Player) const;
	void SpawnDemoBackdrop(const FVector& Around);
#endif
	float Clock = 0.0f;
	float LastFlashClock = UmbrellaVfxDirectorConst::NeverSeconds;
	float LastBeatShotClock = UmbrellaVfxDirectorConst::NeverSeconds;
	float UmbraOpenness = 1.0f;
	int64 BossHitFrame = -1;
	int64 ContactFrame = -1;
	int32 NextSerial = 1;
	int32 StreamSerial = 0;
	int32 ChannelSerial = 0;
	int32 DroppedCount = 0;
	int32 FlashDimmedCount = 0;
	bool bStreaming = false;
	bool bIllumination = true;
	bool bReducedFlash = false;
};
