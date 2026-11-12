#include "Feedback/Anim/EllaAnimPresenterComponent.h"

UEllaAnimPresenterComponent::UEllaAnimPresenterComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UEllaAnimPresenterComponent::BindInput(UEnhancedInputComponent* Input)
{
}
