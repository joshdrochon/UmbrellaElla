#pragma once

#include "CoreMinimal.h"
#include "PaperCharacter.h"
#include "EllaCharacter.generated.h"

class UUmbrellaComponent;

UCLASS()
class UMBRELLAELLA_API AEllaCharacter : public APaperCharacter
{
	GENERATED_BODY()

public:
	AEllaCharacter();

	UFUNCTION(BlueprintPure)
	UUmbrellaComponent* GetUmbrella() const { return Umbrella; }

private:
	UPROPERTY(VisibleAnywhere, meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UUmbrellaComponent> Umbrella;
};
