#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EllaAnimPresenterComponent.generated.h"

class UEnhancedInputComponent;

/** Animation Presenter: state to Paper2D flipbook, placeholder fallback. Never gameplay authority. Lane e. */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UEllaAnimPresenterComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UEllaAnimPresenterComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);
};
