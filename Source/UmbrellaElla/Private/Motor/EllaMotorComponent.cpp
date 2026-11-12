#include "Motor/EllaMotorComponent.h"

UEllaMotorComponent::UEllaMotorComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UEllaMotorComponent::BindInput(UEnhancedInputComponent* Input)
{
}
