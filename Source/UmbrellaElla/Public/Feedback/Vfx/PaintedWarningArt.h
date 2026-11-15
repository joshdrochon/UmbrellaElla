#pragma once

#include "CoreMinimal.h"

class UTexture2D;

/**
 * The Keeper's warning marks painted in code (Josh, Nov 14: the flat red line and the hard neon ring read below the
 * game's art). Etched-ink style: shot-red pigment with grain, feathered edges and a faint glow, never a uniform fill.
 * Built once per run as transient textures; no asset import, so the art lane's approved files are untouched.
 */
namespace PaintedWarningArt
{
	/** Streak texture size: length along U, width along V. */
	static constexpr int32 StreakW = 256;
	static constexpr int32 StreakH = 64;
	/** Ring sheet: Frames square cells of CellSize in one row (the VFX sheet layout). */
	static constexpr int32 CellSize = 128;
	static constexpr int32 Frames = 8;
	/** Alpha at the streak's tail (U = 0) and head (U = 1). */
	static constexpr float TailAlpha = 0.18f;
	static constexpr float HeadAlpha = 0.95f;
	/** Shot red #ff3658 and its lighter core. */
	static constexpr uint8 RedR = 0xFF, RedG = 0x36, RedB = 0x58;
	static constexpr uint8 CoreR = 0xFF, CoreG = 0xB4, CoreB = 0xA8;

	/** The streak alpha at (U, V) in 0..1 (tail at U 0, head at U 1, centre line at V 0.5). Pure. */
	UMBRELLAELLA_API float StreakAlpha(float U, float V);
	/** The ring alpha at (X, Y) in -1..1 of a cell for Frame (broken arcs that pulse and turn). Pure. */
	UMBRELLAELLA_API float RingAlpha(float X, float Y, int32 Frame);

	/** The streak texture (created on first use, kept for the run). */
	UMBRELLAELLA_API UTexture2D* Streak();
	/** The 8-frame ring sheet (created on first use, kept for the run). */
	UMBRELLAELLA_API UTexture2D* RingSheet();
}
