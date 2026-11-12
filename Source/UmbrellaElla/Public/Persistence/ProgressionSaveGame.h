#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Progression/ProgressionTypes.h"
#include "ProgressionSaveGame.generated.h"

/** One saved copy of the earned-character data plus its checksum. Tuning and key bindings live elsewhere (separate data). */
UCLASS()
class UMBRELLAELLA_API UProgressionSaveGame final : public USaveGame
{
	GENERATED_BODY()

public:
	void Store(const FProgressionProfile& InProfile, int32 InChecksum)
	{
		Profile = InProfile;
		Checksum = InChecksum;
	}

	const FProgressionProfile& GetProfile() const { return Profile; }
	int32 GetChecksum() const { return Checksum; }

private:
	UPROPERTY(SaveGame)
	int32 FormatVersion = 1;

	UPROPERTY(SaveGame)
	FProgressionProfile Profile;

	UPROPERTY(SaveGame)
	int32 Checksum = 0;
};

UENUM()
enum class EProgressionLoadStatus : uint8
{
	/** No save exists: a fresh profile. */
	Fresh,
	Loaded,
	/** The main copy failed its checksum and the backup was used. */
	LoadedFromBackup,
	/** Both copies are corrupt: progression is blocked with a recoverable error, nothing is overwritten. */
	BlockedCorrupt
};

struct UMBRELLAELLA_API FProgressionLoadResult
{
	EProgressionLoadStatus Status = EProgressionLoadStatus::Fresh;
	FProgressionProfile Profile;
};

/** Checksummed save with a backup copy. Plain functions; the slot name decides where it goes (tests use their own slot and delete it). */
struct UMBRELLAELLA_API FProgressionStore
{
	static FString BackupSlotName(const FString& Slot);
	static int32 ComputeChecksum(const FProgressionProfile& Profile);
	/** Moves the current good main copy to the backup slot, then writes the new main copy. Returns the count of copies written (0 = failed). */
	static int32 Save(const FString& Slot, const FProgressionProfile& Profile);
	/** Test seam: write a slot with an explicit checksum (to plant a corrupt copy). */
	static void WriteSlot(const FString& Slot, const FProgressionProfile& Profile, int32 Checksum);
	static FProgressionLoadResult Load(const FString& Slot);
	static void Delete(const FString& Slot);
};
