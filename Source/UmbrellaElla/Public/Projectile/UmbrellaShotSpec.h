#pragma once

#include "CoreMinimal.h"
#include "UmbrellaShotSpec.generated.h"

/** Who fired it and what it does on contact (COM: red = damage, yellow = absorbable/heals). */
UENUM()
enum class EUmbrellaShotKind : uint8
{
	PlayerBlast,
	EnemyRed,
	EnemyYellow
};

/** What a spawner asks the Projectile Service for (lane c owns the service; lanes a and b call it). */
USTRUCT()
struct UMBRELLAELLA_API FUmbrellaShotSpec
{
	GENERATED_BODY()

	UPROPERTY()
	EUmbrellaShotKind Kind = EUmbrellaShotKind::PlayerBlast;

	UPROPERTY()
	FVector Origin = FVector::ZeroVector;

	/** World units per second, in X/Z. */
	UPROPERTY()
	FVector Velocity = FVector::ZeroVector;

	UPROPERTY()
	float Radius = 0.0f;

	UPROPERTY()
	float Damage = 0.0f;

	UPROPERTY()
	float LifetimeSeconds = 0.0f;

	UPROPERTY()
	FName SourceId;
};
