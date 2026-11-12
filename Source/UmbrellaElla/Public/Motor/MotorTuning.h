#pragma once

#include "CoreMinimal.h"
#include "MotorTuning.generated.h"

/** Every number of the Motor module: default, units and clamps (lane a). Units: GDD world units = Unreal cm. End a shipped default with // bake: <feature ID>.<param>. */
USTRUCT()
struct UMBRELLAELLA_API FMotorTuning
{
	GENERATED_BODY()

	/** Overhead rise speed, units/s (neither Shoot nor Absorb held). */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float RiseSpeed = 120.0f; // bake: MOVE-21.rise_speed

	/** Shoot-fall and absorb-fall speed, units/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float FallSpeed = 330.0f; // bake: MOVE-21.fall_speed

	/** Fast free fall speed (both held), units/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float FreeFallSpeed = 610.0f; // bake: MOVE-21.free_fall_speed

	/** Cap on current-driven horizontal (and vertical) travel, units/s. Direct steering is OFF. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float HorizontalMaxSpeed = 290.0f; // bake: MOVE-21.horizontal_max_speed

	/** Vertical trim: percent of the state's speed added or removed by full stick/key. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0", ClampMax = "100"))
	float VerticalTrimPct = 20.0f; // bake: MOVE-21.vertical_trim_pct

	/** Overhead hop distance, units. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float HopDistance = 40.0f; // bake: MOVE-21.hop_distance

	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0.01"))
	float HopDurationSeconds = 0.22f; // bake: MOVE-21.hop_duration_s

	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float HopCooldownSeconds = 0.7f; // bake: MOVE-21.hop_cooldown_s

	/** Protection granted by a hop. Dash grants none (dash invulnerability OFF). */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float HopProtectionSeconds = 0.2f; // bake: MOVE-21.hop_protection_s

	/** Falling dash distance, units. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float DashDistance = 85.0f; // bake: MOVE-21.dash_distance

	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0.01"))
	float DashDurationSeconds = 0.16f; // bake: MOVE-21.dash_duration_s

	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float DashCooldownSeconds = 0.3f; // bake: MOVE-21.dash_cooldown_s

	/** Free-fall dash distance multiplier. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float FreeFallDashMultiplier = 0.5f; // bake: MOVE-21.free_fall_dash_multiplier

	/** Wind response: how fast riding Ella reaches the current's velocity, 1/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float WindAcceleration = 3.0f; // bake: MOVE-22.wind_acceleration

	/** Wind momentum decay while overhead and not riding, 1/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float WindOpenDecay = 1.5f; // bake: MOVE-22.wind_open_decay

	/** Wind momentum decay while falling, 1/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float WindFallingDecay = 12.0f; // bake: MOVE-22.wind_falling_decay

	/** A hop/dash press made this long before it is allowed still fires (pipeline/feel/feel.json forgiveness.toggle_buffer_s). */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float ToggleBufferSeconds = 0.1f;
};
