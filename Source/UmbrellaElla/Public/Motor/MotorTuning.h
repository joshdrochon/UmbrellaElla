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
	float RiseSpeed = 240.0f; // bake: MOVE-21.rise_speed

	/** Shoot-fall and absorb-fall speed, units/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float FallSpeed = 660.0f; // bake: MOVE-21.fall_speed

	/** Fast free fall speed (both held), units/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float FreeFallSpeed = 1220.0f; // bake: MOVE-21.free_fall_speed

	/** Cap on current-driven horizontal (and vertical) travel, units/s. Direct steering is OFF. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float HorizontalMaxSpeed = 580.0f; // bake: MOVE-21.horizontal_max_speed

	/** Vertical trim: percent of the state's speed added or removed by full stick/key. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0", ClampMax = "100"))
	float VerticalTrimPct = 20.0f; // bake: MOVE-21.vertical_trim_pct

	/** Overhead hop distance, units. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float HopDistance = 80.0f; // bake: MOVE-21.hop_distance

	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0.01"))
	float HopDurationSeconds = 0.22f; // bake: MOVE-21.hop_duration_s

	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float HopCooldownSeconds = 0.7f; // bake: MOVE-21.hop_cooldown_s

	/** Protection granted by a hop. Dash grants none (dash invulnerability OFF). */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float HopProtectionSeconds = 0.2f; // bake: MOVE-21.hop_protection_s

	/** Falling dash distance, units. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float DashDistance = 170.0f; // bake: MOVE-21.dash_distance

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

	/** Largest wind velocity the Motor carries, units/s (GDD wind 360 x WindScale, D-new-move-speeds). */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float WindMaxSpeed = 720.0f;

	/** Every wind current, gust push and local wind field reaches Ella at this multiple of its GDD speed (D-new-move-speeds:
	 *  the felt speeds from the old double move, kept by Josh 14 Nov, now from one knob). */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float WindScale = 2.0f;

	/** Wind momentum decay while overhead and not riding, 1/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float WindOpenDecay = 1.5f; // bake: MOVE-22.wind_open_decay

	/** Wind momentum decay while falling, 1/s. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float WindFallingDecay = 12.0f; // bake: MOVE-22.wind_falling_decay

	/** A hop/dash press made this long before it is allowed still fires (pipeline/feel/feel.json forgiveness.toggle_buffer_s). */
	UPROPERTY(Config, EditAnywhere, Category = "Motor", meta = (ClampMin = "0"))
	float ToggleBufferSeconds = 0.1f;

	/** HeroSize: Ella's size multiplier; 1 is the reference the muzzle fixture (+44/+6) is measured at. Clamped to HeroSizeMin..HeroSizeMax. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor|HeroSize", meta = (ClampMin = "0.75", ClampMax = "1.3"))
	float HeroSize = 1.0f; // bake: HAZ-10.herosize

	/** Lowest supported HeroSize. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor|HeroSize", meta = (ClampMin = "0"))
	float HeroSizeMin = 0.75f; // bake: HAZ-14.herosize.2

	/** Highest supported HeroSize. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor|HeroSize", meta = (ClampMin = "0"))
	float HeroSizeMax = 1.3f; // bake: HAZ-13.herosize

	/** Ella's actor scale at HeroSize 1; the applied scale is this times HeroSize (GDD). */
	UPROPERTY(Config, EditAnywhere, Category = "Motor|HeroSize", meta = (ClampMin = "0.01"))
	float ActorScaleAtReference = 0.5f; // bake: HAZ-10.actor_scale

	/** Hurtbox (capsule) scale on top of the actor scale; 1 is the full hitbox. Clamped to HitboxScaleMin..HitboxScaleMax. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor|HeroSize", meta = (ClampMin = "0.75", ClampMax = "1"))
	float HitboxScale = 1.0f;

	/** Lowest supported hitbox scale. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor|HeroSize", meta = (ClampMin = "0"))
	float HitboxScaleMin = 0.75f; // bake: HAZ-14.hitbox

	/** Highest supported hitbox scale. */
	UPROPERTY(Config, EditAnywhere, Category = "Motor|HeroSize", meta = (ClampMin = "0"))
	float HitboxScaleMax = 1.0f; // bake: HAZ-14.across
};
