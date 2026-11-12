#pragma once

#include "CoreMinimal.h"
#include "Engine/EngineTypes.h"

/** Collision channels; mirror of [/Script/Engine.CollisionProfile] in Config/DefaultEngine.ini (Core, TD-owned). */
namespace UmbrellaCollision
{
	static constexpr ECollisionChannel PlayerShot = ECC_GameTraceChannel1;
	static constexpr ECollisionChannel EnemyShot = ECC_GameTraceChannel2;
	static constexpr ECollisionChannel Hazard = ECC_GameTraceChannel3;
}
