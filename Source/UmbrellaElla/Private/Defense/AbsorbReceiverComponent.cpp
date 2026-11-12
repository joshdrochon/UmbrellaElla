#include "Defense/AbsorbReceiverComponent.h"

UAbsorbReceiverComponent::UAbsorbReceiverComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UAbsorbReceiverComponent::BindInput(UEnhancedInputComponent* Input)
{
}
