#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "EllaCharacter.generated.h"

class UInputMappingContext;

/** Shell only: creates the components, camera and plane constraint; adds IMC_Default; calls each BindInput. */
/** Not final: card 0.8 makes its Blueprint child (BP_GameMode / BP_Ella). */
UCLASS()
class UMBRELLAELLA_API AEllaCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AEllaCharacter();

protected:
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

	UPROPERTY(EditDefaultsOnly, Category = "Input")
	TObjectPtr<UInputMappingContext> DefaultMappingContext;
};
