#include "Persistence/ProgressionSaveGame.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/Crc.h"
#include "Progression/ProgressionRules.h"
#include "Serialization/MemoryWriter.h"

namespace
{
	/** The slot's profile and checksum, or null when the slot is absent or not our class. */
	const UProgressionSaveGame* ReadSlot(const FString& Slot)
	{
		if (!UGameplayStatics::DoesSaveGameExist(Slot, 0))
		{
			return nullptr;
		}
		return Cast<UProgressionSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot, 0));
	}

	bool IsIntact(const UProgressionSaveGame* Save)
	{
		return Save != nullptr && Save->GetChecksum() == FProgressionStore::ComputeChecksum(Save->GetProfile());
	}
}

FString FProgressionStore::BackupSlotName(const FString& Slot)
{
	return Slot + TEXT("_Backup");
}

int32 FProgressionStore::ComputeChecksum(const FProgressionProfile& Profile)
{
	TArray<uint8> Bytes;
	FMemoryWriter Writer(Bytes);
	int32 Xp = Profile.Xp;
	int32 Runs = Profile.CompletedRuns;
	int32 CheckpointXp = Profile.CheckpointXp;
	uint8 Valid = Profile.bCheckpointValid ? 1 : 0;
	uint8 Kind = static_cast<uint8>(Profile.CheckpointKind);
	TArray<int32> Ranks = Profile.Ranks;
	TArray<int32> CheckpointRanks = Profile.CheckpointRanks;
	Writer << Xp << Runs << CheckpointXp << Valid << Kind << Ranks << CheckpointRanks;
	return static_cast<int32>(FCrc::MemCrc32(Bytes.GetData(), Bytes.Num()));
}

void FProgressionStore::WriteSlot(const FString& Slot, const FProgressionProfile& Profile, int32 Checksum)
{
	UProgressionSaveGame* Save = Cast<UProgressionSaveGame>(UGameplayStatics::CreateSaveGameObject(UProgressionSaveGame::StaticClass()));
	if (Save != nullptr)
	{
		Save->Store(Profile, Checksum);
		UGameplayStatics::SaveGameToSlot(Save, Slot, 0);
	}
}

int32 FProgressionStore::Save(const FString& Slot, const FProgressionProfile& Profile)
{
	if (!IsFeatureEnabled(EFeatureId::FLOW_22) || Slot.IsEmpty())
	{
		return 0;
	}
	int32 Written = 0;
	const UProgressionSaveGame* Current = ReadSlot(Slot);
	if (IsIntact(Current))
	{
		WriteSlot(BackupSlotName(Slot), Current->GetProfile(), Current->GetChecksum());
		++Written;
	}
	WriteSlot(Slot, Profile, ComputeChecksum(Profile));
	return Written + 1;
}

FProgressionLoadResult FProgressionStore::Load(const FString& Slot)
{
	FProgressionLoadResult Result;
	Result.Profile = FProgressionRules::MakeEmptyProfile();
	if (Slot.IsEmpty())
	{
		return Result;
	}
	const UProgressionSaveGame* Main = ReadSlot(Slot);
	const UProgressionSaveGame* Backup = ReadSlot(BackupSlotName(Slot));
	if (IsIntact(Main))
	{
		Result.Status = EProgressionLoadStatus::Loaded;
		Result.Profile = Main->GetProfile();
	}
	else if (IsIntact(Backup))
	{
		Result.Status = EProgressionLoadStatus::LoadedFromBackup;
		Result.Profile = Backup->GetProfile();
	}
	else if (Main != nullptr || Backup != nullptr)
	{
		Result.Status = EProgressionLoadStatus::BlockedCorrupt;
	}
	return Result;
}

void FProgressionStore::Delete(const FString& Slot)
{
	UGameplayStatics::DeleteGameInSlot(Slot, 0);
	UGameplayStatics::DeleteGameInSlot(BackupSlotName(Slot), 0);
}
