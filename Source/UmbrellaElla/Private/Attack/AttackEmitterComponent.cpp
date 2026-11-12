#include "Attack/AttackEmitterComponent.h"

UAttackEmitterComponent::UAttackEmitterComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UAttackEmitterComponent::BindInput(UEnhancedInputComponent* Input)
{
}
