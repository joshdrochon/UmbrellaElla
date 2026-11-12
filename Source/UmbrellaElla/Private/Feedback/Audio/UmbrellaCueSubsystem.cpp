#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

namespace
{
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
	};
}

void UUmbrellaCueSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Collection.InitializeDependency<UUmbrellaEventBus>();
	Super::Initialize(Collection);
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this);
	if (!IsValid(Bus))
	{
		return;
	}
	for (const EUmbrellaEventType Type : CuedEvents)
	{
		Handles.Add(Bus->On(Type).AddUObject(this, &UUmbrellaCueSubsystem::HandleEvent));
	}
}

void UUmbrellaCueSubsystem::Deinitialize()
{
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this);
	if (IsValid(Bus))
	{
		for (int32 Index = 0; Index < Handles.Num(); ++Index)
		{
			Bus->On(CuedEvents[Index]).Remove(Handles[Index]);
		}
	}
	Handles.Reset();
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
		return TEXT("KeeperHit");
	case EUmbrellaEventType::BossAttackTelegraphed:
		return TEXT("KeeperAttack");
	case EUmbrellaEventType::PlayerDefeated:
		return TEXT("EndMusic");
	case EUmbrellaEventType::EncounterCompleted:
		return TEXT("EndMusic");
	case EUmbrellaEventType::ModeSelected:
		return TEXT("StartMusic");
	default:
		return NAME_None;
	}
}

void UUmbrellaCueSubsystem::HandleEvent(const FUmbrellaEvent& Event)
{
	const FName Cue = CueForEvent(Event);
	if (Cue.IsNone())
	{
		return;
	}
	LastCue = Cue;
	++CueCount;
	// Sound assets live at /Game/UmbrellaElla/Audio/<Cue>; absent until generated, so a miss is silent.
	const FString Path = FString::Printf(TEXT("/Game/UmbrellaElla/Audio/%s.%s"), *Cue.ToString(), *Cue.ToString());
	if (USoundBase* Sound = LoadObject<USoundBase>(nullptr, *Path, nullptr, LOAD_Quiet | LOAD_NoWarn))
	{
		UGameplayStatics::PlaySound2D(this, Sound);
	}
}
