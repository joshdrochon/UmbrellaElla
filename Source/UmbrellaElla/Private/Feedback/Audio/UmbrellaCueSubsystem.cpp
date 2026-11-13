#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Core/UmbrellaEvent.h"
#include "Feedback/Audio/UmbrellaCueTable.h"
#include "Sound/SoundClass.h"
#include "Sound/SoundConcurrency.h"
#include "Subsystems/SubsystemCollection.h"
#include "Subsystems/SubsystemCollection.h"
#include "Core/UmbrellaEventBus.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Components/AudioComponent.h"
#include "Misc/ScopeExit.h"
#if UMBRELLAELLA_WORKBENCH
#include "Feedback/Audio/SoundLabelBoard.h"
#include "Feedback/Audio/SoundLabelHud.h"
#endif

namespace
{
	// Takes are SW_<Id>_NN under /Game/UmbrellaElla/Audio/<Id>/ (tools/build/assets/arena_audio_import.py).
	TArray<USoundBase*> LoadTakes(const FUmbrellaSoundCue& Cue)
	{
		TArray<USoundBase*> Takes;
		for (int32 Take = 0; Take < Cue.Takes; ++Take)
		{
			const FString Name = FString::Printf(TEXT("SW_%s_%02d"), Cue.Id, Take);
			const FString Path = FString::Printf(TEXT("/Game/UmbrellaElla/Audio/%s/%s.%s"), Cue.Id, *Name, *Name);
			if (USoundBase* Sound = LoadObject<USoundBase>(nullptr, *Path, nullptr, LOAD_Quiet | LOAD_NoWarn))
			{
				Takes.Add(Sound);
			}
		}
		return Takes;
	}

	const EUmbrellaEventType CuedEvents[] = {
		EUmbrellaEventType::ProjectileSpawned,
		EUmbrellaEventType::ProjectileContact,
		EUmbrellaEventType::CatchSucceeded,
		EUmbrellaEventType::CatchFailed,
		EUmbrellaEventType::BossTargetHit,
		EUmbrellaEventType::BossAttackTelegraphed,
		EUmbrellaEventType::PlayerDefeated,
		EUmbrellaEventType::EncounterCompleted,
		EUmbrellaEventType::ModeSelected,
		EUmbrellaEventType::LevelGained,
	};
}

void UUmbrellaCueSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Collection.InitializeDependency<UUmbrellaEventBus>();
	Super::Initialize(Collection);
#if UMBRELLAELLA_WORKBENCH
	SoundLabels = MakeShared<FUmbrellaSoundLabelBoard>();
	SoundLabelHud = MakeShared<FUmbrellaSoundLabelHud>(SoundLabels.ToSharedRef());
	SoundLabelHud->Arm(GetWorld());
#endif
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this);
	if (!IsValid(Bus))
	{
		return;
	}
	TArray<EUmbrellaEventType> Listened = UmbrellaCueTable::ListenedEvents();
	for (const EUmbrellaEventType Type : CuedEvents)
	{
		Listened.AddUnique(Type);
	}
	for (const EUmbrellaEventType Type : Listened)
	{
		Handles.Emplace(Type, Bus->On(Type).AddUObject(this, &UUmbrellaCueSubsystem::HandleEvent));
	}
}

#if UMBRELLAELLA_WORKBENCH
void UUmbrellaCueSubsystem::NoteSoundLabel(FName Id, int32 Take)
{
	if (SoundLabels.IsValid())
	{
		SoundLabels->Note(Id, LabelEvent.IsEmpty() ? FString(TEXT("Direct")) : LabelEvent, Take);
	}
}
#endif

void UUmbrellaCueSubsystem::Deinitialize()
{
#if UMBRELLAELLA_WORKBENCH
	if (SoundLabelHud.IsValid())
	{
		SoundLabelHud->Detach();
	}
	SoundLabelHud.Reset();
	SoundLabels.Reset();
#endif
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this);
	if (IsValid(Bus))
	{
		for (const TPair<EUmbrellaEventType, FDelegateHandle>& Handle : Handles)
		{
			Bus->On(Handle.Key).Remove(Handle.Value);
		}
	}
	Handles.Reset();
	for (TPair<FName, TObjectPtr<UAudioComponent>>& Loop : ActiveLoops)
	{
		if (IsValid(Loop.Value))
		{
			Loop.Value->Stop();
		}
	}
	ActiveLoops.Reset();
	StopMusic();
	MusicComponent = nullptr;
	Super::Deinitialize();
}

FName UUmbrellaCueSubsystem::CueForEvent(const FUmbrellaEvent& Event)
{
	switch (Event.Type)
	{
	case EUmbrellaEventType::ProjectileSpawned:
		return TEXT("Shot");
	case EUmbrellaEventType::ProjectileContact:
		return TEXT("Hit");
	case EUmbrellaEventType::CatchSucceeded:
		return TEXT("Absorb");
	case EUmbrellaEventType::CatchFailed:
		return TEXT("AbsorbFail");
	case EUmbrellaEventType::BossTargetHit:
		// Regular enemy hits share the event; only Keeper hits get the Keeper cue.
		return Event.Detail == TEXT("Enemy") ? FName(TEXT("Hit")) : FName(TEXT("KeeperHit"));
	case EUmbrellaEventType::BossAttackTelegraphed:
		return TEXT("KeeperAttack");
	case EUmbrellaEventType::PlayerDefeated:
		return TEXT("EndMusic");
	case EUmbrellaEventType::EncounterCompleted:
		return TEXT("EndMusic");
	case EUmbrellaEventType::ModeSelected:
		return TEXT("StartMusic");
	case EUmbrellaEventType::LevelGained:
		return TEXT("LevelUp");
	default:
		return NAME_None;
	}
}

void UUmbrellaCueSubsystem::HandleEvent(const FUmbrellaEvent& Event)
{
#if UMBRELLAELLA_WORKBENCH
	LabelEvent = StaticEnum<EUmbrellaEventType>()->GetNameStringByValue(static_cast<int64>(Event.Type));
	ON_SCOPE_EXIT { LabelEvent.Reset(); };
#endif
	const FName PrevDetail = PrevDetails.FindRef(Event.Type);
	for (const FUmbrellaLoopGroupStop& Stop : UmbrellaCueTable::GroupStops())
	{
		if (Stop.Event == Event.Type)
		{
			StopLoopGroup(Stop.Group);
		}
	}
	bool bPlayedFromTable = false;
	for (const FUmbrellaSoundCue* Row : UmbrellaCueTable::ForEvent(Event, PrevDetail))
	{
		bool bRowPlayed = false;
		PlayRow(*Row, bRowPlayed);
		bPlayedFromTable |= bRowPlayed;
	}
	// Only Details some row matches on are remembered (UmbrellaConfigChanged also carries spell equips).
	for (const FUmbrellaSoundCue& Row : UmbrellaCueTable::All())
	{
		if (Row.Event == Event.Type && (Row.Match == EUmbrellaCueMatch::Detail || Row.Match == EUmbrellaCueMatch::LeftDetail)
			&& Event.Detail == FName(Row.Value))
		{
			PrevDetails.Add(Event.Type, Event.Detail);
			break;
		}
	}
	const FName Cue = CueForEvent(Event);
	if (Cue.IsNone())
	{
		return;
	}
	LastCue = Cue;
	++CueCount;
	if (bPlayedFromTable)
	{
		// The per-sound takes played; the flat placeholder cue asset stays silent.
		return;
	}
	// Sound assets live at /Game/UmbrellaElla/Audio/<Cue>; absent until generated, so a miss is silent.
	const FString Path = FString::Printf(TEXT("/Game/UmbrellaElla/Audio/%s.%s"), *Cue.ToString(), *Cue.ToString());
	if (USoundBase* Sound = LoadObject<USoundBase>(nullptr, *Path, nullptr, LOAD_Quiet | LOAD_NoWarn))
	{
#if UMBRELLAELLA_WORKBENCH
		NoteSoundLabel(Cue, 0);
#endif
		if (IsMusicCue(Cue))
		{
			RestartMusic(Sound);
		}
		else
		{
			if (Cue == TEXT("EndMusic"))
			{
				// The end sting replaces the music instead of playing over it.
				StopMusic();
			}
			UGameplayStatics::PlaySound2D(this, Sound);
		}
	}
}

bool UUmbrellaCueSubsystem::IsMusicCue(FName Cue)
{
	return Cue == TEXT("StartMusic");
}

void UUmbrellaCueSubsystem::StopMusic()
{
	if (IsValid(MusicComponent))
	{
		MusicComponent->Stop();
	}
}

void UUmbrellaCueSubsystem::RestartMusic(USoundBase* Sound)
{
	StopMusic();
	if (!IsValid(Sound))
	{
		return;
	}
	if (!IsValid(MusicComponent))
	{
		// One persistent, non-auto-destroy component: a mode change reuses it instead of orphaning a fire-and-forget sound.
		MusicComponent = UGameplayStatics::CreateSound2D(this, Sound, 1.0f, 1.0f, 0.0f, nullptr, true, false);
	}
	else
	{
		MusicComponent->SetSound(Sound);
	}
	if (IsValid(MusicComponent))
	{
		MusicComponent->Play();
		++MusicStartCount;
	}
}

void UUmbrellaCueSubsystem::PlaySoundById(FName Id)
{
	if (const FUmbrellaSoundCue* Row = UmbrellaCueTable::Find(Id))
	{
		bool bPlayed = false;
		PlayRow(*Row, bPlayed);
	}
}

bool UUmbrellaCueSubsystem::CanPlaySound(FName Id) const
{
	const FUmbrellaSoundCue* Row = UmbrellaCueTable::Find(Id);
	return Row && HasTakes(*Row);
}

void UUmbrellaCueSubsystem::StopLoopGroup(const FString& Group)
{
	for (const FUmbrellaSoundCue& Row : UmbrellaCueTable::All())
	{
		if (Group == Row.LoopGroup)
		{
			if (TObjectPtr<UAudioComponent>* Loop = ActiveLoops.Find(FName(Row.Id)))
			{
				if (IsValid(*Loop))
				{
					(*Loop)->Stop();
				}
				ActiveLoops.Remove(FName(Row.Id));
			}
		}
	}
}

bool UUmbrellaCueSubsystem::HasTakes(const FUmbrellaSoundCue& Cue) const
{
	return !LoadTakes(Cue).IsEmpty();
}

void UUmbrellaCueSubsystem::PlayRow(const FUmbrellaSoundCue& Cue, bool& bOutPlayed)
{
	bOutPlayed = false;
	// Takes are SW_<Id>_NN under /Game/UmbrellaElla/Audio/<Id>/ (tools/build/assets/arena_audio_import.py).
	const TArray<USoundBase*> Takes = LoadTakes(Cue);
	if (Takes.IsEmpty())
	{
		return;
	}
	if (FCString::Strlen(Cue.LoopGroup) > 0)
	{
		StopLoopGroup(Cue.LoopGroup);
	}
	USoundBase* Sound = Takes[CueRandom.RandHelper(Takes.Num())];
	bOutPlayed = true;
#if UMBRELLAELLA_WORKBENCH
	NoteSoundLabel(FName(Cue.Id), FUmbrellaSoundLabelBoard::TakeFromAssetName(Sound->GetName()));
#endif
	LastSoundId = FName(Cue.Id);
	++SoundCueCount;
	if (Cue.SoundClass == EUmbrellaCueClass::Music && Cue.bLoop)
	{
		RestartMusic(Sound);
		return;
	}
	const float Pitch = 1.0f + CueRandom.FRandRange(-Cue.PitchJitter, Cue.PitchJitter);
	USoundConcurrency* Concurrency = nullptr;
	if (FCString::Strlen(Cue.Concurrency) > 0)
	{
		const FString Path = FString::Printf(TEXT("/Game/UmbrellaElla/Audio/Core/%s.%s"), Cue.Concurrency, Cue.Concurrency);
		Concurrency = LoadObject<USoundConcurrency>(nullptr, *Path, nullptr, LOAD_Quiet | LOAD_NoWarn);
	}
	UAudioComponent* Component = UGameplayStatics::CreateSound2D(this, Sound, 1.0f, Pitch, 0.0f, Concurrency, false, !Cue.bLoop);
	if (!IsValid(Component))
	{
		return;
	}
	const FString ClassName = UmbrellaCueTable::ClassAssetName(Cue.SoundClass);
	Component->SoundClassOverride = LoadObject<USoundClass>(
		nullptr, *FString::Printf(TEXT("/Game/UmbrellaElla/Audio/Core/%s.%s"), *ClassName, *ClassName), nullptr, LOAD_Quiet | LOAD_NoWarn);
	Component->Play();
	if (Cue.bLoop)
	{
		ActiveLoops.Add(FName(Cue.Id), Component);
	}
}
