#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EllaInputAdapterComponent.generated.h"

class UEnhancedInputComponent;

/** Input Adapter: adds IMC_Default (priority 0) and maps holds to requested actions; no physics. Lane a. */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UEllaInputAdapterComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UEllaInputAdapterComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);
};
