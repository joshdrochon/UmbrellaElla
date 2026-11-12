#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EllaMotorComponent.generated.h"

class UEnhancedInputComponent;

/** Player Motor: the only writer of velocity and gravity. Lane a. */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UEllaMotorComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UEllaMotorComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);
};
