#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UmbrellaArena.generated.h"

/** Camera yaw so it looks down -Y (larger Y is nearer). */
namespace UmbrellaArenaConst
{
	static constexpr double CameraYaw = -90.0;
}

class UCameraComponent;
class UBoxComponent;
class USceneComponent;

/** The Keeper arena: bounds, play camera (fixed 16:9), Ella start and Keeper anchor (CAM, WIND, HAZ, BG). Flow spawns one if the map has none. Lane e. */
UCLASS()
class UMBRELLAELLA_API AUmbrellaArena : public AActor
{
	GENERATED_BODY()

public:
	AUmbrellaArena();

	/** World position of the arena point at (XFraction, ZFraction) of its width and height, from the bottom-left corner. */
	FVector LocalPoint(float XFraction, float ZFraction) const;

	FVector GetPlayerStartLocation() const;
	FVector GetKeeperAnchorLocation() const;
	UCameraComponent* GetPlayCamera() const { return PlayCamera; }

	/** Advance a looping background offset; returns true when it wrapped (BackgroundLooped). */
	static bool HasWrappedAfterAdvance(float& Offset, float Speed, float DeltaTime, float Period);

	virtual void Tick(float DeltaSeconds) override;

protected:
	virtual void BeginPlay() override;

private:
	void BroadcastLooped(FName Layer) const;

	UPROPERTY(VisibleAnywhere, Category = "Arena")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, Category = "Arena")
	TObjectPtr<UCameraComponent> PlayCamera;

	UPROPERTY(VisibleAnywhere, Category = "Arena")
	TObjectPtr<UBoxComponent> LeftWall;

	UPROPERTY(VisibleAnywhere, Category = "Arena")
	TObjectPtr<UBoxComponent> RightWall;

	UPROPERTY(VisibleAnywhere, Category = "Arena")
	TObjectPtr<UBoxComponent> Ceiling;

	/** Lethal bottom boundary: overlap only; the health lane decides what it does . */
	UPROPERTY(VisibleAnywhere, Category = "Arena")
	TObjectPtr<UBoxComponent> LethalBottom;

	float FarOffset = 0.0f;
	float NearOffset = 0.0f;
};
