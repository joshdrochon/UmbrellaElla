#include "Health/UmbrellaHealthComponent.h"

UUmbrellaHealthComponent::UUmbrellaHealthComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UUmbrellaHealthComponent::BindInput(UEnhancedInputComponent* Input)
{
}
