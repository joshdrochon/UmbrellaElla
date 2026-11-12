#pragma once

#include "CoreMinimal.h"

/** Player-facing ending text, taken word for word from the team story (GDD SH1.0 section 6). Nothing is invented here. */
struct UMBRELLAELLA_API FFlowStoryText
{
	/** The ending story pages shown over the background after the Keeper is beaten. */
	static TArray<FText> GetEndingPages();

	/** Credits lines as Rick supplied them; a role still OPEN in the GDD is left blank, not guessed. */
	static TArray<FText> GetCreditsLines();
};
