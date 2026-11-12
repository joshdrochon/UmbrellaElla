#pragma once

#include "CoreMinimal.h"
#include "UmbrellaPlayMode.generated.h"

/** The two player-facing modes. Start Game: one basic shot, straight to the Keeper. */
UENUM()
enum class EUmbrellaPlayMode : uint8
{
	StartGame,
	DirectorsCut
};
