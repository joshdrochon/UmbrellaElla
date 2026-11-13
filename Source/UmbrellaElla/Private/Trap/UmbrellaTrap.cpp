#include "Feedback/Art/ArtSlot.h"
#include "Trap/UmbrellaTrap.h"
#include "Trap/TrapTuning.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaCollision.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Pawn.h"
#include "Projectile/UmbrellaShotReceiver.h"
#include "Projectile/UmbrellaShotSpec.h"

AUmbrellaTrap::AUmbrellaTrap()
{
	PrimaryActorTick.bCanEverTick = true;
	Hazard = CreateDefaultSubobject<UBoxComponent>(TEXT("Hazard"));
	Hazard->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	Hazard->SetCollisionObjectType(UmbrellaCollision::Hazard);
	Hazard->SetGenerateOverlapEvents(true);
	RootComponent = Hazard;
	Cycle = FTrapRules::MakeCycle(Kind, Tuning());
}

void AUmbrellaTrap::ConfigureKind(ETrapKind NewKind)
{
	Kind = NewKind;
	Cycle = FTrapRules::MakeCycle(Kind, Tuning());
	CycleTime = 0.0f;
	FVector2D Size = FVector2D(Tuning().RotorSweptRadius * 2.0f, Tuning().RotorSweptRadius * 2.0f);
	if (Kind == ETrapKind::RoofTeeth)
	{
		Size = Tuning().TeethSize;
	}
	else if (Kind != ETrapKind::AirMill)
	{
		Size = FVector2D(Tuning().TeethSize.X, Tuning().RotorSweptRadius * 2.0f);
	}
	Hazard->SetBoxExtent(FVector(Size.X * 0.5, Tuning().DepthHalfExtent, Size.Y * 0.5));
}

ETrapPhase AUmbrellaTrap::GetPhase() const
{
	return Cycle.PhaseAt(CycleTime);
}

void AUmbrellaTrap::BeginPlay()
{
	Super::BeginPlay();
	UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	Placeholder = NewObject<UStaticMeshComponent>(this, TEXT("Placeholder"));
	if (IsValid(Shape))
	{
		Placeholder->SetStaticMesh(Shape);
	}
	Placeholder->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Placeholder->SetupAttachment(RootComponent);
	const FVector Extent = Hazard->GetUnscaledBoxExtent();
	Placeholder->SetRelativeScale3D(FVector(Extent.X * 2.0 / TrapConst::CubeSize, Tuning().PlaceholderDepthScale, Extent.Z * 2.0 / TrapConst::CubeSize));
	Placeholder->SetRelativeLocation(FVector(0.0, UmbrellaDrawOrder::HazardY, 0.0));
	ArtSlot::ApplyFlatUnlit(Placeholder, this, UmbrellaArtSlotConst::StandInDefaultColor);
	Placeholder->RegisterComponent();
}

void AUmbrellaTrap::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	StepSeconds(DeltaSeconds);
}

void AUmbrellaTrap::StepSeconds(float DeltaSeconds)
{
	CycleTime += DeltaSeconds;
	Gate.Advance(DeltaSeconds);
	TArray<AActor*> Overlapping;
	Hazard->GetOverlappingActors(Overlapping, APawn::StaticClass());
	for (AActor* Victim : Overlapping)
	{
		ApplyContact(Victim);
	}
}

float AUmbrellaTrap::ApplyContact(AActor* Victim)
{
	if (!IsValid(Victim) || !FTrapRules::IsPhaseDamaging(Kind, GetPhase()))
	{
		return 0.0f;
	}
	// The air mill blocks its whole swept disk, not the box corners.
	if (Kind == ETrapKind::AirMill && !FTrapRules::IsInsideSweptDisk(Victim->GetActorLocation(), GetActorLocation(), Tuning().RotorSweptRadius))
	{
		return 0.0f;
	}
	const float Dealt = Gate.ConsumeHit(Victim->GetFName(), Tuning().ContactDamage, Tuning().PostHitProtectionSeconds);
	if (Dealt <= 0.0f)
	{
		return 0.0f;
	}
	FUmbrellaShotSpec Spec;
	Spec.Kind = EUmbrellaShotKind::EnemyRed;
	Spec.Origin = GetActorLocation();
	Spec.Damage = Dealt;
	Spec.SourceId = GetFName();
	// Stop at the first receiver that consumes the hit, as the projectile service does.
	bool bConsumed = false;
	if (IUmbrellaShotReceiver* Receiver = Cast<IUmbrellaShotReceiver>(Victim))
	{
		bConsumed = Receiver->ReceiveShot(Spec, Victim->GetActorLocation()) == EUmbrellaShotResult::Consumed;
	}
	for (UActorComponent* Component : Victim->GetComponents())
	{
		if (bConsumed)
		{
			break;
		}
		if (IUmbrellaShotReceiver* OnComponent = Cast<IUmbrellaShotReceiver>(Component))
		{
			bConsumed = OnComponent->ReceiveShot(Spec, Victim->GetActorLocation()) == EUmbrellaShotResult::Consumed;
		}
	}
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::ProjectileContact;
		Event.SourceId = GetFName();
		Event.TargetId = Victim->GetFName();
		Event.Detail = FTrapRules::KindName(Kind);
		Event.Value = Dealt;
		Bus->Broadcast(Event);
	}
	return Dealt;
}
