#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "UmbrellaComponent.generated.h"

class UPaperFlipbook;

UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UUmbrellaComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UUmbrellaComponent();

	UFUNCTION(BlueprintCallable)
	void SetOpen(bool bNewOpen);

	bool IsOpen() const { return bOpen; }

	// A raw pointer in a comment must not count: UPaperFlipbook* OldFlipbook;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

protected:
	UPROPERTY(EditDefaultsOnly, Category = "Umbrella")
	UPaperFlipbook* OpenFlipbook;

private:
	UPROPERTY()
	AActor* WindSource = nullptr;

	UPROPERTY()
	TArray<UPaperFlipbook*> Frames;

	UPROPERTY()
	TMap<FName, AActor*> Lookup;

	UPROPERTY(Transient)
	TWeakObjectPtr<AActor> LastWindSource;

	bool bOpen = false;
};
