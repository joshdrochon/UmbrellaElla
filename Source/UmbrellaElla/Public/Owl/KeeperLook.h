#pragma once

#include "CoreMinimal.h"

/** Placeholder look of the Keeper, made from engine primitives until the art lane swaps it (colours, sizes in cm). */
namespace KeeperLook
{
	/** Engine cube mesh edge. */
	static constexpr float CubeEdge = 100.0f;
	/** Visible depth of every placeholder block. */
	static constexpr float VisualDepth = 30.0f;
	/** Collision depth (Y) of every part box. */
	static constexpr float PartDepth = 20.0f;
	/** Rise during the living departure. */
	static constexpr float DepartureRise = 600.0f;

	static constexpr FLinearColor Body = FLinearColor(0.55f, 0.5f, 0.35f);
	static constexpr FLinearColor Broken = FLinearColor(0.15f, 0.15f, 0.15f);
	static constexpr FLinearColor ClockClosed = FLinearColor(0.35f, 0.3f, 0.2f);
	static constexpr FLinearColor ClockOpen = FLinearColor(1.0f, 0.85f, 0.2f);
	static constexpr FLinearColor Eye = FLinearColor(0.9f, 0.1f, 0.9f);
	static constexpr FLinearColor Head = FLinearColor(0.9f, 0.3f, 0.1f);
	static constexpr FLinearColor SafeHead = FLinearColor(0.4f, 0.6f, 0.9f);
	static constexpr FLinearColor Talon = FLinearColor(0.9f, 0.9f, 0.9f);
	static constexpr FLinearColor Gust = FLinearColor(0.7f, 0.85f, 1.0f);
	static constexpr FLinearColor Telegraph = FLinearColor(1.0f, 0.2f, 0.2f);
}
