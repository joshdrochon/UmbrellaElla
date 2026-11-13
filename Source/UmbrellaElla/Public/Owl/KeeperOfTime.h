#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Encounter/KeeperFightModel.h"
#include "KeeperOfTime.generated.h"

class UKeeperPartComponent;
class UStaticMeshComponent;

/**
 * The Keeper of Time boss actor: wings, three hanging mechanisms, clock and eye. Spawned by the Encounter Director.
 * It holds the hit regions and a placeholder look made from engine primitives; every rule lives in FKeeperFightModel.
 * The director calls Refresh each tick so hit regions, heads and telegraphs follow the model, never an animation.
 */
UCLASS()
class UMBRELLAELLA_API AKeeperOfTime : public AActor
{
	GENERATED_BODY()

public:
	AKeeperOfTime();

	virtual void BeginPlay() override;

	/** Make the hit regions and the placeholder look match the model. */
	void Refresh(const FKeeperFightModel& Model, float TimeSeconds);

	/** A physical move started its warning: show the locked lane or target. */
	void ShowTelegraph(const FKeeperCommand& Command);

	/** Remove the visible gust front and telegraph marker. */
	void ClearGusts();

	/** Presentation only: rise and fade away alive over Seconds. */
	void BeginDeparture(float Seconds);

	/** The hit region of a body part (nullptr for Count). Tests read it. */
	UKeeperPartComponent* GetPartComponent(EKeeperPart Part) const;

	/** The moving head of a mechanism cast. */
	UKeeperPartComponent* GetHeadComponent(EKeeperPart Part) const;

	bool IsDeparting() const { return DepartureRemaining > 0.0f; }

	/**
	 * Presentation only: slot art now draws this part (the body sprite or the part's own layer), so its stand-in cube
	 * stays hidden. A stand-in shows only when no art does. Hit regions are unchanged.
	 */
	void SetPartArtDrawn(EKeeperPart Part, bool bDrawn);
	bool IsPartArtDrawn(EKeeperPart Part) const;

	/** The stand-in cube for a body part (nullptr for parts without one). Tests read it. */
	UStaticMeshComponent* GetStandInVisual(EKeeperPart Part) const;

	virtual void Tick(float DeltaSeconds) override;

private:
	UKeeperPartComponent* MakePart(FName Name, EKeeperPart Part, const FVector2D& Offset, const FVector2D& HalfExtent);
	UStaticMeshComponent* MakeVisual(FName Name);
	void PlaceVisual(UStaticMeshComponent* Visual, const FVector2D& Centre, const FVector2D& HalfExtent, const FLinearColor& Colour);
	void HideVisual(UStaticMeshComponent* Visual);
	FVector ToWorld(const FVector2D& Position) const;
	bool IsCoveredByArt(const UStaticMeshComponent* Visual) const;

	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> WingsPart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> ClockPart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> EyePart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> FrontPart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> MiddlePart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> RearPart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> FrontHead;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> MiddleHead;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> RearHead;

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> WingsVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> ClockVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> EyeVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> FrontVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> MiddleVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> RearVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> HeadVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> TalonVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> GustVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> TelegraphVisual;

	FVector2D AnchorXZ = FVector2D::ZeroVector;
	FVector2D TelegraphFrom = FVector2D::ZeroVector;
	FVector2D TelegraphTo = FVector2D::ZeroVector;
	bool bTelegraphShown = false;
	/** One bit per EKeeperPart whose slot art draws. */
	uint8 ArtDrawnParts = 0;
	float DepartureRemaining = 0.0f;
	float DepartureTotal = 0.0f;
};
