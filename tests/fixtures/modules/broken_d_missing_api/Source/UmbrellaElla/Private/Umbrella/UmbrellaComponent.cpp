#include "Umbrella/UmbrellaComponent.h"
#include "Umbrella/UmbrellaRules.h"
#include "PaperFlipbook.h"

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
}
