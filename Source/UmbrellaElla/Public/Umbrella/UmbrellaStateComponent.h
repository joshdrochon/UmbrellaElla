#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "UmbrellaStateComponent.generated.h"

class UEnhancedInputComponent;

/** Umbrella State: Ella's action-state enum and transitions. Lane a. */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UUmbrellaStateComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UUmbrellaStateComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);
};
