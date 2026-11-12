#include "Progression/ProgressionSubsystem.h"
#include "BrokenMill/BrokenMillRoom.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaLog.h"
#include "Engine/GameInstance.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Harness/UmbrellaFeatureFlags.h"

namespace
{
	bool NameHas(FName Name, const TCHAR* Needle)
	{
		return !Name.IsNone() && Name.ToString().Contains(Needle, ESearchCase::IgnoreCase);
	}

	// Exact strings other lanes broadcast (docs/build/requests/progression.md section 2).
	const FName ProgressionEnemyDetail(TEXT("Enemy"));
	const FName ProgressionKeeperSource(TEXT("KeeperOfTime"));
	const TCHAR* const ProgressionKeeperPhases[] = { TEXT("wings"), TEXT("mechanisms"), TEXT("clock") };

	/** The XP label of an enemy that broadcast BossPartDestroyed(Detail=Enemy), found by its actor name. */
	FName ProgressionEnemyLabel(UWorld* World, FName ActorName)
	{
		if (World == nullptr || ActorName.IsNone())
		{
			return NAME_None;
		}
		for (TActorIterator<AUmbrellaEnemy> It(World); It; ++It)
		{
			if (It->GetFName() == ActorName)
			{
				switch (It->GetEnemyType())
				{
				case EEnemyType::Roadwarden: return FName(TEXT("Roadwarden"));
				case EEnemyType::Floodstrider: return FName(TEXT("Floodstrider"));
				case EEnemyType::SkyCourier: return FName(TEXT("Courier"));
				default: return NAME_None;
				}
			}
		}
		// The Broken Mill guard is the introductory stationary Roadwarden.
		for (TActorIterator<ABrokenMillRoom> It(World); It; ++It)
		{
			if (It->GetFName() == ActorName)
			{
				return FName(TEXT("Roadwarden"));
			}
		}
		return NAME_None;
	}
}

UProgressionSubsystem::UProgressionSubsystem()
{
	Profile = FProgressionRules::MakeEmptyProfile();
}

void UProgressionSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	Profile = FProgressionRules::MakeEmptyProfile();
	PostInitHandle = FWorldDelegates::OnPostWorldInitialization.AddUObject(this, &UProgressionSubsystem::OnPostWorldInit);
	CleanupHandle = FWorldDelegates::OnWorldCleanup.AddUObject(this, &UProgressionSubsystem::OnWorldCleanup);
	UseSaveSlot(Tuning.SaveSlotName);
	if (const UGameInstance* Instance = GetGameInstance())
	{
		UWorld* World = Instance->GetWorld();
		if (World != nullptr && World->IsGameWorld())
		{
			BindToBus(World->GetSubsystem<UUmbrellaEventBus>());
		}
	}
}

void UProgressionSubsystem::Deinitialize()
{
	FWorldDelegates::OnPostWorldInitialization.Remove(PostInitHandle);
	FWorldDelegates::OnWorldCleanup.Remove(CleanupHandle);
	UnbindFromBus();
	Super::Deinitialize();
}

UProgressionSubsystem* UProgressionSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	const UGameInstance* Instance = World ? World->GetGameInstance() : nullptr;
	return Instance ? Instance->GetSubsystem<UProgressionSubsystem>() : nullptr;
}

void UProgressionSubsystem::OnPostWorldInit(UWorld* World, const UWorld::InitializationValues Values)
{
	if (World != nullptr && World->IsGameWorld() && World->GetGameInstance() == GetGameInstance())
	{
		BindToBus(World->GetSubsystem<UUmbrellaEventBus>());
	}
}

void UProgressionSubsystem::OnWorldCleanup(UWorld* World, bool bSessionEnded, bool bCleanupResources)
{
	if (BoundBus.IsValid() && BoundBus->GetWorld() == World)
	{
		UnbindFromBus();
	}
}

void UProgressionSubsystem::BindToBus(UUmbrellaEventBus* Bus)
{
	UnbindFromBus();
	if (Bus == nullptr)
	{
		return;
	}
	BoundBus = Bus;
	BoundTypes = { EUmbrellaEventType::ModeSelected, EUmbrellaEventType::BossPartDestroyed, EUmbrellaEventType::CheckpointReached,
		EUmbrellaEventType::CheckpointRetried, EUmbrellaEventType::RunCompleted, EUmbrellaEventType::EncounterCompleted };
	for (const EUmbrellaEventType Type : BoundTypes)
	{
		BoundHandles.Add(Bus->On(Type).AddUObject(this, &UProgressionSubsystem::HandleEvent));
	}
}

void UProgressionSubsystem::UnbindFromBus()
{
	if (UUmbrellaEventBus* Bus = BoundBus.Get())
	{
		for (int32 Index = 0; Index < BoundTypes.Num(); ++Index)
		{
			Bus->On(BoundTypes[Index]).Remove(BoundHandles[Index]);
		}
	}
	BoundTypes.Reset();
	BoundHandles.Reset();
	BoundBus.Reset();
}

void UProgressionSubsystem::UseSaveSlot(const FString& Slot)
{
	SaveSlot = Slot;
	LoadStatus = EProgressionLoadStatus::Fresh;
	Profile = FProgressionRules::MakeEmptyProfile();
	if (Slot.IsEmpty())
	{
		return;
	}
	const FProgressionLoadResult Loaded = FProgressionStore::Load(Slot);
	LoadStatus = Loaded.Status;
	if (Loaded.Status == EProgressionLoadStatus::BlockedCorrupt)
	{
		UE_LOG(LogUmbrellaElla, Error, TEXT("Progression save is corrupt in both copies; progression is blocked and nothing was overwritten."));
		return;
	}
	Profile = Loaded.Profile;
	if (Profile.Ranks.Num() != static_cast<int32>(EProgressionTrack::Count))
	{
		Profile = FProgressionRules::MakeEmptyProfile();
	}
	// Starting the game again is a reload: the last checkpoint's XP and upgrades.
	FProgressionRules::QuitReload(Profile);
}

// ---------------------------------------------------------------- events
void UProgressionSubsystem::HandleEvent(const FUmbrellaEvent& Event)
{
	switch (Event.Type)
	{
	case EUmbrellaEventType::ModeSelected:
		if (NameHas(Event.Detail, TEXT("Director")))
		{
			SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
			BeginRun();
		}
		else if (NameHas(Event.Detail, TEXT("Start")))
		{
			SetPlayMode(EUmbrellaPlayMode::StartGame);
		}
		break;
	case EUmbrellaEventType::BossPartDestroyed:
	{
		if (Event.SourceId == ProgressionKeeperSource)
		{
			// Keeper: TargetId is the part (WINGS, MECH_FRONT, MECH_MIDDLE, MECH_REAR, CLOCK, EYE); Detail is only the phase.
			AwardKill(Event.TargetId);
		}
		else if (Event.Detail == ProgressionEnemyDetail)
		{
			AwardKill(ProgressionEnemyLabel(BoundBus.IsValid() ? BoundBus->GetWorld() : nullptr, Event.SourceId));
		}
		else
		{
			const FName Labels[] = { Event.Detail, Event.TargetId };
			for (const FName Label : Labels)
			{
				if (AwardKill(Label) > 0)
				{
					break;
				}
			}
		}
		break;
	}
	case EUmbrellaEventType::CheckpointReached:
	{
		bool bBoss = Event.SourceId == ProgressionKeeperSource;
		for (const TCHAR* Phase : ProgressionKeeperPhases)
		{
			bBoss = bBoss || Event.Detail.ToString().Equals(Phase, ESearchCase::IgnoreCase);
		}
		bBoss = bBoss || NameHas(Event.Detail, TEXT("Phase")) || NameHas(Event.Detail, TEXT("Boss")) || NameHas(Event.Detail, TEXT("Keeper"));
		ReachCheckpoint(bBoss ? EProgressionCheckpointKind::Boss : EProgressionCheckpointKind::Level);
		break;
	}
	case EUmbrellaEventType::CheckpointRetried:
		RetryFromCheckpoint();
		break;
	case EUmbrellaEventType::RunCompleted:
	case EUmbrellaEventType::EncounterCompleted:
		CompleteRun();
		break;
	default:
		break;
	}
}

void UProgressionSubsystem::Broadcast(EUmbrellaEventType Type, FName Detail, int32 Amount)
{
	UUmbrellaEventBus* Bus = BoundBus.Get();
	if (Bus == nullptr)
	{
		return;
	}
	FUmbrellaEvent Event;
	Event.Type = Type;
	Event.SourceId = FName(TEXT("Progression"));
	Event.Detail = Detail;
	Event.Amount = Amount;
	Event.FeatureIds = { FName(TEXT("FLOW-14")) };
	Bus->Broadcast(Event);
}

// ---------------------------------------------------------------- mode and run
void UProgressionSubsystem::SetPlayMode(EUmbrellaPlayMode Mode)
{
	PlayMode = Mode;
	bRunActive = false;
	ChangedDelegate.Broadcast();
}

EUmbrellaPlayMode UProgressionSubsystem::GetPlayMode() const
{
	return PlayMode;
}

bool UProgressionSubsystem::IsProgressing() const
{
	return PlayMode == EUmbrellaPlayMode::DirectorsCut && !IsBlocked() && IsFeatureEnabled(EFeatureId::FLOW_14);
}

void UProgressionSubsystem::BeginRun()
{
	if (!IsProgressing())
	{
		return;
	}
	bFinalHour = FProgressionRules::IsAllStatsMaxed(Tuning, Profile);
	RunScaling = FProgressionRules::NextRunScaling(Tuning, Profile);
	bRunActive = true;
	FProgressionRules::ReachCheckpoint(Profile, EProgressionCheckpointKind::Level);
	Persist();
	ChangedDelegate.Broadcast();
}

void UProgressionSubsystem::ReachCheckpoint(EProgressionCheckpointKind Kind)
{
	if (!IsProgressing())
	{
		return;
	}
	FProgressionRules::ReachCheckpoint(Profile, Kind);
	Persist();
}

void UProgressionSubsystem::RetryFromCheckpoint()
{
	if (!IsProgressing())
	{
		return;
	}
	FProgressionRules::DeathRetry(Profile);
	Persist();
	ChangedDelegate.Broadcast();
}

void UProgressionSubsystem::QuitAndReload()
{
	if (!IsProgressing())
	{
		return;
	}
	FProgressionRules::QuitReload(Profile);
	bRunActive = false;
	ChangedDelegate.Broadcast();
}

void UProgressionSubsystem::CompleteRun()
{
	if (!IsProgressing() || !bRunActive || bShadowActive)
	{
		return;
	}
	bRunActive = false;
	FProgressionRules::CompleteRun(Profile);
	Persist();
	Broadcast(EUmbrellaEventType::RunCompleted, FName(TEXT("Progression")), Profile.CompletedRuns);
	ChangedDelegate.Broadcast();
}

bool UProgressionSubsystem::IsRunActive() const
{
	return bRunActive;
}

bool UProgressionSubsystem::IsFinalHourRun() const
{
	return bFinalHour;
}

FRunScaling UProgressionSubsystem::GetRunScaling() const
{
	return IsProgressing() ? RunScaling : FRunScaling();
}

// ---------------------------------------------------------------- XP
int32 UProgressionSubsystem::AwardKill(FName Label)
{
	if (!IsProgressing() || !bRunActive)
	{
		return 0;
	}
	const int32 Xp = FProgressionRules::KillXp(Tuning, Label);
	if (Xp <= 0)
	{
		return 0;
	}
	const int32 Gained = FProgressionRules::AddXp(Tuning, Profile, Xp);
	Persist();
	Broadcast(EUmbrellaEventType::XPAwarded, Label, Xp);
	if (Gained > 0)
	{
		const int32 Level = FProgressionRules::LevelForXp(Tuning, Profile.Xp).Level;
		Broadcast(EUmbrellaEventType::LevelGained, Label, Level);
		LevelGainedDelegate.Broadcast(Level);
	}
	ChangedDelegate.Broadcast();
	return Xp;
}

// ---------------------------------------------------------------- reads
FProgressionProfile UProgressionSubsystem::GetEffectiveProfile() const
{
	return PlayMode == EUmbrellaPlayMode::DirectorsCut ? Profile : FProgressionRules::MakeEmptyProfile();
}

int32 UProgressionSubsystem::GetLevel() const
{
	return GetLevelProgress().Level;
}

FLevelProgress UProgressionSubsystem::GetLevelProgress() const
{
	return FProgressionRules::LevelForXp(Tuning, GetEffectiveProfile().Xp);
}

int32 UProgressionSubsystem::GetXp() const
{
	return GetEffectiveProfile().Xp;
}

int32 UProgressionSubsystem::GetUnspentPoints() const
{
	return FProgressionRules::UnspentPoints(Tuning, GetEffectiveProfile());
}

int32 UProgressionSubsystem::GetCompletedRuns() const
{
	return GetEffectiveProfile().CompletedRuns;
}

int32 UProgressionSubsystem::GetRank(EProgressionTrack Track) const
{
	return FProgressionRules::RankOf(GetEffectiveProfile().Ranks, Track);
}

bool UProgressionSubsystem::IsSpellUnlocked(EProgressionSpell Spell) const
{
	return FProgressionRules::IsSpellUnlocked(Tuning, GetLevel(), Spell);
}

TArray<EProgressionSpell> UProgressionSubsystem::GetUnlockedSpells() const
{
	return FProgressionRules::UnlockedSpells(Tuning, GetLevel());
}

int32 UProgressionSubsystem::GetHitCapacity() const
{
	return FProgressionRules::HitCapacity(Tuning, GetEffectiveProfile().Ranks);
}

int32 UProgressionSubsystem::GetMaxLives() const
{
	return FProgressionRules::MaxLives(Tuning, GetEffectiveProfile().Ranks);
}

float UProgressionSubsystem::GetHealPerYellow() const
{
	return FProgressionRules::HealPerYellow(Tuning, GetEffectiveProfile().Ranks);
}

float UProgressionSubsystem::GetDamageReduction() const
{
	return FProgressionRules::DamageReduction(Tuning, GetEffectiveProfile().Ranks);
}

float UProgressionSubsystem::GetSuctionRange() const
{
	return FProgressionRules::SuctionRange(Tuning, GetEffectiveProfile().Ranks);
}

float UProgressionSubsystem::GetSuctionConeDegrees() const
{
	return FProgressionRules::SuctionConeDegrees(Tuning, GetEffectiveProfile().Ranks);
}

float UProgressionSubsystem::GetSpellDamageMultiplier(EProgressionSpell Spell) const
{
	return FProgressionRules::SpellDamageMultiplier(Tuning, GetEffectiveProfile().Ranks, Spell);
}

EProgressionLoadStatus UProgressionSubsystem::GetLoadStatus() const
{
	return LoadStatus;
}

bool UProgressionSubsystem::IsBlocked() const
{
	return LoadStatus == EProgressionLoadStatus::BlockedCorrupt;
}

// ---------------------------------------------------------------- purchases
void UProgressionSubsystem::SetPurchaseContext(const FPurchaseContext& Context)
{
	PurchaseContext = Context;
	ChangedDelegate.Broadcast();
}

FPurchaseContext UProgressionSubsystem::GetPurchaseContext() const
{
	return PurchaseContext;
}

bool UProgressionSubsystem::CanPurchaseNow() const
{
	return IsProgressing() && FProgressionRules::CanPurchase(PurchaseContext);
}

bool UProgressionSubsystem::CanReallocateNow() const
{
	return IsProgressing() && FProgressionRules::CanReallocate(PurchaseContext, Profile);
}

EProgressionCommit UProgressionSubsystem::CommitRanks(const TArray<int32>& NewRanks)
{
	if (!IsProgressing())
	{
		return EProgressionCommit::PurchaseNotAllowed;
	}
	const EProgressionCommit Result = FProgressionRules::TryCommitRanks(Tuning, Profile, NewRanks, PurchaseContext);
	if (Result == EProgressionCommit::Ok)
	{
		Persist();
		ChangedDelegate.Broadcast();
	}
	return Result;
}

// ---------------------------------------------------------------- shadow progress
void UProgressionSubsystem::BeginShadowProgress(int32 Level)
{
	if (!IsFeatureEnabled(EFeatureId::FLOW_23) || bShadowActive)
	{
		return;
	}
	RealProfileWhileShadow = Profile;
	Profile = FProgressionRules::MakeFixture(Tuning, Level);
	bShadowActive = true;
	ChangedDelegate.Broadcast();
}

void UProgressionSubsystem::EndShadowProgress()
{
	if (!bShadowActive)
	{
		return;
	}
	Profile = RealProfileWhileShadow;
	bShadowActive = false;
	bRunActive = false;
	ChangedDelegate.Broadcast();
}

bool UProgressionSubsystem::IsShadowActive() const
{
	return bShadowActive;
}

// ---------------------------------------------------------------- plumbing
void UProgressionSubsystem::Persist()
{
	if (!bShadowActive && !SaveSlot.IsEmpty() && !IsBlocked())
	{
		FProgressionStore::Save(SaveSlot, Profile);
	}
}

FOnProgressionChanged& UProgressionSubsystem::OnChanged()
{
	return ChangedDelegate;
}

FOnProgressionLevelGained& UProgressionSubsystem::OnLevelGained()
{
	return LevelGainedDelegate;
}

const FProgressionTuning& UProgressionSubsystem::GetTuning() const
{
	return Tuning;
}
