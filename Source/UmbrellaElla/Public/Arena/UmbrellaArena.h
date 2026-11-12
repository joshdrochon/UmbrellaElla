#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UmbrellaArena.generated.h"

/** Camera yaw so it looks down -Y (larger Y is nearer). */
namespace UmbrellaArenaConst
{
	static constexpr double CameraYaw = -90.0;
	/** Engine cube edge length in units. */
	static constexpr float CubeSize = 100.0f;
	static constexpr double PlaneThickness = 0.01;
	static constexpr double KeeperDepthScale = 0.1;
}

class UCameraComponent;
class UBoxComponent;
class USceneComponent;
class UStaticMeshComponent;

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

	/** Placeholder visuals from engine primitives; art replaces them later. */
	UPROPERTY(VisibleAnywhere, Category = "Arena")
	TObjectPtr<UStaticMeshComponent> BackgroundFar;

	UPROPERTY(VisibleAnywhere, Category = "Arena")
	TObjectPtr<UStaticMeshComponent> BackgroundNear;

	UPROPERTY(VisibleAnywhere, Category = "Arena")
	TObjectPtr<UStaticMeshComponent> KeeperStandIn;

public:
	UStaticMeshComponent* GetKeeperStandIn() const { return KeeperStandIn; }
	UStaticMeshComponent* GetBackgroundFar() const { return BackgroundFar; }

	/** Create the placeholder visuals (also called from BeginPlay). */
	void BuildPlaceholders();

private:
	float FarOffset = 0.0f;
	float NearOffset = 0.0f;
};
