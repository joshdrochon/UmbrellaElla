#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "UmbrellaHealthComponent.generated.h"

class UEnhancedInputComponent;

/** Health/Condition: hits, lives, damage scale, healing; broadcasts PlayerDefeated. Lane c. */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UUmbrellaHealthComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UUmbrellaHealthComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);
};
