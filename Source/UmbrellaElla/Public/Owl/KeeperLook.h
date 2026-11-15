#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaDrawOrder.h"

/** Placeholder look of the Keeper, made from engine primitives until the art lane swaps it (colours, sizes in cm). */
namespace KeeperLook
{
	/** Engine cube mesh edge. */
	static constexpr float CubeEdge = 100.0f;
	/** Visible depth of every placeholder block. */
	static constexpr float VisualDepth = 30.0f;
	/** Collision depth (Y) of every part box. */
	static constexpr float PartDepth = 20.0f;
	/**
	 * Half depth (Y) of a part's collision box: from the Keeper's plane (KeeperY) past Ella's shot plane (ProjectileY)
	 * by PartDepth. Play is in X/Z and depth is draw order only (collision is fixed data, never the
	 * look); with PartDepth alone the boxes spanned Y -70..-30 and a Small Blast at Y 25 never touched them
	 * (ellashoot, 14 Nov: 58 hip-fire shots in a real-input Keeper run, 0 hits).
	 */
	static constexpr float PartShotHalfDepth = (UmbrellaDrawOrder::ProjectileY - UmbrellaDrawOrder::KeeperY) + PartDepth;
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
	/** Shot red, the same red as UmbrellaFrameConst::TelegraphRed (was 1,0.2,0.2: a salmon-pink block on screen). */
	static constexpr FLinearColor Telegraph = FLinearColor(1.0f, 0.037f, 0.095f);
	/** The warning marker is a thin line along its lane, this thick (cm): 0.15 of the 120 cm gust band. */
	static constexpr float TelegraphLineThickness = 18.0f;
	/** Height (cm) of the painted warning streak quad: its feathered core reads about as thick as the line, the glow wider. */
	static constexpr float TelegraphStreakWidth = 64.0f;
}
