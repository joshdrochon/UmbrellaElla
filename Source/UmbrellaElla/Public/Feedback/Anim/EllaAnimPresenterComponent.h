#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EllaAnimPresenterComponent.generated.h"

class UEnhancedInputComponent;
class UPaperFlipbook;
class UPaperFlipbookComponent;
class UStaticMeshComponent;

namespace UmbrellaPresenterConst
{
	/** Stand-in box scale: a slim figure. */
	static const FVector StandInScale(0.5, 0.1, 1.0);
}

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

protected:
	virtual void BeginPlay() override;

private:
	/** Art set on a Blueprint subclass or by Flow later; empty = stand-in. */
	UPROPERTY(EditDefaultsOnly, Category = "Art")
	TObjectPtr<UPaperFlipbook> IdleFlipbook;

	UPROPERTY()
	TObjectPtr<UPaperFlipbookComponent> Flipbook;

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> StandIn;
};
