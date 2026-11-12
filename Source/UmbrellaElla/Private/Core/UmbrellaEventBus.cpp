#include "Core/UmbrellaEventBus.h"
#include "Engine/World.h"

void UUmbrellaEventBus::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	Delegates.SetNum(static_cast<int32>(EUmbrellaEventType::Count));
}

UUmbrellaEventBus* UUmbrellaEventBus::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	return World ? World->GetSubsystem<UUmbrellaEventBus>() : nullptr;
}

FOnUmbrellaEvent& UUmbrellaEventBus::On(EUmbrellaEventType Type)
{
	if (Delegates.Num() != static_cast<int32>(EUmbrellaEventType::Count))
	{
		Delegates.SetNum(static_cast<int32>(EUmbrellaEventType::Count));
	}
	return Delegates[static_cast<int32>(Type)];
}

void UUmbrellaEventBus::Broadcast(const FUmbrellaEvent& Event)
{
	FUmbrellaEvent Stamped = Event;
	Stamped.Frame = static_cast<int64>(GFrameCounter);
	On(Event.Type).Broadcast(Stamped);
}
