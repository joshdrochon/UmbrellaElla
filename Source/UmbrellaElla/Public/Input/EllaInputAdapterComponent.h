#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Input/UmbrellaInputBindings.h"
#include "EllaInputAdapterComponent.generated.h"

class UEnhancedInputComponent;
class UInputAction;
class UInputMappingContext;
class USettingsMenuSubsystem;
struct FInputActionValue;

/**
 * Input Adapter: adds IMC_Default (priority 0) and maps holds to requested actions; no physics. The IA_* actions and
 * the context are built in C++ at runtime from UmbrellaInputBindings::BuildDefaults() (no .uasset to lose in a merge).
 * Lane a.
 */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UEllaInputAdapterComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UEllaInputAdapterComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Adds IMC_Default and binds every IA_*. */
	void BindInput(UEnhancedInputComponent* Input);

	/** Build the IA_* actions and IMC_Default once. Safe to call again. */
	void BuildInputAssets();

	/** Rebuild IMC_Default's keys from the settings subsystem's saved bindings. Returns mappings made; 0 when Settings is null. */
	int32 ApplySavedBindings(const USettingsMenuSubsystem* Settings);

	UInputMappingContext* GetMappingContext() const { return MappingContext; }
	UInputAction* GetInputAction(EUmbrellaInputAction Action) const;

	/** The routing the bound handlers call. Tests call these directly. */
	void ApplyPress(EUmbrellaInputAction Action);
	void ApplyRelease(EUmbrellaInputAction Action);
	void ApplyAxis(EUmbrellaInputAction Action, float Value);

protected:
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	void HandlePressed(const FInputActionValue& Value, EUmbrellaInputAction Action);
	void HandleReleased(const FInputActionValue& Value, EUmbrellaInputAction Action);
	void HandleAxis(const FInputActionValue& Value, EUmbrellaInputAction Action);

	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> MappingContext;

	/** Indexed by EUmbrellaInputAction. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UInputAction>> InputActions;
};
