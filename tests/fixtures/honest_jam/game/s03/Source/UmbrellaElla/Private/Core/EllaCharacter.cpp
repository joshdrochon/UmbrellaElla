#include "Core/EllaCharacter.h"

#include "EnhancedInputSubsystems.h"
#include "InputMappingContext.h"

AEllaCharacter::AEllaCharacter()
{
	PrimaryActorTick.bCanEverTick = false;
}

void AEllaCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
}
