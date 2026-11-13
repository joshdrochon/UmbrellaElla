#pragma once

#include "CoreMinimal.h"
#include "Engine/Scene.h"
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
	/** Min = max auto-exposure brightness: exposure never adapts, so a flat unlit frame keeps its authored values. */
	static constexpr float FixedExposureBrightness = 1.0f;
	/** Unlit colour of the arena's own background stand-in panels (dark paper, behind all gameplay). */
	static const FLinearColor BackgroundStandInColor(0.10f, 0.095f, 0.085f, 1.0f);
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
	/** World-relative X of a scrolling plane's center for a loop offset. */
	static float PlaneCenterX(float Offset, float ArenaWidth, float WidthScale);

	/** Move both background planes to their current offsets. */
	void ApplyScroll();

	static bool HasWrappedAfterAdvance(float& Offset, float Speed, float DeltaTime, float Period);

	virtual void Tick(float DeltaSeconds) override;

	/** Director's Cut scroll: lead the camera toward the travel direction (-1, 0, +1) along the route. No-op when the camera flag is off. */
	void FollowEllaX(float EllaX, int32 TravelDirection);

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
	UStaticMeshComponent* GetBackgroundNear() const { return BackgroundNear; }

	/** Create the placeholder visuals (also called from BeginPlay). */
	void BuildPlaceholders();

	/**
	 * Presentation only: Keeper slot art draws, so the graybox Keeper square hides (it sits in front of every Keeper
	 * layer). False shows it again. Survives BuildPlaceholders.
	 */
	void SetKeeperArtShown(bool bShown);
	bool IsKeeperArtShown() const { return bKeeperArtShown; }

	/** The unlit 2D look for the play camera: fixed exposure, no bloom, motion blur, vignette or grain. Pure settings. */
	static void ApplyFlatLookPostProcess(FPostProcessSettings& Settings);

private:
	float FarOffset = 0.0f;
	float NearOffset = 0.0f;
	bool bKeeperArtShown = false;
};
