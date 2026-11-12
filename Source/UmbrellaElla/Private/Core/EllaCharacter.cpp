#include "Core/EllaCharacter.h"
#include "GameFramework/CharacterMovementComponent.h"

AEllaCharacter::AEllaCharacter()
{
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->SetPlaneConstraintEnabled(true);
	Move->SetPlaneConstraintNormal(FVector(0.0, 1.0, 0.0));
}
