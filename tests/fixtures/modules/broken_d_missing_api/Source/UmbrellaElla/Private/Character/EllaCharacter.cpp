#include "Character/EllaCharacter.h"
#include "Umbrella/UmbrellaComponent.h"
#include "EnhancedInputComponent.h"

AEllaCharacter::AEllaCharacter()
{
	Umbrella = CreateDefaultSubobject<UUmbrellaComponent>(TEXT("Umbrella"));
}
