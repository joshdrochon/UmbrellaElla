#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AttackEmitterComponent.generated.h"

class UEnhancedInputComponent;

/** Attack Emitter: Small Blasts, fixed right, only while dropping. Lane a. */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UAttackEmitterComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UAttackEmitterComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);
};
