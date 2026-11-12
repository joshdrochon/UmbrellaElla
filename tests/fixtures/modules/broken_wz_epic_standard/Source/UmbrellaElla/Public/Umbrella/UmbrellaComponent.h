#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "UmbrellaComponent.generated.h"

class UPaperFlipbook;

// Planted on purpose: each line below breaks one rule of Epic's coding standard.
class UMBRELLAELLA_API WindThing : public UObject
{
};

struct UMBRELLAELLA_API WindData
{
	float Strength;
};

UENUM()
enum class umbrellaMode : int32
{
	Open
};

UENUM(BlueprintType)
enum EUmbrellaState
{
	Closed,
	Opened
};

UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UUmbrellaComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UUmbrellaComponent();

	UFUNCTION(BlueprintCallable)
	void SetOpen(bool bNewOpen);

	bool IsOpen() const { return bOpen; }

	float GetSpeed() { return 0.f; }
	const FVector GetWind() const;
	void Absorb(UObject& Thing);
	bool bPublicState = false;

	// A raw pointer in a comment must not count: UPaperFlipbook* OldFlipbook;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

protected:
	UPROPERTY(EditDefaultsOnly, Category = "Umbrella")
	TObjectPtr<UPaperFlipbook> OpenFlipbook;

private:
	UPROPERTY(Transient)
	TWeakObjectPtr<AActor> LastWindSource;

	bool bOpen = false;
	float speed_value = 0.f;
	FTimerHandle H2;
};
