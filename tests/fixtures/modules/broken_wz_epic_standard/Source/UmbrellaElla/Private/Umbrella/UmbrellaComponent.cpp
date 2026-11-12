#include "Umbrella/UmbrellaComponent.h"
#include "Umbrella/UmbrellaRules.h"
#include "PaperFlipbook.h"

#define DEBUG_ON 1
using FMath::Max;

UUmbrellaComponent::UUmbrellaComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UUmbrellaComponent::SetOpen(bool bNewOpen)
{
	bOpen = bNewOpen;
}

void UUmbrellaComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	UObject* Scratch = nullptr; // locals are fine
	auto X = GetOwner();
	float Local = 0.f;
	GetWorld()->GetTimerManager().SetTimer(H2, [&]() { Local += 1.f; }, 0.5f, false);
	float Fall = DeltaTime * 600.f;
}
