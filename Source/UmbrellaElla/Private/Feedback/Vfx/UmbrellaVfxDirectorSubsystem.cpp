#include "Feedback/Vfx/UmbrellaVfxDirectorSubsystem.h"
#include "Attack/StreamBeamActor.h"
#include "Components/PointLightComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Components/StaticMeshComponent.h"
#include "Misc/App.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaSourceIds.h"
#include "Core/UmbrellaTuning.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Engine/World.h"
#include "UnrealClient.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "EngineUtils.h"
#include "Feedback/Vfx/LightShaftRules.h"
#include "Feedback/Vfx/UmbrellaVfxSubsystem.h"
#include "Feedback/Vfx/VfxCatalog.h"
#include "Feedback/Vfx/VfxLightPolicy.h"
#include "Feedback/Vfx/VfxSheetVisual.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"
#include "Camera/CameraComponent.h"
#include "Arena/UmbrellaArena.h"
#include "Owl/KeeperOfTime.h"
#include "Owl/KeeperPartComponent.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Umbrella/UmbrellaPlayerIds.h"

namespace
{
	const FName VfxDirectorKeeperSource(TEXT("KeeperOfTime"));
	const FName VfxDirectorConsumed(TEXT("Consumed"));
	const FName VfxDirectorShaftKey(TEXT("LightShaft"));
	const FName VfxDirectorUmbraKey(TEXT("Umbra"));
	const FName VfxDirectorChannelKey(TEXT("NeedleChannel"));

	bool IsVfxFamilyEnabled(EVfxFamily Family)
	{
		if (!IsFeatureEnabled(EFeatureId::VFX_02))
		{
			return false;
		}
		switch (Family)
		{
		case EVfxFamily::Weapon:
			return IsFeatureEnabled(EFeatureId::VFX_03);
		case EVfxFamily::Keeper:
			return IsFeatureEnabled(EFeatureId::VFX_05);
		case EVfxFamily::Story:
			return IsFeatureEnabled(EFeatureId::NAR_05);
		default:
			return false;
		}
	}

	/** The Detail the projectile service stamps on a player shot's spawn event (the enum's own name). */
	FName VfxDirectorPlayerBlastName()
	{
		return StaticEnum<EUmbrellaShotKind>()->GetNameByValue(static_cast<int64>(EUmbrellaShotKind::PlayerBlast));
	}

	bool IsVfxIlluminationFlagOn()
	{
		return IsFeatureEnabled(EFeatureId::VFX_07) && IsFeatureEnabled(EFeatureId::VFX_08);
	}
}

bool UUmbrellaVfxDirectorSubsystem::DoesSupportWorldType(EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId UUmbrellaVfxDirectorSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UUmbrellaVfxDirectorSubsystem, STATGROUP_Tickables);
}

void UUmbrellaVfxDirectorSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Collection.InitializeDependency<UUmbrellaEventBus>();
	Super::Initialize(Collection);
#if !UE_BUILD_SHIPPING
	FString DemoValue;
	if (FParse::Value(FCommandLine::Get(), TEXT("VfxDemo="), DemoValue))
	{
		DemoKey = FName(*DemoValue);
	}
#endif
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		Handles.Add(Bus->On(EUmbrellaEventType::ProjectileSpawned).AddUObject(this, &UUmbrellaVfxDirectorSubsystem::HandleProjectileSpawned));
		Handles.Add(Bus->On(EUmbrellaEventType::ProjectileContact).AddUObject(this, &UUmbrellaVfxDirectorSubsystem::HandleProjectileContact));
		Handles.Add(Bus->On(EUmbrellaEventType::UmbrellaConfigChanged).AddUObject(this, &UUmbrellaVfxDirectorSubsystem::HandleConfigChanged));
		Handles.Add(Bus->On(EUmbrellaEventType::BossTargetHit).AddUObject(this, &UUmbrellaVfxDirectorSubsystem::HandleBossTargetHit));
		Handles.Add(Bus->On(EUmbrellaEventType::BossAttackTelegraphed).AddUObject(this, &UUmbrellaVfxDirectorSubsystem::HandleBossTelegraph));
		Handles.Add(Bus->On(EUmbrellaEventType::BossPartDestroyed).AddUObject(this, &UUmbrellaVfxDirectorSubsystem::HandleBossPartDestroyed));
		Handles.Add(Bus->On(EUmbrellaEventType::CheckpointRetried).AddUObject(this, &UUmbrellaVfxDirectorSubsystem::HandleReset));
		Handles.Add(Bus->On(EUmbrellaEventType::PlayerDefeated).AddUObject(this, &UUmbrellaVfxDirectorSubsystem::HandleReset));
		Handles.Add(Bus->On(EUmbrellaEventType::PhaseStarted).AddUObject(this, &UUmbrellaVfxDirectorSubsystem::HandleReset));
	}
}

void UUmbrellaVfxDirectorSubsystem::Deinitialize()
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		const EUmbrellaEventType Types[] = { EUmbrellaEventType::ProjectileSpawned, EUmbrellaEventType::ProjectileContact,
			EUmbrellaEventType::UmbrellaConfigChanged, EUmbrellaEventType::BossTargetHit, EUmbrellaEventType::BossAttackTelegraphed,
			EUmbrellaEventType::BossPartDestroyed, EUmbrellaEventType::CheckpointRetried, EUmbrellaEventType::PlayerDefeated,
			EUmbrellaEventType::PhaseStarted };
		for (int32 Index = 0; Index < Handles.Num() && Index < UE_ARRAY_COUNT(Types); ++Index)
		{
			Bus->On(Types[Index]).Remove(Handles[Index]);
		}
	}
	Handles.Reset();
	StopAll();
	Super::Deinitialize();
}

void UUmbrellaVfxDirectorSubsystem::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	StepEffects(DeltaTime);
}

bool UUmbrellaVfxDirectorSubsystem::IsDirectorEvent(const FUmbrellaEvent& Event)
{
	switch (Event.Type)
	{
	case EUmbrellaEventType::ProjectileSpawned:
		return IsVfxFamilyEnabled(EVfxFamily::Weapon) && Event.Detail == VfxDirectorPlayerBlastName();
	case EUmbrellaEventType::ProjectileContact:
		return IsVfxFamilyEnabled(EVfxFamily::Weapon) && Event.SourceId == UmbrellaPlayerIds::Ella;
	case EUmbrellaEventType::BossTargetHit:
	case EUmbrellaEventType::BossAttackTelegraphed:
	case EUmbrellaEventType::BossPartDestroyed:
		return IsVfxFamilyEnabled(EVfxFamily::Keeper) && Event.SourceId == VfxDirectorKeeperSource;
	default:
		return false;
	}
}

// ---- Playing and stopping ----

int32 UUmbrellaVfxDirectorSubsystem::Play(FName Key, const FVector& Location, AActor* Follow)
{
	const FVfxArtRow* Row = VfxCatalog::Find(Key);
	UWorld* World = GetWorld();
	if (!Row || !IsValid(World) || !IsVfxFamilyEnabled(Row->Family))
	{
		return 0;
	}
	const bool bLimits = IsFeatureEnabled(EFeatureId::VFX_10);
	if (bLimits && !Row->bLoop && Live.Num() >= UmbrellaVfxDirectorConst::MaxLive)
	{
		++DroppedCount;
		return 0;
	}
	// A flash too soon after the last one is still shown (it may carry a hit or a warning) but throws no light.
	bool bLightAllowed = bIllumination && IsVfxIlluminationFlagOn();
	if (Row->bFlashing)
	{
		if (bLimits && Clock - LastFlashClock < UmbrellaVfxConst::MinFlashGapSeconds)
		{
			bLightAllowed = false;
			++FlashDimmedCount;
		}
		else
		{
			LastFlashClock = Clock;
		}
	}
	const float LayerY = IsFeatureEnabled(EFeatureId::VFX_06) ? VfxCatalog::RowY(*Row) : VfxCatalog::LayerY(EVfxLayer::Vfx);
	const FVector At(Location.X, LayerY, Location.Z);
	AActor* Actor = World->SpawnActor<AActor>(At, FRotator::ZeroRotator);
	if (!IsValid(Actor))
	{
		return 0;
	}
	VfxSheetVisual::Build(Actor, *Row, FVector2D(Row->Size, Row->Size));
	Actor->SetActorLocation(At);

	FVfxLiveEffect Effect;
	Effect.Serial = NextSerial;
	++NextSerial;
	Effect.Key = Key;
	Effect.Row = Row;
	Effect.Actor = Actor;
	Effect.StartClock = Clock;
	if (IsValid(Follow))
	{
		Effect.Follow = Follow;
		Effect.bFollows = true;
		Effect.FollowOffset = Location - Follow->GetActorLocation();
	}
	const FVfxLightPlan Plan = VfxLightPolicy::PlanFor(*Row, bLightAllowed, bReducedFlash && bLimits);
	Effect.Light = VfxSheetVisual::AddLight(Actor, Plan);
	Effect.Spill = VfxSheetVisual::AddSpill(Actor, Plan);
	Effect.LightIntensity = Plan.Intensity;
	Effect.SpillOpacity = Plan.SpillOpacity;
	Live.Add(Effect);
	PlayCounts.FindOrAdd(Key) += 1;
	LastLocations.Add(Key, At);
	return Effect.Serial;
}

int32 UUmbrellaVfxDirectorSubsystem::PlayAnchored(FName Key, EKeeperVfxAnchor Anchor)
{
	const int32 Serial = Play(Key, KeeperAnchorLocation(Anchor), nullptr);
	if (FVfxLiveEffect* Effect = FindSerial(Serial))
	{
		Effect->bKeeperAnchored = true;
		Effect->Anchor = Anchor;
		if (Anchor == EKeeperVfxAnchor::Screen)
		{
			VfxSheetVisual::Resize(Cast<UStaticMeshComponent>(Effect->Actor->GetRootComponent()),
				FVector2D(UmbrellaVfxDirectorConst::ScreenCover, UmbrellaVfxDirectorConst::ScreenCover));
		}
	}
	return Serial;
}

void UUmbrellaVfxDirectorSubsystem::DestroyEffect(FVfxLiveEffect& Effect) const
{
	if (AActor* Actor = Effect.Actor.Get())
	{
		Actor->Destroy();
	}
	Effect.Actor.Reset();
}

void UUmbrellaVfxDirectorSubsystem::Stop(FName Key)
{
	for (int32 Index = Live.Num() - 1; Index >= 0; --Index)
	{
		if (Live[Index].Key == Key)
		{
			DestroyEffect(Live[Index]);
			Live.RemoveAt(Index);
		}
	}
}

void UUmbrellaVfxDirectorSubsystem::StopSerial(int32 Serial)
{
	for (int32 Index = Live.Num() - 1; Index >= 0; --Index)
	{
		if (Live[Index].Serial == Serial)
		{
			DestroyEffect(Live[Index]);
			Live.RemoveAt(Index);
		}
	}
}

void UUmbrellaVfxDirectorSubsystem::StopAll()
{
	for (FVfxLiveEffect& Effect : Live)
	{
		DestroyEffect(Effect);
	}
	Live.Reset();
	Shots.Reset();
	bStreaming = false;
	StreamSerial = 0;
	ChannelSerial = 0;
	for (TWeakObjectPtr<AActor>& Part : ShaftActors)
	{
		if (AActor* Actor = Part.Get())
		{
			Actor->Destroy();
		}
		Part.Reset();
	}
}

void UUmbrellaVfxDirectorSubsystem::StopFamilyHeld()
{
	for (const FName Key : KeeperVfxRules::HeldKeys())
	{
		Stop(Key);
	}
}

FVfxLiveEffect* UUmbrellaVfxDirectorSubsystem::FindSerial(int32 Serial)
{
	if (Serial <= 0)
	{
		return nullptr;
	}
	for (FVfxLiveEffect& Effect : Live)
	{
		if (Effect.Serial == Serial)
		{
			return &Effect;
		}
	}
	return nullptr;
}

int32 UUmbrellaVfxDirectorSubsystem::GetPlayCount(FName Key) const
{
	const int32* Count = PlayCounts.Find(Key);
	return Count ? *Count : 0;
}

int32 UUmbrellaVfxDirectorSubsystem::GetLiveCount(FName Key) const
{
	int32 Count = 0;
	for (const FVfxLiveEffect& Effect : Live)
	{
		Count += (Effect.Key == Key && Effect.Actor.IsValid()) ? 1 : 0;
	}
	return Count;
}

FVector UUmbrellaVfxDirectorSubsystem::GetLastLocation(FName Key) const
{
	const FVector* Location = LastLocations.Find(Key);
	return Location ? *Location : FVector::ZeroVector;
}

AActor* UUmbrellaVfxDirectorSubsystem::GetLiveActor(FName Key) const
{
	for (int32 Index = Live.Num() - 1; Index >= 0; --Index)
	{
		if (Live[Index].Key == Key && Live[Index].Actor.IsValid())
		{
			return Live[Index].Actor.Get();
		}
	}
	return nullptr;
}

AActor* UUmbrellaVfxDirectorSubsystem::GetShaftPart(int32 Index) const
{
	return (Index >= 0 && Index < UmbrellaVfxDirectorConst::ShaftParts) ? ShaftActors[Index].Get() : nullptr;
}

void UUmbrellaVfxDirectorSubsystem::SetIlluminationEnabled(bool bEnabled)
{
	bIllumination = bEnabled;
	for (FVfxLiveEffect& Effect : Live)
	{
		if (UPointLightComponent* Light = Effect.Light.Get())
		{
			Light->SetVisibility(bEnabled);
		}
		if (UStaticMeshComponent* Spill = Effect.Spill.Get())
		{
			Spill->SetVisibility(bEnabled);
		}
	}
}

// ---- Bus events ----

void UUmbrellaVfxDirectorSubsystem::HandleConfigChanged(const FUmbrellaEvent& Event)
{
	if (Event.SourceId != UmbrellaPlayerIds::Ella)
	{
		return;
	}
	for (int32 Index = 0; Index < SpellRules::SpellCount; ++Index)
	{
		const EUmbrellaSpell Spell = static_cast<EUmbrellaSpell>(Index);
		if (Event.Detail == SpellRules::SpellName(Spell))
		{
			// Equipping cancels the old spell's held effects at once.
			Equipped = Spell;
			StopSerial(ChannelSerial);
			ChannelSerial = 0;
			return;
		}
	}
	const EUmbrellaAction Actions[] = { EUmbrellaAction::Rise, EUmbrellaAction::ShootFall, EUmbrellaAction::AbsorbFall, EUmbrellaAction::FreeFall };
	for (const EUmbrellaAction Action : Actions)
	{
		if (Event.Detail == UmbrellaActionRules::ActionName(Action))
		{
			EllaAction = Action;
			return;
		}
	}
}

void UUmbrellaVfxDirectorSubsystem::HandleProjectileSpawned(const FUmbrellaEvent& Event)
{
	UWorld* World = GetWorld();
	if (!IsValid(World))
	{
		return;
	}
	if (Event.SourceId == UmbrellaSourceIds::ClockDoubleBeat() && IsVfxFamilyEnabled(EVfxFamily::Keeper))
	{
		// One beat effect per beat, not per shot of the beat.
		const FKeeperTuning& Keeper = GetDefault<UUmbrellaTuning>()->Keeper;
		if (KeeperVfxRules::IsNewBeat(Clock - LastBeatShotClock, Keeper.RedSpacingSeconds, Keeper.BeatRepeatWaitSeconds))
		{
			Play(TEXT("ClockBeat"), KeeperAnchorLocation(EKeeperVfxAnchor::Clock), nullptr);
		}
		LastBeatShotClock = Clock;
		return;
	}
	if (!IsDirectorEvent(Event))
	{
		return;
	}
	// The event fires right after the shot exists: every player shot not yet followed is new.
	for (TActorIterator<AUmbrellaProjectile> It(World); It; ++It)
	{
		AUmbrellaProjectile* Shot = *It;
		if (!IsValid(Shot) || Shot->GetSpec().Kind != EUmbrellaShotKind::PlayerBlast)
		{
			continue;
		}
		const bool bKnown = Shots.ContainsByPredicate([Shot](const FVfxTrackedShot& Entry) { return Entry.Shot.Get() == Shot; });
		if (bKnown)
		{
			continue;
		}
		FVfxTrackedShot Tracked;
		Tracked.Shot = Shot;
		Tracked.Spell = Equipped;
		Tracked.LastLocation = Shot->GetActorLocation();
		// Release at the shot's own origin: Twin Stars' two shots give two anchors.
		Play(VfxCatalog::WeaponKey(Equipped, EVfxWeaponStage::Release), Tracked.LastLocation, nullptr);
		Tracked.TravelSerial = Play(VfxCatalog::WeaponKey(Equipped, EVfxWeaponStage::Travel), Tracked.LastLocation, Shot);
		Shots.Add(Tracked);
	}
}

void UUmbrellaVfxDirectorSubsystem::HandleProjectileContact(const FUmbrellaEvent& Event)
{
	UWorld* World = GetWorld();
	if (!IsValid(World) || !IsDirectorEvent(Event))
	{
		return;
	}
	const AActor* Target = FindActorNamed(Event.TargetId);
	const FBox TargetBox = IsValid(Target) ? Target->GetComponentsBoundingBox(true) : FBox(ForceInit);
	// Which of our shots touched it: the nearest live one.
	FVfxTrackedShot* Nearest = nullptr;
	double NearestDistance = TNumericLimits<double>::Max();
	for (FVfxTrackedShot& Tracked : Shots)
	{
		const AUmbrellaProjectile* Shot = Tracked.Shot.Get();
		if (!IsValid(Shot) || Tracked.bConsumed)
		{
			continue;
		}
		const double Distance = TargetBox.IsValid ? TargetBox.ComputeSquaredDistanceToPoint(Shot->GetActorLocation()) : 0.0;
		if (Distance < NearestDistance)
		{
			NearestDistance = Distance;
			Nearest = &Tracked;
		}
	}
	// A live beam that reaches the target wins unless a shot is actually touching it.
	const bool bShotTouches = Nearest && NearestDistance <= FMath::Square(static_cast<double>(Nearest->Shot->GetSpec().Radius));
	const bool bFromStream = bStreaming && !bShotTouches;
	EUmbrellaSpell Spell = Equipped;
	FVector Location = IsValid(Target) ? Target->GetActorLocation() : FVector::ZeroVector;
	if (bFromStream)
	{
		Spell = EUmbrellaSpell::StreamedBlast;
		Location = StreamEnd;
		if (TargetBox.IsValid)
		{
			Location.X = FMath::Min(static_cast<double>(StreamEnd.X), TargetBox.Min.X);
		}
	}
	else if (Nearest)
	{
		Spell = Nearest->Spell;
		Location = Nearest->Shot->GetActorLocation();
	}
	const bool bConsumed = Event.Detail == VfxDirectorConsumed;
	const bool bKeeperTarget = IsValid(Target) && Target->IsA<AKeeperOfTime>();
	const bool bKeeperDamaged = BossHitFrame == Event.Frame;
	LastContactLocation = Location;
	ContactFrame = Event.Frame;
	// The hit event belongs to this contact only.
	BossHitFrame = -1;
	if (!bConsumed)
	{
		// Passing through: only the Needle shows it (its valid penetration). Other spells' shots just fly on.
		Play(VfxCatalog::WeaponKey(Spell, EVfxWeaponStage::Pierce), Location, nullptr);
		return;
	}
	if (Nearest && !bFromStream)
	{
		Nearest->bConsumed = true;
	}
	// Exactly one effect per contact: a damaged Keeper part, a protected part, or the weapon's own impact.
	if (bKeeperTarget && bKeeperDamaged && IsVfxFamilyEnabled(EVfxFamily::Keeper))
	{
		Play(TEXT("KeeperPartHit"), Location, nullptr);
	}
	else if (bKeeperTarget && !bKeeperDamaged)
	{
		Play(VfxCatalog::ProtectedContactKey(), Location, nullptr);
	}
	else
	{
		Play(VfxCatalog::WeaponKey(Spell, EVfxWeaponStage::Impact), Location, nullptr);
	}
}

void UUmbrellaVfxDirectorSubsystem::HandleBossTargetHit(const FUmbrellaEvent& Event)
{
	if (Event.SourceId == VfxDirectorKeeperSource)
	{
		// The contact event of the same shot follows in the same frame and places the effect at the hit.
		BossHitFrame = Event.Frame;
	}
}

void UUmbrellaVfxDirectorSubsystem::HandleBossTelegraph(const FUmbrellaEvent& Event)
{
	if (!IsDirectorEvent(Event))
	{
		return;
	}
	const EKeeperPhysical Physical = KeeperVfxRules::PhysicalForAttack(Event.Detail);
	const FName Key = KeeperVfxRules::WarningKey(Physical);
	if (!Key.IsNone() && GetLiveCount(Key) == 0)
	{
		PlayAnchored(Key, KeeperVfxRules::AnchorFor(Physical));
	}
}

void UUmbrellaVfxDirectorSubsystem::HandleBossPartDestroyed(const FUmbrellaEvent& Event)
{
	if (!IsDirectorEvent(Event))
	{
		return;
	}
	const FVector Location = (ContactFrame == Event.Frame) ? LastContactLocation : KeeperAnchorLocation(EKeeperVfxAnchor::Body);
	Play(TEXT("KeeperPartBroken"), Location, nullptr);
}

void UUmbrellaVfxDirectorSubsystem::HandleReset(const FUmbrellaEvent& Event)
{
	// Retry, defeat and a new phase clear what was held. Broken parts are the model's business: nothing is restored here.
	StopFamilyHeld();
	if (Event.Type != EUmbrellaEventType::PhaseStarted)
	{
		StopAll();
	}
	KeeperBefore = FKeeperVfxSnapshot();
}

// ---- Stepping ----

void UUmbrellaVfxDirectorSubsystem::StepEffects(float DeltaSeconds)
{
	Clock += FMath::Max(DeltaSeconds, 0.0f);
	StepShots();
	StepStream();
	StepNeedleChannel();
	StepKeeper();
	StepShaft(DeltaSeconds);
#if !UE_BUILD_SHIPPING
	StepDemo();
#endif
	StepLive();
}

#if !UE_BUILD_SHIPPING
void UUmbrellaVfxDirectorSubsystem::SpawnDemoBackdrop(const FVector& Around)
{
	UWorld* World = GetWorld();
	UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/UmbrellaElla/Materials/M_ArtSlot_Unlit.M_ArtSlot_Unlit"), nullptr, LOAD_NoWarn | LOAD_Quiet);
	UStaticMesh* Plane = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Plane.Plane"), nullptr, LOAD_NoWarn | LOAD_Quiet);
	UTexture* White = LoadObject<UTexture>(nullptr, TEXT("/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture"), nullptr, LOAD_NoWarn | LOAD_Quiet);
	if (!World || !Material || !Plane || !White)
	{
		DemoBackdrop = World ? World->SpawnActor<AActor>() : nullptr;   // nothing to draw; do not retry every step
		return;
	}
	AActor* Actor = World->SpawnActor<AActor>(Around, FRotator::ZeroRotator);
	UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Actor, TEXT("DemoBackdrop"));
	Mesh->SetStaticMesh(Plane);
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetCastShadow(false);
	UMaterialInstanceDynamic* Dynamic = UMaterialInstanceDynamic::Create(Material, Mesh);
	Dynamic->SetTextureParameterValue(TEXT("Art"), White);
	Dynamic->SetVectorParameterValue(TEXT("Tint"), UmbrellaVfxDirectorConst::DemoBackdropColour);
	Mesh->SetMaterial(0, Dynamic);
	Mesh->SetRelativeRotation(VfxSheetVisual::FacingCamera());
	Mesh->SetRelativeScale3D(FVector(UmbrellaVfxDirectorConst::DemoBackdropWidth, UmbrellaVfxDirectorConst::DemoBackdropHeight, 1.0f) / VfxSheetVisual::ShapeEdge);
	Actor->SetRootComponent(Mesh);
	Mesh->RegisterComponent();
	DemoBackdrop = Actor;
}

// Art capture only: the effect sits at the middle of the view (the camera's X and Z), so a crop around it is never clipped by the frame edge.
FVector UUmbrellaVfxDirectorSubsystem::DemoCentre(const AActor* Player) const
{
	const APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(GetWorld(), 0);
	if (IsValid(Camera))
	{
		const FVector Cam = Camera->GetCameraLocation();
		return FVector(Cam.X, 0.0f, Cam.Z);
	}
	return Player->GetActorLocation() + FVector(UmbrellaVfxDirectorConst::DemoOffsetX, 0.0f, UmbrellaVfxDirectorConst::DemoOffsetZ);
}

void UUmbrellaVfxDirectorSubsystem::StepDemo()
{
	if (DemoKey.IsNone())
	{
		return;
	}
	AActor* Player = FindElla();
	if (!Player)
	{
		return;
	}
	// Wall time on purpose: art capture only, non-shipping; game time crawls while shaders compile.
	const double Now = FApp::GetCurrentTime();
	if (DemoStartSeconds < 0.0)
	{
		DemoStartSeconds = Now;
	}
	if (!DemoBackdrop.IsValid())
	{
		// The capture is of the effect on paper: Ella's and the Keeper's dark stand-ins would be mistaken for it by the piece locator.
		Player->SetActorHiddenInGame(true);
		// Zoomed capture: the camera moves closer (a narrower orthographic view); the effect itself is never scaled.
		for (TActorIterator<AUmbrellaArena> ArenaIt(GetWorld()); ArenaIt; ++ArenaIt)
		{
			if (UCameraComponent* PlayCam = ArenaIt->GetPlayCamera())
			{
				PlayCam->SetOrthoWidth(UmbrellaVfxDirectorConst::DemoZoomedOrthoWidth);
			}
		}
		for (TActorIterator<AKeeperOfTime> It(GetWorld()); It; ++It)
		{
			It->SetActorHiddenInGame(true);
		}
		// Just behind the effect's own layer: the scene art (bg, arena) now draws at the depths the old backdrop used and would hide it.
		const FVfxArtRow* DemoRow = VfxCatalog::Find(DemoKey);
		const float DemoLayerY = DemoRow ? VfxCatalog::RowY(*DemoRow) : UmbrellaDrawOrder::VfxY;
		SpawnDemoBackdrop(FVector(DemoCentre(Player).X, DemoLayerY - UmbrellaVfxDirectorConst::DemoBackdropDepth, DemoCentre(Player).Z));
	}
	const int32 LiveOfKey = GetLiveCount(DemoKey);
	if (!bDemoShotTaken && Now - DemoStartSeconds >= UmbrellaVfxDirectorConst::DemoShotSeconds && LiveOfKey > 0)
	{
		bDemoShotTaken = true;
		FScreenshotRequest::RequestScreenshot(FString(), false, false);
	}
	if (UmbrellaVfxDirectorConst::ShouldPlayDemo(DemoKey, LiveOfKey))
	{
		Play(DemoKey, DemoCentre(Player), nullptr);
	}
}
#endif

void UUmbrellaVfxDirectorSubsystem::StepShots()
{
	for (int32 Index = Shots.Num() - 1; Index >= 0; --Index)
	{
		FVfxTrackedShot& Tracked = Shots[Index];
		if (const AUmbrellaProjectile* Shot = Tracked.Shot.Get())
		{
			Tracked.LastLocation = Shot->GetActorLocation();
			continue;
		}
		// The shot is gone: its head stops. If nothing consumed it, it ran out of range and fades.
		StopSerial(Tracked.TravelSerial);
		if (!Tracked.bConsumed)
		{
			Play(VfxCatalog::WeaponKey(Tracked.Spell, EVfxWeaponStage::Fade), Tracked.LastLocation, nullptr);
		}
		Shots.RemoveAt(Index);
	}
}

void UUmbrellaVfxDirectorSubsystem::StepStream()
{
	UWorld* World = GetWorld();
	const AStreamBeamActor* Beam = nullptr;
	if (IsValid(World) && IsVfxFamilyEnabled(EVfxFamily::Weapon))
	{
		for (TActorIterator<AStreamBeamActor> It(World); It && !Beam; ++It)
		{
			Beam = IsValid(*It) ? *It : nullptr;
		}
	}
	if (!Beam)
	{
		if (bStreaming)
		{
			// Released, cancelled or re-equipped: the beam stops where it ended.
			StopSerial(StreamSerial);
			StreamSerial = 0;
			bStreaming = false;
			Play(VfxCatalog::WeaponKey(EUmbrellaSpell::StreamedBlast, EVfxWeaponStage::Fade), StreamEnd, nullptr);
		}
		return;
	}
	const FVector Muzzle = Beam->GetMuzzle();
	const float Length = Beam->GetEffectiveLength();
	StreamEnd = Muzzle + FVector(Length, 0.0, 0.0);
	if (!bStreaming)
	{
		bStreaming = true;
		Play(VfxCatalog::WeaponKey(EUmbrellaSpell::StreamedBlast, EVfxWeaponStage::Release), Muzzle, nullptr);
		StreamSerial = Play(VfxCatalog::WeaponKey(EUmbrellaSpell::StreamedBlast, EVfxWeaponStage::Sustain), Muzzle, nullptr);
	}
	if (FVfxLiveEffect* Sustain = FindSerial(StreamSerial))
	{
		if (AActor* Actor = Sustain->Actor.Get())
		{
			// The beam art covers exactly the hitbox: its length, and its core the width.
			const FVector Centre = Muzzle + FVector(Length * 0.5f, 0.0, 0.0);
			Actor->SetActorLocation(FVector(Centre.X, Actor->GetActorLocation().Y, Centre.Z));
			VfxSheetVisual::Resize(Cast<UStaticMeshComponent>(Actor->GetRootComponent()),
				FVector2D(FMath::Max(Length, AStreamBeamActor::MinVisualLength), Beam->GetWidth() / UmbrellaVfxDirectorConst::BeamCoreFraction));
		}
	}
}

void UUmbrellaVfxDirectorSubsystem::StepNeedleChannel()
{
	AActor* EllaActor = FindElla();
	const bool bChannel = IsValid(EllaActor) && Equipped == EUmbrellaSpell::Needle && EllaAction == EUmbrellaAction::ShootFall
		&& IsVfxFamilyEnabled(EVfxFamily::Weapon);
	if (bChannel && !FindSerial(ChannelSerial))
	{
		const FVector Muzzle = EllaActor->GetActorLocation() + GetDefault<UUmbrellaTuning>()->Attack.MuzzleOffset;
		ChannelSerial = Play(VfxDirectorChannelKey, Muzzle, EllaActor);
	}
	else if (!bChannel && ChannelSerial != 0)
	{
		StopSerial(ChannelSerial);
		ChannelSerial = 0;
	}
}

void UUmbrellaVfxDirectorSubsystem::StepKeeper()
{
	const UWorld* World = GetWorld();
	const UEncounterDirectorSubsystem* Director = IsValid(World) ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr;
	if (!Director || !IsVfxFamilyEnabled(EVfxFamily::Keeper))
	{
		return;
	}
	const AKeeperOfTime* Keeper = Director->GetKeeper();
	const bool bDeparting = IsValid(Keeper) && Keeper->IsDeparting();
	const FKeeperVfxSnapshot After = KeeperVfxRules::Read(Director->GetModel(), IsValid(Keeper) && !bDeparting, bDeparting);
	TArray<FKeeperVfxCue> Cues;
	KeeperVfxRules::Diff(KeeperBefore, After, Cues);
	KeeperBefore = After;
	for (const FKeeperVfxCue& Cue : Cues)
	{
		if (!Cue.bStart)
		{
			Stop(Cue.Key);
		}
		else if (GetLiveCount(Cue.Key) == 0)
		{
			PlayAnchored(Cue.Key, Cue.Anchor);
		}
	}
}

void UUmbrellaVfxDirectorSubsystem::StepShaft(float DeltaSeconds)
{
	UWorld* World = GetWorld();
	AActor* EllaActor = FindElla();
	const FVfxArtRow* ShaftRow = VfxCatalog::Find(VfxDirectorShaftKey);
	const FVfxArtRow* UmbraRow = VfxCatalog::Find(VfxDirectorUmbraKey);
	if (!IsValid(World) || !IsValid(EllaActor) || !ShaftRow || !UmbraRow || !IsVfxFamilyEnabled(EVfxFamily::Story))
	{
		for (TWeakObjectPtr<AActor>& Part : ShaftActors)
		{
			if (AActor* Actor = Part.Get())
			{
				Actor->Destroy();
			}
			Part.Reset();
		}
		return;
	}
	UmbraOpenness = LightShaftRules::StepOpenness(UmbraOpenness, LightShaftRules::IsUmbrellaOpen(EllaAction), DeltaSeconds);
	const FVector At = EllaActor->GetActorLocation();
	const FVector Centres[UmbrellaVfxDirectorConst::ShaftParts] = { LightShaftRules::ShaftAboveCentre(At), LightShaftRules::ShaftBelowCentre(At),
		LightShaftRules::UmbraCentre(At) };
	const FVector2D Sizes[UmbrellaVfxDirectorConst::ShaftParts] = { FVector2D(LightShaftRules::ShaftWidth, LightShaftRules::ShaftLength),
		FVector2D(LightShaftRules::ShaftWidth, LightShaftRules::ShaftLength),
		FVector2D(LightShaftRules::UmbraWidthAt(UmbraOpenness), LightShaftRules::UmbraLength) };
	const float Opacities[UmbrellaVfxDirectorConst::ShaftParts] = { 1.0f, LightShaftRules::LightBelowAt(UmbraOpenness), UmbraOpenness };
	for (int32 Index = 0; Index < UmbrellaVfxDirectorConst::ShaftParts; ++Index)
	{
		const FVfxArtRow* Row = (Index == UmbrellaVfxDirectorConst::ShaftParts - 1) ? UmbraRow : ShaftRow;
		const FVector Location(Centres[Index].X, VfxCatalog::RowY(*Row), Centres[Index].Z);
		AActor* Part = ShaftActors[Index].Get();
		if (!IsValid(Part))
		{
			Part = World->SpawnActor<AActor>(Location, FRotator::ZeroRotator);
			if (!IsValid(Part))
			{
				continue;
			}
			VfxSheetVisual::Build(Part, *Row, Sizes[Index]);
			ShaftActors[Index] = Part;
		}
		UStaticMeshComponent* Visual = Cast<UStaticMeshComponent>(Part->GetRootComponent());
		Part->SetActorLocation(Location);
		VfxSheetVisual::Resize(Visual, Sizes[Index]);
		VfxSheetVisual::SetOpacity(Visual, Opacities[Index]);
		VfxSheetVisual::SetFrame(Visual, VfxCatalog::FrameAt(*Row, Clock));
		Part->SetActorHiddenInGame(Opacities[Index] <= 0.0f);
	}
}

void UUmbrellaVfxDirectorSubsystem::StepLive()
{
	for (int32 Index = Live.Num() - 1; Index >= 0; --Index)
	{
		FVfxLiveEffect& Effect = Live[Index];
		AActor* Actor = Effect.Actor.Get();
		const float Elapsed = Clock - Effect.StartClock;
		const bool bLostFollow = Effect.bFollows && !Effect.Follow.IsValid();
		const bool bExpired = VfxCatalog::IsFinished(*Effect.Row, Elapsed) || (Effect.Row->bLoop && Elapsed >= UmbrellaVfxDirectorConst::MaxHeldSeconds);
		if (!IsValid(Actor) || bLostFollow || bExpired)
		{
			DestroyEffect(Effect);
			Live.RemoveAt(Index);
			continue;
		}
		FVector At = Actor->GetActorLocation();
		if (const AActor* Follow = Effect.Follow.Get())
		{
			const FVector Target = Follow->GetActorLocation() + Effect.FollowOffset;
			At = FVector(Target.X, At.Y, Target.Z);
		}
		else if (Effect.bKeeperAnchored)
		{
			const FVector Target = KeeperAnchorLocation(Effect.Anchor);
			At = FVector(Target.X, At.Y, Target.Z);
		}
		Actor->SetActorLocation(At);
		int32 ShownFrame = VfxCatalog::FrameAt(*Effect.Row, Elapsed);
#if !UE_BUILD_SHIPPING
		if (!DemoKey.IsNone() && Effect.Key == DemoKey)
		{
			// Art capture only: hold one frame so the shot never lands on a faded or empty one.
			ShownFrame = FMath::Min(UmbrellaVfxDirectorConst::DemoHoldFrame, FMath::Max(Effect.Row->Frames - 1, 0));
		}
#endif
		VfxSheetVisual::SetFrame(Cast<UStaticMeshComponent>(Actor->GetRootComponent()), ShownFrame);
		// The light fades with the effect and leaves with it: surfaces return to their normal look.
		const float Fade = VfxLightPolicy::FadeAt(*Effect.Row, Elapsed);
		if (UPointLightComponent* Light = Effect.Light.Get())
		{
			Light->SetIntensity(Effect.LightIntensity * Fade);
		}
		if (UStaticMeshComponent* Spill = Effect.Spill.Get())
		{
			Spill->SetWorldLocation(FVector(At.X, VfxLightPolicy::SpillLayerY(), At.Z));
			VfxSheetVisual::SetOpacity(Spill, Effect.SpillOpacity * Fade);
		}
	}
}

// ---- Readers ----

FVector UUmbrellaVfxDirectorSubsystem::KeeperAnchorLocation(EKeeperVfxAnchor Anchor) const
{
	const UWorld* World = GetWorld();
	const UEncounterDirectorSubsystem* Director = IsValid(World) ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr;
	const AKeeperOfTime* Keeper = Director ? Director->GetKeeper() : nullptr;
	if (!IsValid(Keeper))
	{
		return FVector::ZeroVector;
	}
	const FKeeperFightModel& Model = Director->GetModel();
	switch (Anchor)
	{
	case EKeeperVfxAnchor::Head:
		return FVector(Model.GetHeadPosition().X, 0.0, Model.GetHeadPosition().Y);
	case EKeeperVfxAnchor::Claw:
		return FVector(Model.GetClaw().X, 0.0, Model.GetClaw().Y);
	case EKeeperVfxAnchor::GustFront:
		return FVector(Model.GetGustFront().X, 0.0, Model.GetGustFront().Y);
	case EKeeperVfxAnchor::Clock:
		if (const UKeeperPartComponent* ClockPart = Keeper->GetPartComponent(EKeeperPart::Clock))
		{
			return ClockPart->GetComponentLocation();
		}
		return Keeper->GetActorLocation();
	case EKeeperVfxAnchor::Screen:
		if (const APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(World, 0))
		{
			return Camera->GetCameraLocation();
		}
		return Keeper->GetActorLocation();
	case EKeeperVfxAnchor::Body:
	default:
		return Keeper->GetActorLocation();
	}
}

AActor* UUmbrellaVfxDirectorSubsystem::FindElla()
{
	if (!Ella.IsValid())
	{
		UWorld* World = GetWorld();
		if (IsValid(World))
		{
			TActorIterator<AEllaCharacter> It(World);
			if (It)
			{
				Ella = *It;
			}
		}
	}
	return Ella.Get();
}

AActor* UUmbrellaVfxDirectorSubsystem::FindActorNamed(FName Id) const
{
	UWorld* World = GetWorld();
	if (IsValid(World) && !Id.IsNone())
	{
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (It->GetFName() == Id)
			{
				return *It;
			}
		}
	}
	return nullptr;
}
