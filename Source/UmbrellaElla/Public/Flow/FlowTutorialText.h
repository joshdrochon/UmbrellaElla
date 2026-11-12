#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaPlayMode.h"

/** First-start tutorial pages. Both modes teach the same controls, each with its own presentation. */
struct UMBRELLAELLA_API FFlowTutorialText
{
	static TArray<FText> GetPages(EUmbrellaPlayMode Mode);
	static FText GetHeading(EUmbrellaPlayMode Mode);
};
