#pragma once

#include "CoreMinimal.h"
#include "BrokenMillTuning.generated.h"

/**
 * Every number of the Broken Mill one-room test (lane enemies): GDD SH1.0 proposed adjustable prototype defaults.
 * Room coordinates are the room's own: origin bottom-left, X right, Z up, 1 unit = 1 cm.
 * Not a member of UUmbrellaTuning yet (see docs/build/requests/enemies.md): read as FBrokenMillTuning().
 */
USTRUCT()
struct UMBRELLAELLA_API FBrokenMillTuning
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Room")
	FVector2D RoomSize = FVector2D(1920.0, 1080.0);

	UPROPERTY(EditAnywhere, Category = "Room")
	FVector2D RotorCentre = FVector2D(1120.0, 760.0);

	UPROPERTY(EditAnywhere, Category = "Room")
	float RotorRadius = 150.0f;

	UPROPERTY(EditAnywhere, Category = "Room")
	FVector2D IslandXRange = FVector2D(1350.0, 1570.0);

	UPROPERTY(EditAnywhere, Category = "Room")
	float IslandTop = 390.0f;

	UPROPERTY(EditAnywhere, Category = "Room")
	float IslandUnderside = 350.0f;

	UPROPERTY(EditAnywhere, Category = "Room")
	FVector2D GuardMuzzle = FVector2D(1410.0, 480.0);

	UPROPERTY(EditAnywhere, Category = "Room")
	FVector2D TargetCentre = FVector2D(1440.0, 455.0);

	UPROPERTY(EditAnywhere, Category = "Room")
	FVector2D TargetSize = FVector2D(60.0, 130.0);

	/** Floor height under the underpass. */
	UPROPERTY(EditAnywhere, Category = "Room")
	float FloorTop = 80.0f;

	UPROPERTY(EditAnywhere, Category = "Guard")
	float GuardHp = 10.0f;

	/** Later comparison only, one changed variable. */
	UPROPERTY(EditAnywhere, Category = "Guard")
	float GuardHpComparison = 20.0f;

	UPROPERTY(EditAnywhere, Category = "Guard")
	float ContactDamage = 0.0f;

	/** Activation region x min/max and z min/max (enter from the left). */
	UPROPERTY(EditAnywhere, Category = "Guard")
	FVector2D ActivationX = FVector2D(500.0, 720.0);

	UPROPERTY(EditAnywhere, Category = "Guard")
	FVector2D ActivationZ = FVector2D(620.0, 690.0);

	UPROPERTY(EditAnywhere, Category = "Guard")
	float WarningSeconds = 1.1f;

	UPROPERTY(EditAnywhere, Category = "Guard")
	float ShotSpeed = 240.0f;

	UPROPERTY(EditAnywhere, Category = "Guard")
	float ShotRadius = 8.0f;

	UPROPERTY(EditAnywhere, Category = "Guard")
	float ShotDamage = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Guard")
	float ShotRange = 1000.0f;

	UPROPERTY(EditAnywhere, Category = "Guard")
	float RecoverySeconds = 1.5f;

	UPROPERTY(EditAnywhere, Category = "Guard")
	int32 MaxActiveEnemyBullets = 1;

	/** Winds: firing column, upper reset and lower onward eligibility z ranges. */
	UPROPERTY(EditAnywhere, Category = "Winds")
	FVector2D FiringColumnX = FVector2D(600.0, 800.0);

	UPROPERTY(EditAnywhere, Category = "Winds")
	FVector2D UpperResetZ = FVector2D(360.0, 480.0);

	UPROPERTY(EditAnywhere, Category = "Winds")
	FVector2D LowerOnwardZ = FVector2D(210.0, 330.0);

	UPROPERTY(EditAnywhere, Category = "Winds")
	FVector2D ExitPoint = FVector2D(1780.0, 500.0);

	/** Protected root core x min/max. */
	UPROPERTY(EditAnywhere, Category = "Winds")
	FVector2D ProtectedCoreX = FVector2D(260.0, 360.0);

	/** Local restoring gain and vertical compensation (not global tuning). */
	UPROPERTY(EditAnywhere, Category = "Winds")
	float LocalRestoringGain = 2.4f;

	UPROPERTY(EditAnywhere, Category = "Winds")
	float LocalVerticalCompensation = -78.0f;

	/** Missed-current low assist near this point sends Ella left and up. */
	UPROPERTY(EditAnywhere, Category = "Winds")
	FVector2D MissedCurrentAssistPoint = FVector2D(650.0, 150.0);

	UPROPERTY(EditAnywhere, Category = "Winds")
	float MissedCurrentAssistRadius = 100.0f;

	/** Ella estimates: max hurtbox half height and width, margin, and the shadow fixture's friendly fire. */
	UPROPERTY(EditAnywhere, Category = "Estimates")
	float MaxHalfHeight = 39.0f;

	UPROPERTY(EditAnywhere, Category = "Estimates")
	float MaxHalfWidth = 23.4f;

	UPROPERTY(EditAnywhere, Category = "Estimates")
	float FriendlyShotRadius = 6.0f;

	UPROPERTY(EditAnywhere, Category = "Estimates")
	float FriendlyShotSpeed = 700.0f;

	UPROPERTY(EditAnywhere, Category = "Estimates")
	float FriendlyShotsPerSecond = 5.0f;

	UPROPERTY(EditAnywhere, Category = "Estimates")
	float FriendlyDamage = 10.0f;

	UPROPERTY(EditAnywhere, Category = "Estimates")
	float FriendlyRange = 1500.0f;

	/** Shadow muzzle offset at HeroSize 1 (X, Z). Scales with HeroSize. */
	UPROPERTY(EditAnywhere, Category = "Estimates")
	FVector2D MuzzleOffset = FVector2D(44.0, 6.0);

	/** Island shot margin: the bullet lower edge must clear the island top by this much. */
	UPROPERTY(EditAnywhere, Category = "Estimates")
	float IslandShotMargin = 12.0f;

	/** Ordinary fall speed and trim. */
	UPROPERTY(EditAnywhere, Category = "Estimates")
	float FallSpeed = 330.0f;

	UPROPERTY(EditAnywhere, Category = "Estimates")
	float FallTrimFraction = 0.2f;

	UPROPERTY(EditAnywhere, Category = "Estimates")
	float RayEndX = 421.6f;

	/** Depth (Y) half extent and placeholder depth scale for room boxes. */
	UPROPERTY(EditAnywhere, Category = "Placeholder")
	float DepthHalfExtent = 50.0f;
};
