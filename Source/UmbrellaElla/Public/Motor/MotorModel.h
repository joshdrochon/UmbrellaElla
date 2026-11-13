#pragma once

#include "CoreMinimal.h"
#include "Umbrella/UmbrellaAction.h"

struct FMotorTuning;

/** What a hop/dash press asks for. Hop is contextual: overhead = hop, falling = dash by input direction. */
enum class EMotorRequest : uint8
{
	None,
	Hop,
	DashBack,
	DashForward
};

enum class EMotorBurst : uint8
{
	None,
	Hop,
	Dash
};

/** Everything the motor model remembers between frames. Plain data; the component owns one. */
struct UMBRELLAELLA_API FMotorModelState
{
	/** Total velocity of the last step (X right, Z up), units/s. */
	FVector2D Velocity = FVector2D::ZeroVector;
	FVector2D Wind = FVector2D::ZeroVector;
	FVector2D BurstVelocity = FVector2D::ZeroVector;
	EMotorBurst Burst = EMotorBurst::None;
	float BurstTimeLeft = 0.0f;
	float HopCooldownLeft = 0.0f;
	float DashCooldownLeft = 0.0f;
	float ProtectionLeft = 0.0f;
	EMotorRequest Buffered = EMotorRequest::None;
	float BufferLeft = 0.0f;
	bool bRiding = false;
};

/** What the motor reads each frame. */
struct UMBRELLAELLA_API FMotorInput
{
	EUmbrellaAction Action = EUmbrellaAction::Rise;
	/** Vertical trim, -1 (down) to 1 (up). */
	float TrimAxis = 0.0f;
	/** Horizontal input, -1 (left) to 1 (right). Picks a direction only; it never steers. */
	float MoveAxis = 0.0f;
	bool bRideHeld = false;
	bool bInCurrent = false;
	/** Summed velocity of the overlapped voluntary currents. */
	FVector2D CurrentVelocity = FVector2D::ZeroVector;
	/** Summed velocity of hostile forced pushes (GUST_Band). Applies at once, whatever the action or Ride. */
	FVector2D ForcedVelocity = FVector2D::ZeroVector;
	float LiftMultiplier = 1.0f;
	/** Summed local vertical field term of the overlapped currents (Gain * (CentreZ - RootZ) + Compensation). Applies while riding. */
	float LocalVerticalVelocity = 0.0f;
};

/** Plain rule functions for the Player Motor. No engine objects, so tests call them at any delta. */
namespace MotorModel
{
	/** Tuning percents divide by this. */
	static constexpr float PercentScale = 100.0f;

	/** Number of values in a local field: gain, centre z, compensation. */
	static constexpr int32 LocalFieldValueCount = 3;

	/** Queue a hop/dash press (held for ToggleBufferSeconds if it cannot start yet). */
	UMBRELLAELLA_API void Request(FMotorModelState& State, EMotorRequest Request, const FMotorTuning& Tuning);

	/** Advance one frame; returns the displacement (X, Z) to apply this frame. */
	UMBRELLAELLA_API FVector2D Step(FMotorModelState& State, const FMotorInput& Input, const FMotorTuning& Tuning, float DeltaSeconds);

	/** Base vertical velocity of an action with trim and lift applied (no wind, no burst). */
	UMBRELLAELLA_API float BaseVerticalSpeed(const FMotorInput& Input, const FMotorTuning& Tuning);

	/** True for hostile push sources that bypass the ride path (GUST_Band). */
	UMBRELLAELLA_API bool IsForcedSource(FName SourceId);

	/** True while a hop's protection window is open. Dash never protects. */
	UMBRELLAELLA_API bool IsProtected(const FMotorModelState& State);

	/** Current direction from an event Detail: Right, Left, Up, Down, or "x,z". Zero when unreadable. */
	UMBRELLAELLA_API FVector2D ParseCurrentDirection(FName Detail);

	/** Local vertical field after '@' in a current's Detail: "gain,centreZ,compensation". False when absent. */
	UMBRELLAELLA_API bool HasLocalField(FName Detail, float& OutGain, float& OutCentreZ, float& OutCompensation);

	/** Vertical term of one local field for a root at RootZ. */
	UMBRELLAELLA_API float LocalVerticalTerm(float Gain, float CentreZ, float Compensation, float RootZ);
}
