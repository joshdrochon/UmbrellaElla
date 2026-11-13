#pragma once

#include "CoreMinimal.h"

#if UMBRELLAELLA_WORKBENCH

#include "Containers/Ticker.h"
#include "InputCoreTypes.h"
#include "UObject/StrongObjectPtr.h"

class FUmbrellaSoundLabelBoard;
class SWidget;
class UEnhancedInputComponent;
class UInputAction;
class UInputMappingContext;
class UWorld;

/**
 * The F9 toggle and the on-screen list for the sound labels. Owns an Enhanced Input action (built in code, no asset),
 * its mapping context and a Slate list in the game viewport. Connect needs a local player; without one (tests) it
 * does nothing. Lane soundlabel.
 */
class UMBRELLAELLA_API FUmbrellaSoundLabelHud : public TSharedFromThis<FUmbrellaSoundLabelHud>
{
public:
	explicit FUmbrellaSoundLabelHud(TSharedRef<FUmbrellaSoundLabelBoard> InBoard);
	~FUmbrellaSoundLabelHud();

	/** Starts the per-frame tick (needs to be owned by a TSharedPtr) (ages the lines) and keeps trying to Connect until the world has a local player. */
	void Arm(UWorld* World);
	/** Maps F9 and adds the list to the viewport; does nothing without a local player controller (IsAttached says). */
	void Connect(UWorld* World);
	void Detach();
	bool IsAttached() const { return bConnected; }

	/** The key that flips the list. */
	static FKey GetToggleKey();

private:
	void OnFrame(float DeltaSeconds);

	TSharedRef<FUmbrellaSoundLabelBoard> Board;
	TStrongObjectPtr<UInputAction> ToggleAction;
	TStrongObjectPtr<UInputMappingContext> Context;
	TStrongObjectPtr<UEnhancedInputComponent> InputComponent;
	TWeakObjectPtr<UWorld> AttachedWorld;
	TSharedPtr<SWidget> ListWidget;
	FTSTicker::FDelegateHandle TickHandle;
	bool bConnected = false;
	bool bArmed = false;
};

#endif // UMBRELLAELLA_WORKBENCH
