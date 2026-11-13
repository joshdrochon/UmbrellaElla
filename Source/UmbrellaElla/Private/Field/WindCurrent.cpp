#include "Field/WindCurrent.h"
#include "Components/BoxComponent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "GameFramework/Pawn.h"
#include "Harness/UmbrellaFeatureFlags.h"

AWindCurrent::AWindCurrent()
{
	PrimaryActorTick.bCanEverTick = false;
	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	Volume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	Volume->SetGenerateOverlapEvents(true);
	RootComponent = Volume;
}

FName AWindCurrent::DirectionLabel(const FVector& InDirection)
{
	if (FMath::Abs(InDirection.X) >= FMath::Abs(InDirection.Z))
	{
		return InDirection.X < 0.0 ? FName(TEXT("Left")) : FName(TEXT("Right"));
	}
	return InDirection.Z < 0.0 ? FName(TEXT("Down")) : FName(TEXT("Up"));
}

float AWindCurrent::GetForce() const
{
	const float Used = Force < 0.0f ? GetDefault<UUmbrellaTuning>()->Field.DefaultWindForce : Force;
	return FMath::Max(0.0f, Used);
}

void AWindCurrent::SetHalfExtent(float HalfX, float HalfZ)
{
	Volume->SetBoxExtent(FVector(HalfX, Volume->GetUnscaledBoxExtent().Y, HalfZ));
}

void AWindCurrent::SetCurrent(const FVector& NewDirection, float NewForce)
{
	Direction = NewDirection.GetSafeNormal();
	Force = NewForce;
}

void AWindCurrent::SetLocalVerticalField(float Gain, float CentreZ, float Compensation)
{
	bHasLocalField = true;
	LocalGain = Gain;
	LocalCentreZ = CentreZ;
	LocalCompensation = Compensation;
}

void AWindCurrent::BroadcastEntered(const AActor* Other) const
{
	if (!IsFeatureEnabled(EFeatureId::WIND_03) || !IsValid(Other))
	{
		return;
	}
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::WindEntered;
		Event.SourceId = GetFName();
		Event.TargetId = Other->GetFName();
		Event.Detail = bHasLocalField
			? FName(*FString::Printf(TEXT("%s@%g,%g,%g"), *DirectionLabel(Direction).ToString(), LocalGain, LocalCentreZ, LocalCompensation))
			: DirectionLabel(Direction);
		Event.Value = GetForce();
		Bus->Broadcast(Event);
	}
}

void AWindCurrent::BroadcastExited(const AActor* Other) const
{
	if (!IsFeatureEnabled(EFeatureId::WIND_03) || !IsValid(Other))
	{
		return;
	}
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::WindExited;
		Event.SourceId = GetFName();
		Event.TargetId = Other->GetFName();
		Event.Detail = DirectionLabel(Direction);
		Event.Value = GetForce();
		Bus->Broadcast(Event);
	}
}

void AWindCurrent::NotifyActorBeginOverlap(AActor* OtherActor)
{
	Super::NotifyActorBeginOverlap(OtherActor);
	if (Cast<APawn>(OtherActor))
	{
		BroadcastEntered(OtherActor);
	}
}

void AWindCurrent::NotifyActorEndOverlap(AActor* OtherActor)
{
	Super::NotifyActorEndOverlap(OtherActor);
	if (Cast<APawn>(OtherActor))
	{
		BroadcastExited(OtherActor);
	}
}
