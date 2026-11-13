#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BrokenMillIsland.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

/**
 * The Broken Mill's harmless solid island: its own actor with no shot receiver, so the projectile service treats it
 * as a solid stop for both shot channels (a friendly shot that lands on it never counts as a hit on the guard, and the
 * red shot ends on it). The room spawns and sizes it. Lane enemies.
 */
UCLASS()
class UMBRELLAELLA_API ABrokenMillIsland : public AActor
{
	GENERATED_BODY()

public:
	ABrokenMillIsland();

	/** Size the solid box (half extents X, depth, Z) and its placeholder cube. */
	void ConfigureBox(const FVector& HalfExtent, const FLinearColor& Color, float CubeSize, float DepthScale);

	UBoxComponent* GetBox() const { return Box; }
	UStaticMeshComponent* GetVisual() const { return Visual; }

private:
	UPROPERTY(VisibleAnywhere, Category = "BrokenMill")
	TObjectPtr<UBoxComponent> Box;

	UPROPERTY(VisibleAnywhere, Category = "BrokenMill")
	TObjectPtr<UStaticMeshComponent> Visual;
};
