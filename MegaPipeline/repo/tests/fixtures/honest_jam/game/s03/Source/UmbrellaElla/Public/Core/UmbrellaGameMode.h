#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "UmbrellaGameMode.generated.h"

/** Not final: card 0.8 makes its Blueprint child (BP_GameMode / BP_Ella). */
UCLASS()
class UMBRELLAELLA_API AUmbrellaGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AUmbrellaGameMode();

	UFUNCTION(BlueprintCallable, Category = "Flow")
	void QuitFromPlay();
};
