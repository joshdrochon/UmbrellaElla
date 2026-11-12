#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AbsorbReceiverComponent.generated.h"

class UEnhancedInputComponent;

/** Defense Receiver: absorbs yellow shots during absorb-fall. Lane c. */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UAbsorbReceiverComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UAbsorbReceiverComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);
};
