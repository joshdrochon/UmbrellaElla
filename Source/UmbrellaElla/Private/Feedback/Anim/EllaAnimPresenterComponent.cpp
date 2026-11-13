#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Arena/ArenaCameraTuning.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Feedback/Art/ArtSlot.h"
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
	return IsValid(StandIn) && !IsValid(Flipbook) && !ArtSlot::HasArt(StandIn);
}

bool UEllaAnimPresenterComponent::IsShowingArt() const
{
	return ArtSlot::HasArt(StandIn);
}

UTexture2D* UEllaAnimPresenterComponent::TextureForState(EEllaVisualState State) const
{
	if (const TObjectPtr<UTexture2D>* Found = StateTextures.Find(State))
	{
		if (IsValid(*Found))
		{
			return *Found;
		}
	}
	const TObjectPtr<UTexture2D>* Idle = StateTextures.Find(EEllaVisualState::Idle);
	return Idle ? Idle->Get() : nullptr;
}

FString UEllaAnimPresenterComponent::FlipbookSlotName(EEllaVisualState State)
{
	switch (State)
	{
	case EEllaVisualState::Idle:
		return TEXT("Open");
	case EEllaVisualState::Shoot:
		return TEXT("Attack");
	case EEllaVisualState::Absorb:
		return TEXT("Shield");
	case EEllaVisualState::Down:
		return TEXT("Closed");
	default:
		return FString();
	}
}

TArray<FString> UEllaAnimPresenterComponent::FlipbookSlotPaths(EEllaVisualState State)
{
	TArray<FString> Paths;
	const FString Name = FlipbookSlotName(State);
	if (!Name.IsEmpty())
	{
		const FString Base = FString::Printf(TEXT("%s/Ella/FB_Ella_%s"), UmbrellaArtSlotConst::GameRoot, *Name);
		const FString Leaf = FString::Printf(TEXT("FB_Ella_%s"), *Name);
		Paths.Add(FString::Printf(TEXT("%s%s.%s%s"), *Base, UmbrellaArtSlotConst::PlaceholderSuffix, *Leaf, UmbrellaArtSlotConst::PlaceholderSuffix));
		Paths.Add(FString::Printf(TEXT("%s.%s"), *Base, *Leaf));
	}
	return Paths;
}

void UEllaAnimPresenterComponent::LoadSlotFlipbooks()
{
	const UEnum* States = StaticEnum<EEllaVisualState>();
	for (int32 Index = 0; Index < States->NumEnums() - 1; ++Index)
	{
		const EEllaVisualState State = static_cast<EEllaVisualState>(States->GetValueByIndex(Index));
		for (const FString& Path : FlipbookSlotPaths(State))
		{
			if (UPaperFlipbook* Found = LoadObject<UPaperFlipbook>(nullptr, *Path, nullptr, LOAD_NoWarn | LOAD_Quiet))
			{
				StateFlipbooks.Add(State, Found);
				break;
			}
		}
	}
	if (!IsValid(IdleFlipbook))
	{
		if (const TObjectPtr<UPaperFlipbook>* Idle = StateFlipbooks.Find(EEllaVisualState::Idle))
		{
			IdleFlipbook = *Idle;
		}
	}
}

void UEllaAnimPresenterComponent::LoadSlotArt()
{
	const UEnum* States = StaticEnum<EEllaVisualState>();
	for (int32 Index = 0; Index < States->NumEnums() - 1; ++Index)
	{
		const FString Visual = TEXT("ella-state:") + States->GetNameStringByIndex(Index);
		const FArtSlotRow* Row = ArtSlot::Find(*Visual);
		if (UTexture2D* Texture = Row ? ArtSlot::LoadTexture(*Row) : nullptr)
		{
			StateTextures.Add(static_cast<EEllaVisualState>(States->GetValueByIndex(Index)), Texture);
		}
	}
	DrawArt();
}

void UEllaAnimPresenterComponent::DrawArt()
{
	UTexture2D* Texture = TextureForState(VisualState);
	const FArtSlotRow* Row = ArtSlot::Find(TEXT("ella-state:Idle"));
	if (IsValid(StandIn) && !ArtSlot::HasArt(StandIn) && Texture && Row)
	{
		ArtSlot::Apply(StandIn, Texture, *Row, StandInScaleFor(VisualState));
	}
}

void UEllaAnimPresenterComponent::SetStateTexture(EEllaVisualState State, UTexture2D* Texture)
{
	StateTextures.Add(State, Texture);
	DrawArt();
	ApplyState();
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
		ArtSlot::SetBoxScale(StandIn, StandInScaleFor(VisualState));
		if (ArtSlot::HasArt(StandIn))
		{
			ArtSlot::SetTexture(StandIn, TextureForState(VisualState));
		}
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
	LoadSlotFlipbooks();
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
	LoadSlotArt();
}
