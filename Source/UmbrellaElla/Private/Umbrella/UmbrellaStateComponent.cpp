#include "Umbrella/UmbrellaStateComponent.h"
#include "Core/UmbrellaEventBus.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Umbrella/UmbrellaPlayerIds.h"

UUmbrellaStateComponent::UUmbrellaStateComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UUmbrellaStateComponent::BindInput(UEnhancedInputComponent* Input)
{
	// Holds arrive through the Input Adapter; nothing to bind here.
}

void UUmbrellaStateComponent::SetShootHeld(bool bHeld)
{
	bShootHeld = bHeld;
	if (!bHeld)
	{
		bShootAwaitNeutral = false;
	}
	Refresh();
}

void UUmbrellaStateComponent::SetAbsorbHeld(bool bHeld)
{
	bAbsorbHeld = bHeld;
	if (!bHeld)
	{
		bAbsorbAwaitNeutral = false;
	}
	Refresh();
}

void UUmbrellaStateComponent::SetRideHeld(bool bHeld)
{
	bRideHeld = bHeld;
	if (!bHeld)
	{
		bRideAwaitNeutral = false;
	}
	Refresh();
}

void UUmbrellaStateComponent::SetLocked(bool bLocked)
{
	if (bLocked == bInputLocked)
	{
		return;
	}
	bInputLocked = bLocked;
	if (!bLocked)
	{
		// The press that ended the lock (a menu confirm, a held trigger) must be let go before it counts.
		bShootAwaitNeutral = bShootHeld;
		bAbsorbAwaitNeutral = bAbsorbHeld;
		bRideAwaitNeutral = bRideHeld;
	}
	Refresh();
}

void UUmbrellaStateComponent::Refresh()
{
	if (!IsFeatureEnabled(EFeatureId::MOVE_19))
	{
		return;
	}
	// MOVE-19: locks resolve before player actions; then Shoot and Absorb pick one of four modes.
	Transition(UmbrellaActionRules::ResolveAction(IsShootHeld(), IsAbsorbHeld()));
}

void UUmbrellaStateComponent::Transition(EUmbrellaAction NewAction)
{
	if (NewAction == Action)
	{
		return;
	}
	Action = NewAction;
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::UmbrellaConfigChanged;
		Event.SourceId = UmbrellaPlayerIds::Ella;
		Event.Detail = UmbrellaActionRules::ActionName(Action);
		Event.Amount = static_cast<int32>(Action);
		Bus->Broadcast(Event);
	}
}
