#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaEvent.h"
#include "Subsystems/WorldSubsystem.h"
#include "UmbrellaEventBus.generated.h"

DECLARE_MULTICAST_DELEGATE_OneParam(FOnUmbrellaEvent, const FUmbrellaEvent&);

/**
 * Modules talk through this bus (Core, TD-owned): one native multicast delegate per manifest event, per world.
 * Subscribe in BeginPlay and remove the handle in EndPlay (rule F). Broadcast stamps Frame.
 */
UCLASS()
class UMBRELLAELLA_API UUmbrellaEventBus final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	static UUmbrellaEventBus* Get(const UObject* WorldContext);

	FOnUmbrellaEvent& On(EUmbrellaEventType Type);

	void Broadcast(const FUmbrellaEvent& Event);

private:
	TArray<FOnUmbrellaEvent> Delegates;
};
