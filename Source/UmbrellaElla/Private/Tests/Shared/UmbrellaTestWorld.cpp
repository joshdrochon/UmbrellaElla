#include "Tests/Shared/UmbrellaTestWorld.h"

#if WITH_AUTOMATION_TESTS

#include "Core/EllaCharacter.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/WorldSettings.h"
#include "Projectile/UmbrellaProjectile.h"

FUmbrellaTestWorld::FUmbrellaTestWorld()
{
	World = UWorld::CreateWorld(EWorldType::Game, false, FName(TEXT("UmbrellaTestWorld")));
	if (!World || !GEngine)
	{
		return;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	World->InitializeActorsForPlay(FURL());
	World->BeginPlay();
	if (!World->HasBegunPlay())
	{
		// No game mode in a bare test world: start play on the world settings so spawned actors run BeginPlay and tick.
		World->GetWorldSettings()->NotifyBeginPlay();
		World->GetWorldSettings()->NotifyMatchStarted();
	}
}

FUmbrellaTestWorld::~FUmbrellaTestWorld()
{
	if (World && GEngine)
	{
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			It->RouteEndPlay(EEndPlayReason::Quit);
		}
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}
}

AEllaCharacter* FUmbrellaTestWorld::SpawnElla(const FVector& Location)
{
	if (!World)
	{
		return nullptr;
	}
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	return World->SpawnActor<AEllaCharacter>(AEllaCharacter::StaticClass(), FTransform(Location), Params);
}

void FUmbrellaTestWorld::TickFrames(int32 Frames, float DeltaSeconds)
{
	for (int32 Frame = 0; World && Frame < Frames; ++Frame)
	{
		// The tick manager skips a tick function it already ran in this engine frame; a test frame is a new frame.
		++GFrameCounter;
		World->Tick(LEVELTICK_All, DeltaSeconds);
	}
}

void FUmbrellaTestWorld::TickSeconds(float Seconds, float DeltaSeconds)
{
	TickFrames(FMath::RoundToInt(Seconds / DeltaSeconds), DeltaSeconds);
}

template <typename ActorType>
int32 FUmbrellaTestWorld::CountActors() const
{
	int32 Count = 0;
	for (TActorIterator<ActorType> It(World); It; ++It)
	{
		++Count;
	}
	return Count;
}

template int32 FUmbrellaTestWorld::CountActors<AUmbrellaProjectile>() const;

#endif
