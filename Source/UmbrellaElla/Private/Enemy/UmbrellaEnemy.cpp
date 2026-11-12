#include "Enemy/UmbrellaEnemy.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaCollision.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Owl/KeeperLook.h"
#include "Projectile/UmbrellaProjectile.h"
#include "UObject/UObjectGlobals.h"

namespace
{
	const TCHAR* CubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
	const TCHAR* BasicMaterialPath = TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
	const FName ColourParameter(TEXT("Color"));
	const FName SourceName(TEXT("Enemy"));

	FName StateName(EEnemyState State)
	{
		switch (State)
		{
		case EEnemyState::Patrol: return FName(TEXT("enemy_patrol"));
		case EEnemyState::Aim: return FName(TEXT("enemy_aim"));
		case EEnemyState::Recovery: return FName(TEXT("enemy_recovery"));
		case EEnemyState::Defeated: return FName(TEXT("enemy_defeated"));
		default: return FName(TEXT("enemy_withdrawn"));
		}
	}
}

AUmbrellaEnemy::AUmbrellaEnemy()
{
	PrimaryActorTick.bCanEverTick = true;
	HitBox = CreateDefaultSubobject<UBoxComponent>(TEXT("HitBox"));
	SetRootComponent(HitBox);
	HitBox->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	HitBox->SetCollisionObjectType(ECC_WorldDynamic);
	HitBox->SetCollisionResponseToAllChannels(ECR_Ignore);
	HitBox->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
	HitBox->SetGenerateOverlapEvents(true);
	Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
	Visual->SetupAttachment(HitBox);
	Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Visual->SetCastShadow(false);
}

AUmbrellaEnemy* AUmbrellaEnemy::SpawnEnemy(UWorld* World, EEnemyType Type, EEnemyVariant Variant, EUmbrellaShotKind Color, const FVector& Location,
	float SupportMinX, float SupportMaxX)
{
	if (!World)
	{
		return nullptr;
	}
	const bool bTypeOn = (Type == EEnemyType::Floodstrider) ? IsFeatureEnabled(EFeatureId::COM_15)
		: (Type == EEnemyType::SkyCourier) ? IsFeatureEnabled(EFeatureId::COM_16)
		: IsFeatureEnabled(EFeatureId::COM_14);
	if (!bTypeOn)
	{
		return nullptr;
	}
	// Both shot colours are supported by every type; with the dual-colour rule off the type shoots red only.
	const EUmbrellaShotKind UsedColor = IsFeatureEnabled(EFeatureId::COM_13) ? Color : EUmbrellaShotKind::EnemyRed;
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AUmbrellaEnemy* Enemy = World->SpawnActor<AUmbrellaEnemy>(AUmbrellaEnemy::StaticClass(), Location, FRotator::ZeroRotator, Params);
	if (Enemy)
	{
		Enemy->Configure(Type, Variant, UsedColor, Location, SupportMinX, SupportMaxX);
	}
	return Enemy;
}

void AUmbrellaEnemy::Configure(EEnemyType InType, EEnemyVariant InVariant, EUmbrellaShotKind InColor, const FVector& Location, float SupportMinX, float SupportMaxX)
{
	const FKeeperTuning& T = GetDefault<UUmbrellaTuning>()->Keeper;
	FEnemyProfile Profile = FEnemyModel::ProfileFor(InType, T);
	// The finite packet total is the Courier's own rule and can be switched off with its feature.
	if (!IsFeatureEnabled(EFeatureId::COM_17))
	{
		Profile.MaxEmissions = 0;
	}
	Variant = InVariant;
	Model.Init(InType, Profile, InColor, FVector2D(Location.X, Location.Z), SupportMinX, SupportMaxX);
	FVector2D Size = T.RoadwardenTorso;
	if (InType == EEnemyType::Floodstrider)
	{
		Size = T.FloodstriderTorso;
	}
	else if (InType == EEnemyType::SkyCourier)
	{
		Size = T.CourierBody;
	}
	HitBox->SetBoxExtent(FVector(Size.X * 0.5f, KeeperLook::PartDepth, Size.Y * 0.5f));
	SetActorLocation(FVector(Location.X, UmbrellaDrawOrder::KeeperY, Location.Z));
	ApplyLook();
}

void AUmbrellaEnemy::ApplyLook()
{
	if (!Visual || !Visual->GetStaticMesh())
	{
		return;
	}
	const FVector Extent = HitBox->GetUnscaledBoxExtent();
	Visual->SetWorldScale3D(FVector(Extent.X * 2.0f / KeeperLook::CubeEdge, KeeperLook::VisualDepth / KeeperLook::CubeEdge, Extent.Z * 2.0f / KeeperLook::CubeEdge));
	const bool bYellow = Model.GetColor() == EUmbrellaShotKind::EnemyYellow;
	FLinearColor Colour = bYellow ? KeeperLook::EnemyYellow : KeeperLook::EnemyRed;
	if (!Model.IsAlive())
	{
		Colour = KeeperLook::Broken;
	}
	if (UMaterialInstanceDynamic* Dynamic = Visual->CreateDynamicMaterialInstance(0))
	{
		Dynamic->SetVectorParameterValue(ColourParameter, Colour);
	}
}

void AUmbrellaEnemy::BeginPlay()
{
	Super::BeginPlay();
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, CubePath);
	UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, BasicMaterialPath);
	if (Cube)
	{
		Visual->SetStaticMesh(Cube);
	}
	if (Material)
	{
		Visual->SetMaterial(0, Material);
	}
	ApplyLook();
}

void AUmbrellaEnemy::StepBy(float DeltaSeconds, const FVector2D& PlayerPos)
{
	bManualStepping = true;
	TArray<FEnemyCommand> Commands;
	Model.Step(DeltaSeconds, PlayerPos, GetDefault<UUmbrellaTuning>()->Keeper, Commands);
	Process(Commands);
}

void AUmbrellaEnemy::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (bManualStepping || !Model.IsAlive())
	{
		return;
	}
	FVector2D PlayerPos = FVector2D::ZeroVector;
	if (const APawn* Pawn = GetWorld() ? GetWorld()->GetFirstPlayerController() ? GetWorld()->GetFirstPlayerController()->GetPawn() : nullptr : nullptr)
	{
		PlayerPos = FVector2D(Pawn->GetActorLocation().X, Pawn->GetActorLocation().Z);
	}
	TArray<FEnemyCommand> Commands;
	Model.Step(DeltaSeconds, PlayerPos, GetDefault<UUmbrellaTuning>()->Keeper, Commands);
	Process(Commands);
}

void AUmbrellaEnemy::Process(TArray<FEnemyCommand>& Commands)
{
	const FKeeperTuning& T = GetDefault<UUmbrellaTuning>()->Keeper;
	for (const FEnemyCommand& Command : Commands)
	{
		switch (Command.Type)
		{
		case EEnemyCommandType::FireShot:
		{
			FUmbrellaShotSpec Spec;
			Spec.Kind = Command.ShotKind;
			Spec.Origin = FVector(Command.A.X, UmbrellaDrawOrder::ProjectileY, Command.A.Y);
			Spec.Velocity = FVector(Command.B.X, 0.0f, Command.B.Y);
			Spec.Radius = T.EnemyShotRadius;
			Spec.Damage = T.EnemyShotDamage;
			Spec.LifetimeSeconds = T.EnemyShotLifetimeSeconds;
			Spec.SourceId = SourceName;
			AUmbrellaProjectile::Fire(GetWorld(), Spec);
			break;
		}
		case EEnemyCommandType::StateChanged:
			Broadcast(Command.State);
			ApplyLook();
			break;
		case EEnemyCommandType::Defeated:
		case EEnemyCommandType::Withdrawn:
			HitBox->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			break;
		default:
			break;
		}
	}
	SetActorLocation(FVector(Model.GetPosition().X, UmbrellaDrawOrder::KeeperY, Model.GetPosition().Y));
}

void AUmbrellaEnemy::Broadcast(EEnemyState State) const
{
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this);
	if (!Bus)
	{
		return;
	}
	// The art lane maps these cues to animation; the cue carries state, never timing.
	FUmbrellaEvent Event;
	Event.Type = EUmbrellaEventType::AnimationCue;
	Event.SourceId = GetFName();
	Event.Detail = StateName(State);
	Event.Amount = static_cast<int32>(Model.GetType());
	Event.Value = Model.GetHp();
	Bus->Broadcast(Event);
}

EUmbrellaShotResult AUmbrellaEnemy::ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation)
{
	if (Shot.Kind != EUmbrellaShotKind::PlayerBlast || !Model.IsAlive())
	{
		return EUmbrellaShotResult::Ignored;
	}
	TArray<FEnemyCommand> Commands;
	Model.ApplyHit(Shot.Damage, Commands);
	Process(Commands);
	return EUmbrellaShotResult::Consumed;
}

void AUmbrellaEnemy::ResetForRestart()
{
	Model.Reset();
	HitBox->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	SetActorHiddenInGame(false);
	SetActorLocation(FVector(Model.GetPosition().X, UmbrellaDrawOrder::KeeperY, Model.GetPosition().Y));
	ApplyLook();
}
