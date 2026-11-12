#pragma once

#include "CoreMinimal.h"
#include "KeeperTuning.generated.h"

/**
 * Every number of the Owl module: default, units and clamps (lane b). End a shipped default with // bake: <feature ID>.<param>.
 * Units: GDD world units = Unreal cm (D-new-sh10-units); time in seconds; speed in units/s; angles in degrees.
 * Lines without a bake marker are pipeline prototype defaults (D-new-sh10-open-details), not GDD numbers.
 */
USTRUCT()
struct UMBRELLAELLA_API FKeeperTuning
{
	GENERATED_BODY()

	// ---- Body and HP ----
	UPROPERTY(EditAnywhere, Category = "Body", meta = (ClampMin = "1"))
	float WingsHp = 180.0f; // bake: OWL-08.wings_hp
	UPROPERTY(EditAnywhere, Category = "Body", meta = (ClampMin = "1"))
	float FrontHp = 100.0f; // bake: OWL-08.front_hp
	UPROPERTY(EditAnywhere, Category = "Body", meta = (ClampMin = "1"))
	float MiddleHp = 110.0f; // bake: OWL-08.middle_hp
	UPROPERTY(EditAnywhere, Category = "Body", meta = (ClampMin = "1"))
	float RearHp = 120.0f; // bake: OWL-08.rear_hp
	UPROPERTY(EditAnywhere, Category = "Body", meta = (ClampMin = "1"))
	float ClockHp = 320.0f; // bake: OWL-08.clock_hp
	/** The clock cannot drop below this before the final phase (40% of 320). */
	UPROPERTY(EditAnywhere, Category = "Body", meta = (ClampMin = "0"))
	float ClockReserveHp = 128.0f; // bake: OWL-08.clock_reserve_hp

	// ---- Red pressure ----
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "0.1"))
	float RedIntervalSeconds = 1.35f; // bake: OWL-11.red_interval_s
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "0.1"))
	float ReducedIntervalSeconds = 2.16f; // bake: OWL-11.reduced_interval_s
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "0.01"))
	float RedSpacingSeconds = 0.09f; // bake: OWL-11.red_spacing_s
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "1"))
	int32 RedShotCount = 4;
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "1"))
	float RedSpeedWings = 240.0f; // bake: OWL-11.red_speed_wings
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "1"))
	float RedSpeedMechanisms = 270.0f; // bake: OWL-11.red_speed_mechanisms
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "1"))
	float RedSpeedClock = 300.0f; // bake: OWL-11.red_speed_clock
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "0"))
	float RedSpreadWingsDeg = 36.0f; // bake: OWL-11.red_spread_wings_deg
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "0"))
	float RedSpreadMechanismsDeg = 70.0f; // bake: OWL-11.red_spread_mechanisms_deg
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "0"))
	float RedSpreadClockDeg = 48.0f; // bake: OWL-11.red_spread_clock_deg
	/** Mechanisms phase fan axis: fixed to the left (180 degrees from +X). */
	UPROPERTY(EditAnywhere, Category = "Red")
	float FixedLeftAngleDeg = 180.0f;
	/** Combined hit-size factor per act (GDD section 5 table): 1.05 / 1.1025 / 1.155. */
	UPROPERTY(EditAnywhere, Category = "Red")
	float RedSizeWings = 1.05f;
	UPROPERTY(EditAnywhere, Category = "Red")
	float RedSizeMechanisms = 1.1025f;
	UPROPERTY(EditAnywhere, Category = "Red")
	float RedSizeClock = 1.155f;
	UPROPERTY(EditAnywhere, Category = "Red", meta = (ClampMin = "1"))
	float RedBaseRadius = 14.0f;
	/** First volley delay after the phase transition ends (encounter.json first_at). */
	UPROPERTY(EditAnywhere, Category = "Red")
	float RedFirstAtSeconds = 2.0f;
	/** After entering recovery the red countdown is at least this (the longer delay is preserved). */
	UPROPERTY(EditAnywhere, Category = "Red")
	float RedRecoveryMinSeconds = 0.6f;
	/** After entering recovery the yellow countdown is at most this. */
	UPROPERTY(EditAnywhere, Category = "Red")
	float YellowRecoveryMaxSeconds = 0.15f;

	// ---- Yellow ----
	UPROPERTY(EditAnywhere, Category = "Yellow", meta = (ClampMin = "0.1"))
	float YellowIntervalSeconds = 2.3f; // bake: OWL-13.yellow_interval_s
	UPROPERTY(EditAnywhere, Category = "Yellow", meta = (ClampMin = "1"))
	int32 YellowShotCount = 2;
	UPROPERTY(EditAnywhere, Category = "Yellow", meta = (ClampMin = "1"))
	float YellowSpeedWings = 180.0f; // bake: OWL-13.yellow_speed_wings
	UPROPERTY(EditAnywhere, Category = "Yellow", meta = (ClampMin = "1"))
	float YellowSpeedMechanisms = 195.0f; // bake: OWL-13.yellow_speed_mechanisms
	UPROPERTY(EditAnywhere, Category = "Yellow", meta = (ClampMin = "1"))
	float YellowSpeedClock = 210.0f; // bake: OWL-13.yellow_speed_clock
	UPROPERTY(EditAnywhere, Category = "Yellow", meta = (ClampMin = "0.1"))
	float YellowSize = 1.2f; // bake: OWL-13.yellow_size
	UPROPERTY(EditAnywhere, Category = "Yellow")
	float YellowFirstAtSeconds = 3.0f;

	// ---- Shared shot numbers ----
	/** Incoming damage of one red or yellow shot (health). */
	UPROPERTY(EditAnywhere, Category = "Shots")
	float ProjectileDamage = 1.0f; // bake: FLOW-33.projectile_damage
	/** Lifetime so a shot crosses the 1920-wide arena at the slowest speed. */
	UPROPERTY(EditAnywhere, Category = "Shots")
	float ShotLifetimeSeconds = 12.0f;

	// ---- Physical scheduler ----
	UPROPERTY(EditAnywhere, Category = "Physical", meta = (ClampMin = "0.1"))
	float PhysicalIntervalSeconds = 6.5f; // bake: OWL-15.physical_interval_s
	UPROPERTY(EditAnywhere, Category = "Physical")
	float GustFirstAtSeconds = 3.0f;
	UPROPERTY(EditAnywhere, Category = "Physical")
	float CastFirstAtSeconds = 2.5f;
	UPROPERTY(EditAnywhere, Category = "Physical")
	float TalonFirstAtSeconds = 2.0f;

	// ---- Wing gust ----
	UPROPERTY(EditAnywhere, Category = "Gust", meta = (ClampMin = "0.1"))
	float GustWarningSeconds = 1.1f; // bake: OWL-15.gust_warning_s
	UPROPERTY(EditAnywhere, Category = "Gust", meta = (ClampMin = "1"))
	float GustSpeed = 350.0f; // bake: OWL-16.gust_speed
	UPROPERTY(EditAnywhere, Category = "Gust", meta = (ClampMin = "1"))
	float GustBandWidth = 120.0f; // bake: OWL-16.gust_band_width
	UPROPERTY(EditAnywhere, Category = "Gust", meta = (ClampMin = "0.1"))
	float GustLifetimeSeconds = 3.0f; // bake: OWL-16.gust_lifetime_s
	UPROPERTY(EditAnywhere, Category = "Gust")
	float GustPush = 280.0f; // bake: OWL-16.gust_push
	/** Front thickness along its travel (open detail; the band width is the vertical extent). */
	UPROPERTY(EditAnywhere, Category = "Gust")
	float GustFrontThickness = 60.0f;
	UPROPERTY(EditAnywhere, Category = "Gust")
	float GustDamage = 1.0f;
	/** Recovery after the gust leaves the arena or expires (wing recovery follows the flap). */
	UPROPERTY(EditAnywhere, Category = "Gust")
	float GustRecoverySeconds = 1.0f;

	// ---- Talon ----
	UPROPERTY(EditAnywhere, Category = "Talon")
	float TalonReach = 270.0f; // bake: OWL-18.talon_reach
	UPROPERTY(EditAnywhere, Category = "Talon")
	float TalonWarningSeconds = 1.05f; // bake: OWL-18.talon_warning_s
	UPROPERTY(EditAnywhere, Category = "Talon")
	float TalonTipWidth = 48.0f; // bake: OWL-19.talon_tip_width
	UPROPERTY(EditAnywhere, Category = "Talon")
	float TalonStrikeSeconds = 0.18f; // bake: OWL-19.talon_strike_s
	UPROPERTY(EditAnywhere, Category = "Talon")
	float TalonRecoverySeconds = 1.0f; // bake: OWL-20.talon_recovery_s
	UPROPERTY(EditAnywhere, Category = "Talon")
	float TalonCooldownSeconds = 3.5f; // bake: OWL-20.talon_cooldown_s
	UPROPERTY(EditAnywhere, Category = "Talon")
	float TalonRearmExit = 370.0f; // bake: OWL-20.talon_rearm_exit
	UPROPERTY(EditAnywhere, Category = "Talon")
	float TalonDamage = 1.5f; // bake: FLOW-33.talon_damage

	// ---- Mechanism casts ----
	UPROPERTY(EditAnywhere, Category = "Cast")
	float CastWarningSeconds = 0.9f; // bake: OWL-21.cast_warning_s
	UPROPERTY(EditAnywhere, Category = "Cast")
	float ChainReach = 800.0f; // bake: OWL-22.chain_reach
	UPROPERTY(EditAnywhere, Category = "Cast")
	float ChainSpeed = 400.0f; // bake: OWL-22.chain_speed
	UPROPERTY(EditAnywhere, Category = "Cast")
	float ChainHeadWidth = 32.0f; // bake: OWL-22.chain_head_width
	UPROPERTY(EditAnywhere, Category = "Cast")
	float ChainReturnSeconds = 1.2f; // bake: OWL-23.chain_return_s
	UPROPERTY(EditAnywhere, Category = "Cast")
	float ChainDamage = 1.25f; // bake: FLOW-33.chain_damage
	UPROPERTY(EditAnywhere, Category = "Cast")
	float MiddleOffset = 80.0f; // bake: OWL-24.middle_offset
	UPROPERTY(EditAnywhere, Category = "Cast")
	float RearPauseSeconds = 0.65f; // bake: OWL-26.rear_pause_s

	// ---- Clock double beat ----
	UPROPERTY(EditAnywhere, Category = "Clock")
	float BeatRepeatWaitSeconds = 0.6f; // bake: OWL-28.repeat_wait_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float BeatRecoverySeconds = 0.85f; // bake: OWL-28.repeat_recovery_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float BeatFirstAtSeconds = 2.0f;

	// ---- Clock protection, slow, eye, stun ----
	UPROPERTY(EditAnywhere, Category = "Clock")
	float ClockOpenSeconds = 1.8f; // bake: OWL-29.clock_open_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float ClockProtectRecoverySeconds = 1.3f; // bake: OWL-29.clock_protect_recovery_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float FinalExposureSeconds = 1.9f; // bake: OWL-29.final_exposure_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float FinalExposureCycleSeconds = 4.8f; // bake: OWL-29.final_exposure_cycle_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float BreakStunSeconds = 1.2f; // bake: OWL-30.break_stun_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float FirePauseSeconds = 0.65f; // bake: OWL-30.fire_pause_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float SlowSeconds = 3.0f; // bake: OWL-31.slow_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float SlowWorldScale = 0.35f; // bake: OWL-31.slow_world_scale
	UPROPERTY(EditAnywhere, Category = "Clock")
	float SlowCooldownSeconds = 3.0f; // bake: OWL-31.slow_cooldown_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float EyeWindowSeconds = 2.0f; // bake: OWL-32.eye_window_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float EyeCooldownSeconds = 5.0f; // bake: OWL-32.eye_cooldown_s
	UPROPERTY(EditAnywhere, Category = "Clock")
	float BlackoutSeconds = 3.0f; // bake: OWL-32.blackout_s
	/** Baseline switches: slow on, eye-when-slow-off on. */
	UPROPERTY(EditAnywhere, Category = "Clock")
	bool bSlowEnabled = true;
	UPROPERTY(EditAnywhere, Category = "Clock")
	bool bEyeWhenSlowOff = true;

	// ---- Success ----
	UPROPERTY(EditAnywhere, Category = "Success")
	float DepartureSeconds = 2.5f; // bake: OWL-35.departure_s

	// ---- Placeholder body layout (cm from the Keeper anchor; X right, Z up) ----
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D WingsOffset = FVector2D(0.0f, 60.0f);
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D WingsHalfExtent = FVector2D(180.0f, 110.0f);
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D ClockOffset = FVector2D(0.0f, 0.0f);
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D ClockHalfExtent = FVector2D(70.0f, 70.0f);
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D EyeOffset = FVector2D(-20.0f, 25.0f);
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D EyeHalfExtent = FVector2D(22.0f, 22.0f);
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D FrontOffset = FVector2D(-130.0f, -110.0f);
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D MiddleOffsetPos = FVector2D(-10.0f, -140.0f);
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D RearOffset = FVector2D(110.0f, -110.0f);
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D MechanismHalfExtent = FVector2D(36.0f, 36.0f);
	/** Where the red volleys and yellow packets leave the body, and where the claw rests. */
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D MuzzleOffset = FVector2D(-60.0f, 10.0f);
	UPROPERTY(EditAnywhere, Category = "Layout")
	FVector2D ClawOffset = FVector2D(-100.0f, -40.0f);
	/** Hover bob of the whole body (cosmetic; collision follows the body). */
	UPROPERTY(EditAnywhere, Category = "Layout")
	float HoverAmplitude = 12.0f;
	UPROPERTY(EditAnywhere, Category = "Layout")
	float HoverHz = 0.35f;

	// ======== Regular enemies (G2): GDD section 5 "Enemy roles and proposed combat baselines" ========
	// ---- Roadwarden (all three equipment variants share these) ----
	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenHp = 40.0f; // bake: COM-14.roadwarden_hp
	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenPatrolSpan = 300.0f;
	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenPatrolSpeed = 90.0f;
	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenAimSeconds = 1.0f;
	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenShotSpeed = 240.0f;
	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenRecoverySeconds = 1.0f;
	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	float RoadwardenCycleSeconds = 2.5f;
	UPROPERTY(EditAnywhere, Category = "Roadwarden")
	FVector2D RoadwardenTorso = FVector2D(40.0f, 80.0f);

	// ---- Floodstrider ----
	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderHp = 60.0f; // bake: COM-15.floodstrider_hp
	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderPatrolSpan = 300.0f;
	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderPatrolSpeed = 60.0f;
	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderAimSeconds = 1.1f;
	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderShotSpeed = 220.0f;
	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderRecoverySeconds = 1.0f;
	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderCycleSeconds = 3.0f;
	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	FVector2D FloodstriderTorso = FVector2D(40.0f, 80.0f);
	/** Stilt height (short or long); the underbody passage stays open under the body. */
	UPROPERTY(EditAnywhere, Category = "Floodstrider")
	float FloodstriderStiltHeight = 160.0f;

	// ---- Sky Courier ----
	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierHp = 40.0f; // bake: COM-16.courier_hp
	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierPatrolSpan = 400.0f;
	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierPatrolSpeed = 100.0f;
	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierAimSeconds = 1.1f;
	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierShotSpeed = 180.0f;
	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierRecoverySeconds = 1.0f;
	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	float CourierCycleSeconds = 2.3f;
	UPROPERTY(EditAnywhere, Category = "SkyCourier")
	FVector2D CourierBody = FVector2D(48.0f, 88.0f);
	/** At most this many single emissions in total, red and yellow together (stable slots 0 to 7). */
	UPROPERTY(EditAnywhere, Category = "SkyCourier", meta = (ClampMin = "1"))
	int32 CourierMaxEmissions = 8;

	// ---- Shared ----
	UPROPERTY(EditAnywhere, Category = "Enemy")
	float EnemyShotDamage = 1.0f;
	UPROPERTY(EditAnywhere, Category = "Enemy")
	float EnemyShotRadius = 14.0f;
	UPROPERTY(EditAnywhere, Category = "Enemy")
	float EnemyShotLifetimeSeconds = 10.0f;
	/** Muzzle height above the enemy centre. */
	UPROPERTY(EditAnywhere, Category = "Enemy")
	float EnemyMuzzleLift = 10.0f;
	/** Two red-shooting enemies to one yellow-shooting enemy across a level (red : yellow). */
	UPROPERTY(EditAnywhere, Category = "Enemy", meta = (ClampMin = "1"))
	int32 RedPerYellow = 2;
};
