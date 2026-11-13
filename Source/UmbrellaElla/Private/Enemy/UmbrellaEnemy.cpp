#include "Feedback/Art/ArtSlot.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Enemy/EnemyTuning.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaCollision.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Kismet/GameplayStatics.h"
#include "Projectile/UmbrellaProjectile.h"

namespace
{
	bool IsTypeEnabled(EEnemyType Type)
	{
		switch (Type)
		{
		case EEnemyType::Roadwarden:
			return IsFeatureEnabled(EFeatureId::COM_14);
		case EEnemyType::Floodstrider:
			return IsFeatureEnabled(EFeatureId::COM_15);
		case EEnemyType::SkyCourier:
			return IsFeatureEnabled(EFeatureId::COM_16);
		default:
			return false;
		}
	}
}

AUmbrellaEnemy::AUmbrellaEnemy()
{
	PrimaryActorTick.bCanEverTick = true;
	Hitbox = CreateDefaultSubobject<UBoxComponent>(TEXT("Hitbox"));
	Hitbox->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	Hitbox->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
	RootComponent = Hitbox;
	Profile = FEnemyRules::MakeProfile(Type, Tuning());
	Brain.Reset(Profile);
	Packets.Reset(0);
}

void AUmbrellaEnemy::Configure(EEnemyType NewType, EEnemyGender NewGender, EUmbrellaShotKind NewShotKind)
{
	Type = NewType;
	Gender = IsFeatureEnabled(EFeatureId::COM_12) ? NewGender : EEnemyGender::Male;
	// Red or yellow only; a type is never limited to one colour.
	ShotKind = (IsFeatureEnabled(EFeatureId::COM_13) && NewShotKind == EUmbrellaShotKind::EnemyYellow) ? EUmbrellaShotKind::EnemyYellow : EUmbrellaShotKind::EnemyRed;
	Profile = FEnemyRules::MakeProfile(Type, Tuning());
	const FVector2D Body = Profile.Body;
	Hitbox->SetBoxExtent(FVector(Body.X * 0.5, Tuning().DepthHalfExtent, Body.Y * 0.5));
	HomeLocation = GetActorLocation();
	ResetForRestart();
}

void AUmbrellaEnemy::ResetForRestart()
{
	Brain.Reset(Profile);
	Packets.Reset(Type == EEnemyType::SkyCourier && IsFeatureEnabled(EFeatureId::COM_17) ? Tuning().CourierEmissionSlots : 0);
	ShotsFired = 0;
	SetActorHiddenInGame(false);
	Hitbox->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
	SetActorLocation(HomeLocation);
}

void AUmbrellaEnemy::SetTargetActor(AActor* NewTarget)
{
	TargetActor = NewTarget;
}

void AUmbrellaEnemy::BeginPlay()
{
	Super::BeginPlay();
	HomeLocation = GetActorLocation();
	UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	Placeholder = NewObject<UStaticMeshComponent>(this, TEXT("Placeholder"));
	if (IsValid(Shape))
	{
		Placeholder->SetStaticMesh(Shape);
	}
	Placeholder->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Placeholder->SetupAttachment(RootComponent);
	Placeholder->SetRelativeScale3D(FVector(Profile.Body.X / EnemyConst::CubeSize, Tuning().PlaceholderDepthScale, Profile.Body.Y / EnemyConst::CubeSize));
	ArtSlot::ApplyFlatUnlit(Placeholder, this, UmbrellaArtSlotConst::StandInEnemyColor);
	Placeholder->RegisterComponent();
}

bool AUmbrellaEnemy::CanResolveTarget(FVector& OutLocation) const
{
	const AActor* Found = TargetActor.Get();
	if (!IsValid(Found))
	{
		Found = UGameplayStatics::GetPlayerPawn(this, 0);
	}
	if (!IsValid(Found))
	{
		return false;
	}
	OutLocation = Found->GetActorLocation();
	return true;
}

FVector AUmbrellaEnemy::GetMuzzleLocation() const
{
	// Fixed-right fire: the muzzle sits on the left edge of the body, on the projectile plane.
	const FVector Here = GetActorLocation();
	return FVector(Here.X - Profile.Body.X * 0.5, UmbrellaDrawOrder::ProjectileY, Here.Z);
}

void AUmbrellaEnemy::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	StepSeconds(DeltaSeconds);
}

EEnemyBrainEvent AUmbrellaEnemy::StepSeconds(float DeltaSeconds)
{
	if (!IsTypeEnabled(Type))
	{
		return EEnemyBrainEvent::None;
	}
	FVector TargetLocation = FVector::ZeroVector;
	const bool bHaveTarget = CanResolveTarget(TargetLocation);
	const bool bInWindow = bHaveTarget && FEnemyRules::IsTargetInFiringWindow(GetActorLocation(), TargetLocation, Profile);
	const bool bHasEmissions = Type != EEnemyType::SkyCourier || !Packets.IsExhausted();
	const EEnemyState Before = Brain.State;
	const EEnemyBrainEvent Event = Brain.Advance(Profile, DeltaSeconds, bInWindow, bHasEmissions);
	if (Before != EEnemyState::Aim && Brain.State == EEnemyState::Aim)
	{
		AimPoint = TargetLocation;
	}
	if (Event == EEnemyBrainEvent::ReleaseShot)
	{
		ReleaseShot();
	}
	else if (Event == EEnemyBrainEvent::Withdraw)
	{
		// Withdrawal after the finite sequence: no kill XP, just leave.
		SetActorHiddenInGame(true);
		Hitbox->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Ignore);
	}
	SetActorLocation(FVector(HomeLocation.X + Brain.PatrolOffset, HomeLocation.Y, HomeLocation.Z));
	return Event;
}

void AUmbrellaEnemy::ReleaseShot()
{
	if (Type == EEnemyType::SkyCourier && IsFeatureEnabled(EFeatureId::COM_17) && Packets.TakeNextSlot() == INDEX_NONE)
	{
		return;
	}
	const FUmbrellaShotSpec Spec = FEnemyRules::MakeShot(Profile, ShotKind, GetMuzzleLocation(), AimPoint, GetFName());
	++ShotsFired;
	if (UWorld* World = GetWorld())
	{
		AUmbrellaProjectile::Fire(World, Spec);
	}
}

EUmbrellaShotResult AUmbrellaEnemy::ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation)
{
	if (!FEnemyRules::IsDamagingShot(Shot) || Brain.State == EEnemyState::Defeated || Brain.State == EEnemyState::Withdrawn)
	{
		return EUmbrellaShotResult::Ignored;
	}
	Brain.ApplyDamage(Shot.Damage);
	BroadcastEnemyEvent(EUmbrellaEventType::BossTargetHit, TEXT("Enemy"), Shot.Damage);
	if (Brain.State == EEnemyState::Defeated)
	{
		Defeat();
	}
	return EUmbrellaShotResult::Consumed;
}

void AUmbrellaEnemy::Defeat()
{
	// Zero HP stops new fire (the brain ignores steps) and shows a non-graphic disable; launched shots fly on.
	SetActorHiddenInGame(true);
	Hitbox->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Ignore);
	// No EnemyKilled event on the bus yet (docs/build/requests/enemies.md): part-destroyed with Detail=Enemy.
	BroadcastEnemyEvent(EUmbrellaEventType::BossPartDestroyed, TEXT("Enemy"), Profile.Hp);
}

void AUmbrellaEnemy::BroadcastEnemyEvent(EUmbrellaEventType EventType, FName Detail, float Value) const
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EventType;
		Event.SourceId = GetFName();
		Event.TargetId = GetFName();
		Event.Detail = Detail;
		Event.Value = Value;
		Bus->Broadcast(Event);
	}
}
