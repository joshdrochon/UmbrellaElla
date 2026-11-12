#pragma once

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

class AEllaCharacter;
class UWorld;

/**
 * Shared world-test helper (move lane, reused by other areas): a transient game world with BeginPlay run, Ella
 * spawning, and a fixed-delta tick. Create one per test on the stack; it destroys the world when it goes away.
 */
class FUmbrellaTestWorld
{
public:
	FUmbrellaTestWorld();
	~FUmbrellaTestWorld();

	FUmbrellaTestWorld(const FUmbrellaTestWorld&) = delete;
	FUmbrellaTestWorld& operator=(const FUmbrellaTestWorld&) = delete;

	UWorld* GetWorld() const { return World; }

	/** Spawn Ella (components run BeginPlay). Returns nullptr if the world refuses. */
	AEllaCharacter* SpawnElla(const FVector& Location = FVector::ZeroVector);

	/** Tick the world Frames times at DeltaSeconds each. */
	void TickFrames(int32 Frames, float DeltaSeconds);

	/** Tick for about Seconds of game time at DeltaSeconds per frame (rounded to whole frames). */
	void TickSeconds(float Seconds, float DeltaSeconds);

	/** How many actors of a class exist in the world. */
	template <typename ActorType>
	int32 CountActors() const;

private:
	UWorld* World = nullptr;
};

#endif
