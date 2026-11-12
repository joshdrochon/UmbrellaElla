#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "PaperFlipbook.h"
#include "PaperFlipbookComponent.h"

UEllaAnimPresenterComponent::UEllaAnimPresenterComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UEllaAnimPresenterComponent::BindInput(UEnhancedInputComponent* Input)
{
}

bool UEllaAnimPresenterComponent::IsShowingStandIn() const
{
	return IsValid(StandIn) && !IsValid(Flipbook);
}

void UEllaAnimPresenterComponent::BeginPlay()
{
	Super::BeginPlay();
	BuildVisual();
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
