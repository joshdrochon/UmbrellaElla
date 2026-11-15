#pragma once

#include "CoreMinimal.h"

class UTexture2D;

/**
 * The Keeper's warning marks painted in code (Josh, Nov 14: the flat red line and the hard neon ring read below the
 * game's art). Etched-ink style: shot-red pigment with grain, feathered edges and a faint glow, never a uniform fill.
 * Built once per run as transient textures (kept rooted in the transient package); no asset import, so the art
 * lane's approved files are untouched.
 */
namespace PaintedWarningArt
{
	/** Streak texture size: length along U, width along V. */
	static constexpr int32 StreakW = 256;
	static constexpr int32 StreakH = 64;
	/** Ring sheet: Frames square cells of CellSize in one row (the VFX sheet layout). */
	static constexpr int32 CellSize = 128;
	static constexpr int32 Frames = 8;
	/** Alpha at the streak's tail (U = 0) and head (U = 1), and how the fade bends between them. */
	static constexpr float TailAlpha = 0.18f;
	static constexpr float HeadAlpha = 0.95f;
	static constexpr float FadeBend = 1.4f;
	/** Streak taper: width share at the tail, its curve, and the rounded head's share of the length. */
	static constexpr float TailWidth = 0.35f;
	static constexpr float TaperBend = 0.7f;
	static constexpr float HeadRound = 0.08f;
	/** Feathered core width and glow width (shares of the taper width), glow strength, smallest widths. */
	static constexpr float CoreWidth = 0.3f;
	static constexpr float GlowWidth = 0.75f;
	static constexpr float GlowStrength = 0.32f;
	static constexpr float MinCoreWidth = 0.02f;
	static constexpr float MinGlowWidth = 0.05f;
	/** Gaussian sharpness of every soft profile. */
	static constexpr float Sharpness = 2.0f;
	/** Dry-brush grain: base opacity at the tail and the head, grain amount at the tail and head, grain scale. */
	static constexpr float DryTail = 0.55f;
	static constexpr float DryHead = 0.95f;
	static constexpr float GrainTail = 0.9f;
	static constexpr float GrainHead = 0.45f;
	static constexpr float GrainU = 40.0f;
	static constexpr float GrainV = 12.0f;
	/** Lighter core band across the streak (share of the width). */
	static constexpr float CoreBand = 0.12f;
	/** Ring: radius and pulse, band and halo widths, halo strength, arcs, gap contrast, turn per loop. */
	static constexpr float RingRadius = 0.62f;
	static constexpr float RingPulse = 0.06f;
	static constexpr float RingBand = 0.07f;
	static constexpr float RingHaloWidth = 0.22f;
	static constexpr float RingHalo = 0.22f;
	static constexpr float RingHaloFloor = 0.4f;
	static constexpr float RingArcs = 3.0f;
	static constexpr float RingArcContrast = 1.6f;
	static constexpr float RingTurnShare = 1.0f / 3.0f;
	static constexpr float RingDryBase = 0.75f;
	static constexpr float RingDryAmount = 0.5f;
	static constexpr float RingGrain = 20.0f;
	static constexpr float RingBreathBase = 0.75f;
	static constexpr float RingBreath = 0.25f;
	static constexpr float RingOpacity = 0.7f;
	static constexpr float RingCoreShare = 0.5f;
	/** Shot red #ff3658 and its lighter core. */
	static constexpr uint8 RedR = 0xFF, RedG = 0x36, RedB = 0x58;
	static constexpr uint8 CoreR = 0xFF, CoreG = 0xB4, CoreB = 0xA8;
	/** Hash noise lattice constants (integer hash) and its 16-bit output range. */
	static constexpr uint32 HashX = 374761393u;
	static constexpr uint32 HashY = 668265263u;
	static constexpr uint32 HashMix = 1274126177u;
	static constexpr uint32 HashShiftA = 13u;
	static constexpr uint32 HashShiftB = 16u;
	static constexpr uint32 HashMask = 0xFFFFu;
	static constexpr float HashRange = 65535.0f;
	static constexpr float ByteMax = 255.0f;
	static const TCHAR* const StreakName = TEXT("T_KeeperWarnStreak_Painted");
	static const TCHAR* const RingName = TEXT("T_KeeperWarnRing_Painted");

	/** The streak alpha at (U, V) in 0..1 (tail at U 0, head at U 1, centre line at V 0.5). Pure. */
	UMBRELLAELLA_API float StreakAlpha(float U, float V);
	/** The ring alpha at (X, Y) in -1..1 of a cell for Frame (broken arcs that pulse and turn). Pure. */
	UMBRELLAELLA_API float RingAlpha(float X, float Y, int32 Frame);

	/** The streak texture (created on first use, kept for the run). */
	UMBRELLAELLA_API UTexture2D* Streak();
	/** The 8-frame ring sheet (created on first use, kept for the run). */
	UMBRELLAELLA_API UTexture2D* RingSheet();
}
