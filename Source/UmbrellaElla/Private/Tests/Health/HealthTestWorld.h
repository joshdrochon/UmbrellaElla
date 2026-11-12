#pragma once

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/WorldSettings.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Health/UmbrellaHealthComponent.h"

#if WITH_AUTOMATION_TESTS

/** A transient game world with Ella and an event counter, torn down on scope exit. Health lane test helper. */
class FHealthTestWorld
{
public:
	FHealthTestWorld()
	{
		World = UWorld::CreateWorld(EWorldType::Game, false);
		FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
		Context.SetCurrentWorld(World);
		const FURL Url;
		World->InitializeActorsForPlay(Url);
		World->BeginPlay();
		if (!World->HasBegunPlay())
		{
			// No game mode in a bare test world: start play so spawned actors and their components run BeginPlay.
			World->GetWorldSettings()->NotifyBeginPlay();
			World->GetWorldSettings()->NotifyMatchStarted();
		}

		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Ella = World->SpawnActor<AEllaCharacter>(AEllaCharacter::StaticClass(), FTransform(FVector::ZeroVector), Params);
		if (Ella)
		{
			Ella->GetCharacterMovement()->DisableMovement();
		}
		for (int32 Index = 0; Index < static_cast<int32>(EUmbrellaEventType::Count); ++Index)
		{
			Counts.Add(0);
		}
		if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World))
		{
			for (int32 Index = 0; Index < static_cast<int32>(EUmbrellaEventType::Count); ++Index)
			{
				Handles.Add(Bus->On(static_cast<EUmbrellaEventType>(Index)).AddRaw(this, &FHealthTestWorld::OnEvent));
			}
		}
	}

	~FHealthTestWorld()
	{
		if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World))
		{
			for (int32 Index = 0; Index < Handles.Num(); ++Index)
			{
				Bus->On(static_cast<EUmbrellaEventType>(Index)).Remove(Handles[Index]);
			}
		}
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			It->RouteEndPlay(EEndPlayReason::Quit);
		}
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}

	FHealthTestWorld(const FHealthTestWorld&) = delete;
	FHealthTestWorld& operator=(const FHealthTestWorld&) = delete;

	int32 CountOf(EUmbrellaEventType Type) const { return Counts[static_cast<int32>(Type)]; }

	/** Run world time forward in frames of at most StepSeconds (world settings clamp one frame); Ella does not move. */
	void Step(float Seconds)
	{
		float Left = Seconds;
		while (Left > 0.0f)
		{
			const float Frame = FMath::Min(Left, StepSeconds);
			World->Tick(LEVELTICK_All, Frame);
			Left -= Frame;
		}
	}

	static constexpr float StepSeconds = 0.05f;

	UWorld* World = nullptr;
	AEllaCharacter* Ella = nullptr;

private:
	void OnEvent(const FUmbrellaEvent& Event) { Counts[static_cast<int32>(Event.Type)] += 1; }

	TArray<int32> Counts;
	TArray<FDelegateHandle> Handles;
};

#endif
