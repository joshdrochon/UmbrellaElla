#pragma once

#include "CoreMinimal.h"
#include "Settings/SettingsResult.h"

struct FUmbrellaSettingsData;

/** Reads and writes the persistent settings file (plain text, FConfigFile format). Independent of earned progression. */
namespace SettingsStore
{
	/** The shipped settings file: Saved/SaveGames/UmbrellaSettings.ini. */
	UMBRELLAELLA_API FString GetDefaultPath();

	/** Write Data to Path. Ok on success. */
	UMBRELLAELLA_API ESettingsResult Write(const FString& Path, const FUmbrellaSettingsData& Data);

	/** Read Path into Data. Failed (Data = defaults) when the file is missing or unreadable. Out-of-range values are clamped. */
	UMBRELLAELLA_API ESettingsResult Read(const FString& Path, FUmbrellaSettingsData& Data);

	/** Delete the file (tests clean up with this). */
	UMBRELLAELLA_API void Delete(const FString& Path);
}
