#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Umbrella/UmbrellaAction.h"
#include "UmbrellaStateComponent.generated.h"

class UEnhancedInputComponent;

/**
 * Umbrella State: Ella's action-state enum and transitions. The only writer of the action enum is Transition();
 * the holds (Shoot, Absorb, Ride) arrive from the Input Adapter. A lock (pause, presentation, terminal) beats every
 * hold, and after it ends a hold must be released once before it counts again (resume waits for neutral input).
 * Lane a.
 */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UUmbrellaStateComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UUmbrellaStateComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);

	/** The raw hold of a button, as the device reports it. */
	void SetShootHeld(bool bHeld);
	void SetAbsorbHeld(bool bHeld);
	void SetRideHeld(bool bHeld);

	/** Pause / presentation / terminal lock. While locked the state is Rise with nothing held. */
	void SetLocked(bool bLocked);

	EUmbrellaAction GetAction() const { return Action; }
	bool IsLocked() const { return bInputLocked; }

	/** Holds as the rules see them: zero while locked or waiting for neutral. */
	bool IsShootHeld() const { return bShootHeld && !bShootAwaitNeutral && !bInputLocked; }
	bool IsAbsorbHeld() const { return bAbsorbHeld && !bAbsorbAwaitNeutral && !bInputLocked; }
	bool IsRideHeld() const { return bRideHeld && !bRideAwaitNeutral && !bInputLocked; }

private:
	/** The one function that changes Action. */
	void Transition(EUmbrellaAction NewAction);

	/** Recompute the effective holds and move to the matching action. */
	void Refresh();

	UPROPERTY(VisibleInstanceOnly, Category = "Umbrella")
	EUmbrellaAction Action = EUmbrellaAction::Rise;

	bool bShootHeld = false;
	bool bAbsorbHeld = false;
	bool bRideHeld = false;
	bool bShootAwaitNeutral = false;
	bool bAbsorbAwaitNeutral = false;
	bool bRideAwaitNeutral = false;
	bool bInputLocked = false;
};
