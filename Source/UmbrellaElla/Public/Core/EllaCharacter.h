#pragma once

#include "CoreMinimal.h"
#include "PaperCharacter.h"
#include "EllaCharacter.generated.h"

/** Ella pawn shell (card 0.3). Components are added by later cards. */
UCLASS()
class UMBRELLAELLA_API AEllaCharacter : public APaperCharacter
{
	GENERATED_BODY()

public:
	AEllaCharacter();
};
