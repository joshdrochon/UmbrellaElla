#include "BrokenMill/BrokenMillRoom.h"
#include "BrokenMill/BrokenMillIsland.h"
#include "BrokenMill/BrokenMillPlaceholder.h"
#include "BrokenMill/BrokenMillTuning.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Core/UmbrellaCollision.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Enemy/EnemyRules.h"
#include "Engine/World.h"
#include "Field/WindCurrent.h"
#include "GameFramework/Pawn.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Trap/UmbrellaTrap.h"

ABrokenMillRoom::ABrokenMillRoom()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
	TargetBox = CreateDefaultSubobject<UBoxComponent>(TEXT("TargetBox"));
	TargetBox->SetupAttachment(Root);
	TargetBox->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	TargetBox->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
	GuardVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("GuardVisual"));
	GuardVisual->SetupAttachment(Root);
	GuardVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	TellVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TellVisual"));
	TellVisual->SetupAttachment(Root);
	TellVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	TellVisual->SetVisibility(false);
	GuardHp = Tuning().GuardHp;
}

FVector ABrokenMillRoom::RoomToWorld(const FVector2D& RoomPoint) const
{
	return GetActorTransform().TransformPosition(FVector(RoomPoint.X, UmbrellaDrawOrder::EllaY, RoomPoint.Y));
}

FVector2D ABrokenMillRoom::WorldToRoom(const FVector& WorldPoint) const
{
	const FVector Local = GetActorTransform().InverseTransformPosition(WorldPoint);
	return FVector2D(Local.X, Local.Z);
}

void ABrokenMillRoom::BuildRoom()
{
	if (!IsFeatureEnabled(EFeatureId::HAZ_02) || !IsFeatureEnabled(EFeatureId::HAZ_03) || IsValid(Rotor))
	{
		return;
	}
	const FBrokenMillTuning& T = Tuning();
	if (FParse::Param(FCommandLine::Get(), TEXT("MillGuardComparison")))
	{
		SetGuardProfile(EMillGuardProfile::Comparison);
	}
	// The target sits at the shared target centre in the room frame.
	TargetBox->SetBoxExtent(FVector(T.TargetSize.X * 0.5, T.DepthHalfExtent, T.TargetSize.Y * 0.5));
	TargetBox->SetRelativeLocation(FVector(T.TargetCentre.X, 0.0, T.TargetCentre.Y));
	BrokenMillPlaceholder::ApplyCube(GuardVisual, this, T.TargetSize, T.GuardColor, T.PlaceholderCubeSize, T.PlaceholderDepthScale);
	GuardVisual->SetRelativeLocation(FVector(T.TargetCentre.X, UmbrellaDrawOrder::HazardY, T.TargetCentre.Y));
	BrokenMillPlaceholder::ApplyCube(TellVisual, this, FVector2D(T.TellSize, T.TellSize), T.TellColor, T.PlaceholderCubeSize, T.PlaceholderDepthScale);
	if (UWorld* World = GetWorld())
	{
		// The island is its own actor with no shot receiver: a solid stop for both shot channels, never a guard hit.
		const float IslandWidth = T.IslandXRange.Y - T.IslandXRange.X;
		const float IslandHeight = T.IslandTop - T.IslandUnderside;
		// The solid stops a shot at IslandTop + IslandShotMargin (GDD shot margin); the drawn cube keeps the real top.
		const FVector2D IslandCentre(T.IslandXRange.X + IslandWidth * 0.5f, T.IslandUnderside + (IslandHeight + T.IslandShotMargin) * 0.5f);
		Island = World->SpawnActor<ABrokenMillIsland>(ABrokenMillIsland::StaticClass(), FTransform(RoomToWorld(IslandCentre)));
		if (IsValid(Island))
		{
			Island->ConfigureBox(FVector(IslandWidth * 0.5f, T.DepthHalfExtent, IslandHeight * 0.5f), T.IslandColor, T.PlaceholderCubeSize, T.PlaceholderDepthScale, T.IslandShotMargin);
		}
		Rotor = World->SpawnActor<AUmbrellaTrap>(AUmbrellaTrap::StaticClass(), FTransform(RoomToWorld(Tuning().RotorCentre)));
		if (IsValid(Rotor))
		{
			Rotor->ConfigureKind(ETrapKind::AirMill);
		}
	}
	BuildWinds();
}

void ABrokenMillRoom::BuildWinds()
{
	UWorld* World = GetWorld();
	if (!World || !IsFeatureEnabled(EFeatureId::HAZ_06) || IsValid(UpperWind))
	{
		return;
	}
	const FBrokenMillTuning& T = Tuning();
	auto SpawnBand = [&](const FVector2D& ZRange, const FVector& Direction) -> AWindCurrent*
	{
		const FVector2D Centre((T.FiringColumnX.X + T.FiringColumnX.Y) * 0.5f, (ZRange.X + ZRange.Y) * 0.5f);
		AWindCurrent* Wind = World->SpawnActor<AWindCurrent>(AWindCurrent::StaticClass(), FTransform(RoomToWorld(Centre)));
		if (IsValid(Wind))
		{
			Wind->SetHalfExtent((T.FiringColumnX.Y - T.FiringColumnX.X) * 0.5f, (ZRange.Y - ZRange.X) * 0.5f);
			Wind->SetCurrent(Direction, T.WindSpeed);
		}
		return Wind;
	};
	UpperWind = SpawnBand(T.UpperResetZ, FVector(-1.0, 0.0, 0.0));
	LowerWind = SpawnBand(T.LowerOnwardZ, FVector(1.0, 0.0, 0.0));
	if (IsValid(LowerWind))
	{
		// Local restoring field: pulls the root toward the onward centre z 230 while Ella rides this band.
		LowerWind->SetLocalVerticalField(T.LocalRestoringGain, RoomToWorld(FVector2D(0.0, T.LowerOnwardCentreZ)).Z, T.LocalVerticalCompensation);
	}
}

void ABrokenMillRoom::SetTargetActor(AActor* NewTarget)
{
	TargetActor = NewTarget;
}

void ABrokenMillRoom::DisableGuard()
{
	Guard.SetGuardEnabled(false);
}

void ABrokenMillRoom::SetGuardProfile(EMillGuardProfile NewProfile)
{
	Profile = NewProfile;
	GuardHp = FBrokenMillRules::GetGuardHp(Tuning(), Profile);
}

EMillTellPose ABrokenMillRoom::GetTellPose() const
{
	return FBrokenMillRules::GetTellPose(Guard.State, bLastReleaseAborted, GuardHp > 0.0f);
}

void ABrokenMillRoom::UpdateVisuals()
{
	const EMillTellPose Pose = GetTellPose();
	TellVisual->SetVisibility(Pose != EMillTellPose::Hidden);
	if (Pose != EMillTellPose::Hidden)
	{
		const FVector2D Offset = Pose == EMillTellPose::Raised ? Tuning().TellRaisedOffset : Tuning().TellLoweredOffset;
		const FVector2D Centre = Tuning().GuardMuzzle + Offset;
		TellVisual->SetRelativeLocation(FVector(Centre.X, UmbrellaDrawOrder::VfxY, Centre.Y));
	}
	GuardVisual->SetVisibility(GuardHp > 0.0f);
}

void ABrokenMillRoom::ResetForRestart()
{
	Guard.Reset();
	Guard.SetGuardEnabled(true);
	ShotLog.Entries.Reset();
	GuardHp = FBrokenMillRules::GetGuardHp(Tuning(), Profile);
	bLastReleaseAborted = false;
	ShotsFired = 0;
	Clock = 0.0f;
	EventCounts.Reset();
	SetActorHiddenInGame(false);
	TargetBox->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
	UpdateVisuals();
}

EUmbrellaShotResult ABrokenMillRoom::ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation)
{
	if (!FEnemyRules::IsDamagingShot(Shot) || GuardHp <= 0.0f)
	{
		return EUmbrellaShotResult::Ignored;
	}
	GuardHp = FMath::Max(0.0f, GuardHp - Shot.Damage);
	if (GuardHp <= 0.0f)
	{
		DisableGuard();
		TargetBox->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Ignore);
		UpdateVisuals();
		if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
		{
			FUmbrellaEvent Event;
			Event.Type = EUmbrellaEventType::BossPartDestroyed;
			Event.SourceId = GetFName();
			Event.TargetId = GetFName();
			Event.Detail = TEXT("Enemy");
			Event.Value = FBrokenMillRules::GetGuardHp(Tuning(), Profile);
			Bus->Broadcast(Event);
		}
	}
	return EUmbrellaShotResult::Consumed;
}

void ABrokenMillRoom::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bSimulationPaused && !UGameplayStatics::IsGamePaused(this))
	{
		StepSeconds(DeltaSeconds);
	}
}

EMillGuardEvent ABrokenMillRoom::StepSeconds(float DeltaSeconds)
{
	const bool bPaused = bSimulationPaused || UGameplayStatics::IsGamePaused(this);
	if (!bPaused)
	{
		Clock += DeltaSeconds;
	}
	const AActor* Found = TargetActor.Get();
	if (!IsValid(Found))
	{
		Found = UGameplayStatics::GetPlayerPawn(this, 0);
	}
	FMillGuardInputs Inputs;
	Inputs.bPaused = bPaused;
	Inputs.bShotGone = !ActiveShot.IsValid();
	if (IsValid(Found))
	{
		const FVector2D Ella = WorldToRoom(Found->GetActorLocation());
		Inputs.Ella = FVector(Ella.X, 0.0, Ella.Y);
		Inputs.bInActivationRegion = FBrokenMillRules::IsInActivationRegion(Tuning(), Inputs.Ella);
		Inputs.bEngagementValid = FBrokenMillRules::IsEngagementValid(Tuning(), Ella, true);
		Inputs.bPassedBehind = Ella.X > Tuning().GuardMuzzle.X;
		// Assist and exit are the no-warning phases of the room (reset is the upper band, which stays warned).
		Inputs.bInNoWarningPhase = FBrokenMillRules::IsInMissedCurrentAssist(Tuning(), Ella) || Ella.X >= Tuning().ExitPoint.X;
		if (IsFeatureEnabled(EFeatureId::HAZ_07))
		{
			ApplyWindEligibility(FBrokenMillRules::GetEligibleWind(Tuning(), Ella));
		}
	}
	const EMillGuardEvent Event = Guard.Advance(Tuning(), DeltaSeconds, Inputs);
	if (Event != EMillGuardEvent::None)
	{
		++EventCounts.FindOrAdd(Event);
	}
	if (Event == EMillGuardEvent::WarningStarted || Event == EMillGuardEvent::ShotReleased || Event == EMillGuardEvent::WarningAborted)
	{
		bLastReleaseAborted = Event == EMillGuardEvent::WarningAborted;
	}
	if (Event == EMillGuardEvent::ShotReleased)
	{
		ReleaseShot();
	}
	UpdateVisuals();
	return Event;
}

void ABrokenMillRoom::ApplyWindEligibility(EMillWind Eligible)
{
	// Both currents stay live (actor and volume collision enabled, overlap events on) for the guard's whole life, as
	// CAM-07 requires. Eligibility only switches the volume's response to pawns: an Ignore response ends the overlap,
	// so the wind actor itself sends WindExited (and WindEntered when it comes back with Ella inside). The Motor
	// still only rides while overhead with Ride held.
	auto Gate = [](AWindCurrent* Wind, bool bEligible)
	{
		if (!IsValid(Wind))
		{
			return;
		}
		if (UBoxComponent* Volume = Wind->FindComponentByClass<UBoxComponent>())
		{
			const ECollisionResponse Wanted = bEligible ? ECR_Overlap : ECR_Ignore;
			if (Volume->GetCollisionResponseToChannel(ECC_Pawn) != Wanted)
			{
				Volume->SetCollisionResponseToChannel(ECC_Pawn, Wanted);
			}
		}
	};
	Gate(UpperWind, Eligible == EMillWind::UpperReset);
	Gate(LowerWind, Eligible == EMillWind::LowerOnward);
}

void ABrokenMillRoom::ReleaseShot()
{
	FUmbrellaShotSpec Spec;
	Spec.Kind = EUmbrellaShotKind::EnemyRed;
	Spec.Origin = RoomToWorld(Tuning().GuardMuzzle);
	Spec.Origin.Y = UmbrellaDrawOrder::ProjectileY;
	const FVector Captured = RoomToWorld(FVector2D(Guard.CapturedTarget.X, Guard.CapturedTarget.Z));
	Spec.Velocity = FEnemyRules::AimVelocity(Spec.Origin, Captured, Tuning().ShotSpeed);
	Spec.Radius = Tuning().ShotRadius;
	Spec.Damage = Tuning().ShotDamage;
	Spec.LifetimeSeconds = FBrokenMillRules::GetGuardShotLifetime(Tuning());
	Spec.SourceId = GetFName();
	++ShotsFired;
	ShotLog.RecordEmission(Guard.ShotSerial, Clock, Spec.Origin);
	ActiveShot = AUmbrellaProjectile::Fire(GetWorld(), Spec);
}
