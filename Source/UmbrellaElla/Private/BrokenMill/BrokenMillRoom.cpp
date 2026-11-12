#include "BrokenMill/BrokenMillRoom.h"
#include "BrokenMill/BrokenMillTuning.h"
#include "Components/BoxComponent.h"
#include "Core/UmbrellaCollision.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Enemy/EnemyRules.h"
#include "Engine/World.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Kismet/GameplayStatics.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Trap/UmbrellaTrap.h"

ABrokenMillRoom::ABrokenMillRoom()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;
	Island = CreateDefaultSubobject<UBoxComponent>(TEXT("Island"));
	Island->SetupAttachment(Root);
	Island->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	Island->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
	Island->SetCollisionResponseToChannel(UmbrellaCollision::EnemyShot, ECR_Block);
	TargetBox = CreateDefaultSubobject<UBoxComponent>(TEXT("TargetBox"));
	TargetBox->SetupAttachment(Root);
	TargetBox->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	TargetBox->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
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
	const float IslandWidth = Tuning().IslandXRange.Y - Tuning().IslandXRange.X;
	const float IslandHeight = Tuning().IslandTop - Tuning().IslandUnderside;
	Island->SetBoxExtent(FVector(IslandWidth * 0.5, Tuning().DepthHalfExtent, IslandHeight * 0.5));
	Island->SetRelativeLocation(FVector(Tuning().IslandXRange.X + IslandWidth * 0.5, 0.0, Tuning().IslandUnderside + IslandHeight * 0.5));
	// The target sits at the shared target centre in the room frame.
	TargetBox->SetBoxExtent(FVector(Tuning().TargetSize.X * 0.5, Tuning().DepthHalfExtent, Tuning().TargetSize.Y * 0.5));
	TargetBox->SetRelativeLocation(FVector(Tuning().TargetCentre.X, 0.0, Tuning().TargetCentre.Y));
	if (UWorld* World = GetWorld())
	{
		Rotor = World->SpawnActor<AUmbrellaTrap>(AUmbrellaTrap::StaticClass(), FTransform(RoomToWorld(Tuning().RotorCentre)));
		if (IsValid(Rotor))
		{
			Rotor->ConfigureKind(ETrapKind::AirMill);
		}
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

void ABrokenMillRoom::ResetForRestart()
{
	Guard.Reset();
	Guard.SetGuardEnabled(true);
	ShotLog.Entries.Reset();
	GuardHp = Tuning().GuardHp;
	ShotsFired = 0;
	Clock = 0.0f;
	SetActorHiddenInGame(false);
	TargetBox->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
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
		if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
		{
			FUmbrellaEvent Event;
			Event.Type = EUmbrellaEventType::BossPartDestroyed;
			Event.SourceId = GetFName();
			Event.TargetId = GetFName();
			Event.Detail = TEXT("Enemy");
			Event.Value = Tuning().GuardHp;
			Bus->Broadcast(Event);
		}
	}
	return EUmbrellaShotResult::Consumed;
}

void ABrokenMillRoom::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!UGameplayStatics::IsGamePaused(this))
	{
		StepSeconds(DeltaSeconds);
	}
}

EMillGuardEvent ABrokenMillRoom::StepSeconds(float DeltaSeconds)
{
	Clock += DeltaSeconds;
	const AActor* Found = TargetActor.Get();
	if (!IsValid(Found))
	{
		Found = UGameplayStatics::GetPlayerPawn(this, 0);
	}
	FMillGuardInputs Inputs;
	Inputs.bShotGone = !ActiveShot.IsValid();
	if (IsValid(Found))
	{
		const FVector2D Ella = WorldToRoom(Found->GetActorLocation());
		Inputs.Ella = FVector(Ella.X, 0.0, Ella.Y);
		Inputs.bInActivationRegion = FBrokenMillRules::IsInActivationRegion(Tuning(), Inputs.Ella);
		Inputs.bEngagementValid = FBrokenMillRules::IsEngagementValid(Tuning(), Ella, true);
		Inputs.bPassedBehind = Ella.X > Tuning().GuardMuzzle.X;
	}
	const EMillGuardEvent Event = Guard.Advance(Tuning(), DeltaSeconds, Inputs);
	if (Event == EMillGuardEvent::ShotReleased)
	{
		ReleaseShot();
	}
	return Event;
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
