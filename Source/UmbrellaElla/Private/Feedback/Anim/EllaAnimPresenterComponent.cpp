#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Arena/ArenaCameraTuning.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "PaperFlipbook.h"
#include "PaperFlipbookComponent.h"

UEllaAnimPresenterComponent::UEllaAnimPresenterComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UEllaAnimPresenterComponent::BindInput(UEnhancedInputComponent* Input)
{
}

bool UEllaAnimPresenterComponent::IsShowingStandIn() const
{
	return IsValid(StandIn) && !IsValid(Flipbook);
}

namespace
{
	const EUmbrellaEventType PresentedEvents[] = {
		EUmbrellaEventType::ProjectileSpawned,
		EUmbrellaEventType::CatchAttempt,
		EUmbrellaEventType::CatchSucceeded,
		EUmbrellaEventType::CatchFailed,
		EUmbrellaEventType::LifeLost,
		EUmbrellaEventType::PlayerDefeated,
	};
}

EEllaVisualState UEllaAnimPresenterComponent::StateForEvent(const FUmbrellaEvent& Event, FName OwnerId)
{
	switch (Event.Type)
	{
	case EUmbrellaEventType::ProjectileSpawned:
		return Event.SourceId == OwnerId ? EEllaVisualState::Shoot : EEllaVisualState::Idle;
	case EUmbrellaEventType::CatchAttempt:
	case EUmbrellaEventType::CatchSucceeded:
		return EEllaVisualState::Absorb;
	case EUmbrellaEventType::CatchFailed:
	case EUmbrellaEventType::LifeLost:
		return EEllaVisualState::Hurt;
	case EUmbrellaEventType::PlayerDefeated:
		return EEllaVisualState::Down;
	default:
		return EEllaVisualState::Idle;
	}
}

FVector UEllaAnimPresenterComponent::StandInScaleFor(EEllaVisualState State)
{
	switch (State)
	{
	case EEllaVisualState::Shoot:
		return UmbrellaPresenterConst::StandInScale * UmbrellaPresenterConst::ShootMul;
	case EEllaVisualState::Absorb:
		return UmbrellaPresenterConst::StandInScale * UmbrellaPresenterConst::AbsorbMul;
	case EEllaVisualState::Hurt:
		return UmbrellaPresenterConst::StandInScale * UmbrellaPresenterConst::HurtMul;
	case EEllaVisualState::Down:
		return FVector(UmbrellaPresenterConst::StandInScale.Z, UmbrellaPresenterConst::StandInScale.Y, UmbrellaPresenterConst::StandInScale.X);
	default:
		return UmbrellaPresenterConst::StandInScale;
	}
}

void UEllaAnimPresenterComponent::SetStateFlipbook(EEllaVisualState State, UPaperFlipbook* InFlipbook)
{
	StateFlipbooks.Add(State, InFlipbook);
	ApplyState();
}

void UEllaAnimPresenterComponent::SetVisualState(EEllaVisualState State)
{
	VisualState = State;
	StateTimeLeft = (State == EEllaVisualState::Idle || State == EEllaVisualState::Down) ? 0.0f : GetDefault<UUmbrellaTuning>()->ArenaCamera.EllaStateHoldSeconds;
	ApplyState();
}

void UEllaAnimPresenterComponent::ApplyState()
{
	if (IsValid(StandIn))
	{
		StandIn->SetRelativeScale3D(StandInScaleFor(VisualState));
	}
	if (IsValid(Flipbook))
	{
		if (const TObjectPtr<UPaperFlipbook>* Found = StateFlipbooks.Find(VisualState))
		{
			if (IsValid(*Found))
			{
				Flipbook->SetFlipbook(*Found);
			}
		}
	}
}

void UEllaAnimPresenterComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (StateTimeLeft > 0.0f)
	{
		StateTimeLeft -= DeltaTime;
		if (StateTimeLeft <= 0.0f)
		{
			SetVisualState(EEllaVisualState::Idle);
		}
	}
}

void UEllaAnimPresenterComponent::HandleEvent(const FUmbrellaEvent& Event)
{
	const AActor* Owner = GetOwner();
	const EEllaVisualState State = StateForEvent(Event, IsValid(Owner) ? Owner->GetFName() : NAME_None);
	if (State != EEllaVisualState::Idle)
	{
		SetVisualState(State);
	}
}

void UEllaAnimPresenterComponent::BeginPlay()
{
	Super::BeginPlay();
	BuildVisual();
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		for (const EUmbrellaEventType Type : PresentedEvents)
		{
			Handles.Emplace(Type, Bus->On(Type).AddUObject(this, &UEllaAnimPresenterComponent::HandleEvent));
		}
	}
}

void UEllaAnimPresenterComponent::EndPlay(const EEndPlayReason::Type Reason)
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		for (const TPair<EUmbrellaEventType, FDelegateHandle>& Pair : Handles)
		{
			Bus->On(Pair.Key).Remove(Pair.Value);
		}
	}
	Handles.Reset();
	Super::EndPlay(Reason);
}

void UEllaAnimPresenterComponent::BuildVisual()
{
	AActor* Owner = GetOwner();
	if (!IsValid(Owner) || IsValid(StandIn) || IsValid(Flipbook) || !IsFeatureEnabled(EFeatureId::ART_03))
	{
		return;
	}
	if (IsValid(IdleFlipbook))
	{
		Flipbook = NewObject<UPaperFlipbookComponent>(Owner, TEXT("EllaFlipbook"));
		Flipbook->SetFlipbook(IdleFlipbook);
		Flipbook->SetupAttachment(Owner->GetRootComponent());
		Flipbook->RegisterComponent();
		return;
	}
	StandIn = NewObject<UStaticMeshComponent>(Owner, TEXT("EllaStandIn"));
	UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (IsValid(Shape))
	{
		StandIn->SetStaticMesh(Shape);
	}
	StandIn->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	StandIn->SetupAttachment(Owner->GetRootComponent());
	StandIn->SetRelativeScale3D(UmbrellaPresenterConst::StandInScale);
	StandIn->RegisterComponent();
}
