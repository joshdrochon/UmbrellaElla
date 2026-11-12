#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EllaAnimPresenterComponent.generated.h"

struct FUmbrellaEvent;
enum class EUmbrellaEventType : uint8;
class UEnhancedInputComponent;
class UPaperFlipbook;
class UPaperFlipbookComponent;
class UStaticMeshComponent;

namespace UmbrellaPresenterConst
{
	/** Stand-in box scale: a slim figure. */
	static const FVector StandInScale(0.5, 0.1, 1.0);
	/** Per-state stand-in shape multipliers (X, Y, Z). */
	static const FVector ShootMul(1.4, 1.0, 1.0);
	static const FVector AbsorbMul(1.8, 1.0, 0.8);
	static const FVector HurtMul(1.0, 1.0, 0.8);
}

/** What Ella is shown doing. Presentation only. */
UENUM()
enum class EEllaVisualState : uint8
{
	Idle,
	Shoot,
	Absorb,
	Hurt,
	Down
};

/** Animation Presenter: state to Paper2D flipbook, placeholder fallback. Never gameplay authority. Lane e. */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UEllaAnimPresenterComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UEllaAnimPresenterComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);

	/** True while a neutral stand-in shape is shown because no flipbook art is set. */
	bool IsShowingStandIn() const;

	/** Create the visual (flipbook if art is set, otherwise the stand-in). Safe to call twice. */
	void BuildVisual();

	UStaticMeshComponent* GetStandIn() const { return StandIn; }

	/** The visual state an event maps to for this owner; Idle means "no change". Only shots fired by the owner show Shoot. Pure, tests call it. */
	static EEllaVisualState StateForEvent(const FUmbrellaEvent& Event, FName OwnerId);

	/** Stand-in scale for a state (shape stands in for the flipbook of that state). */
	static FVector StandInScaleFor(EEllaVisualState State);

	/** Show a state; transient states return to Idle after the hold time. */
	void SetVisualState(EEllaVisualState State);
	EEllaVisualState GetVisualState() const { return VisualState; }

	/** Per-state flipbooks (set by art later); a state without one keeps the stand-in shape. */
	void SetStateFlipbook(EEllaVisualState State, UPaperFlipbook* Flipbook);

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

private:
	void HandleEvent(const FUmbrellaEvent& Event);
	void ApplyState();

	EEllaVisualState VisualState = EEllaVisualState::Idle;
	float StateTimeLeft = 0.0f;
	TMap<EEllaVisualState, TObjectPtr<UPaperFlipbook>> StateFlipbooks;
	TArray<TPair<EUmbrellaEventType, FDelegateHandle>> Handles;

	/** Art set on a Blueprint subclass or by Flow later; empty = stand-in. */
	UPROPERTY(EditDefaultsOnly, Category = "Art")
	TObjectPtr<UPaperFlipbook> IdleFlipbook;

	UPROPERTY()
	TObjectPtr<UPaperFlipbookComponent> Flipbook;

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> StandIn;
};
