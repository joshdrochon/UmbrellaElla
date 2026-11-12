#pragma once

#include "CoreMinimal.h"

/** Every depth offset (Y; play is in X/Z) and sort priority, back to front (Core, TD-owned). No depth literal anywhere else. */
namespace UmbrellaDrawOrder
{
	static constexpr float BackgroundFarY = -400.0f;
	static constexpr float BackgroundNearY = -300.0f;
	static constexpr float ArenaY = -200.0f;
	static constexpr float HazardY = -100.0f;
	static constexpr float KeeperY = -50.0f;
	static constexpr float EllaY = 0.0f;
	static constexpr float ProjectileY = 25.0f;
	static constexpr float VfxY = 50.0f;
	static constexpr float ForegroundY = 100.0f;
}
