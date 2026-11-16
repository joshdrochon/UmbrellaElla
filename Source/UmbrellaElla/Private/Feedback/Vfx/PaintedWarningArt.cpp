#include "Feedback/Vfx/PaintedWarningArt.h"
#include "Engine/Texture2D.h"
#include "TextureResource.h"
#include "UObject/Package.h"

namespace
{
	/** Grain: hash noise in 0..1 on an integer lattice, smoothed (the etched paper tooth). */
	float Hash(int32 X, int32 Y)
	{
		uint32 H = static_cast<uint32>(X) * PaintedWarningArt::HashX + static_cast<uint32>(Y) * PaintedWarningArt::HashY;
		H = (H ^ (H >> PaintedWarningArt::HashShiftA)) * PaintedWarningArt::HashMix;
		return static_cast<float>((H ^ (H >> PaintedWarningArt::HashShiftB)) & PaintedWarningArt::HashMask) / PaintedWarningArt::HashRange;
	}

	float Grain(float X, float Y)
	{
		const int32 IX = FMath::FloorToInt32(X);
		const int32 IY = FMath::FloorToInt32(Y);
		const float FX = X - IX;
		const float FY = Y - IY;
		const float A = FMath::Lerp(Hash(IX, IY), Hash(IX + 1, IY), FX);
		const float B = FMath::Lerp(Hash(IX, IY + 1), Hash(IX + 1, IY + 1), FX);
		return FMath::Lerp(A, B, FY);
	}

	/** A soft gaussian profile: 1 at the centre, falling off over Width. */
	float Soft(float Distance, float Width)
	{
		return FMath::Exp(-FMath::Square(Distance / Width) * PaintedWarningArt::Sharpness);
	}

	/** Pigment for an alpha: the core runs lighter, the feathered edge stays shot red. */
	FColor Pigment(float Alpha, float Core)
	{
		namespace P = PaintedWarningArt;
		const float C = FMath::Clamp(Core, 0.0f, 1.0f);
		return FColor(
			static_cast<uint8>(FMath::Lerp(static_cast<float>(P::RedR), static_cast<float>(P::CoreR), C)),
			static_cast<uint8>(FMath::Lerp(static_cast<float>(P::RedG), static_cast<float>(P::CoreG), C)),
			static_cast<uint8>(FMath::Lerp(static_cast<float>(P::RedB), static_cast<float>(P::CoreB), C)),
			static_cast<uint8>(FMath::Clamp(Alpha, 0.0f, 1.0f) * P::ByteMax));
	}

	UTexture2D* MakeTexture(int32 W, int32 H, const TArray<FColor>& Pixels, const TCHAR* Name)
	{
		UTexture2D* Texture = UTexture2D::CreateTransient(W, H, PF_B8G8R8A8, FName(Name));
		if (!Texture || !Texture->GetPlatformData() || Texture->GetPlatformData()->Mips.Num() == 0)
		{
			return nullptr;
		}
		FTexture2DMipMap& Mip = Texture->GetPlatformData()->Mips[0];
		void* Data = Mip.BulkData.Lock(LOCK_READ_WRITE);
		FMemory::Memcpy(Data, Pixels.GetData(), Pixels.Num() * sizeof(FColor));
		Mip.BulkData.Unlock();
		Texture->SRGB = true;
		Texture->Filter = TF_Bilinear;
		Texture->AddressX = TA_Clamp;
		Texture->AddressY = TA_Clamp;
		Texture->UpdateResource();
		Texture->AddToRoot();
		return Texture;
	}
}

float PaintedWarningArt::StreakAlpha(float U, float V)
{
	const float Along = FMath::Clamp(U, 0.0f, 1.0f);
	// Taper: the width narrows toward the tail; the head end is rounded off over its last HeadRound.
	const float Width = FMath::Lerp(TailWidth, 1.0f, FMath::Pow(Along, TaperBend)) * FMath::Clamp((1.0f - Along) / HeadRound, 0.0f, 1.0f);
	const float Across = FMath::Abs(V - 0.5f) * 2.0f;
	// Feathered core plus a faint wide glow.
	const float Core = Soft(Across, FMath::Max(CoreWidth * Width, MinCoreWidth));
	const float Glow = GlowStrength * Soft(Across, FMath::Max(GlowWidth * Width, MinGlowWidth));
	// Etched grain: dry-brush breaks along the stroke, stronger toward the tail.
	const float Dry = FMath::Lerp(DryTail, DryHead, Along) + (Grain(U * GrainU, V * GrainV) - 0.5f) * FMath::Lerp(GrainTail, GrainHead, Along);
	const float Fade = FMath::Lerp(TailAlpha, HeadAlpha, FMath::Pow(Along, FadeBend));
	return FMath::Clamp((Core * FMath::Clamp(Dry, 0.0f, 1.0f) + Glow) * Fade, 0.0f, 1.0f);
}

float PaintedWarningArt::RingAlpha(float X, float Y, int32 Frame)
{
	const float Phase = static_cast<float>(Frame % Frames) / static_cast<float>(Frames);
	const float R = FMath::Sqrt(X * X + Y * Y);
	// The pulse: the ring breathes out and back over the loop.
	const float Radius = RingRadius + RingPulse * FMath::Sin(2.0f * PI * Phase);
	const float Band = Soft(R - Radius, RingBand);
	const float Halo = RingHalo * Soft(R - Radius, RingHaloWidth);
	// Broken: painted arcs with soft gaps, turning slowly.
	const float Angle = FMath::Atan2(Y, X) / (2.0f * PI) + Phase * RingTurnShare;
	const float Arc = FMath::Clamp(0.5f + RingArcContrast * FMath::Sin(2.0f * PI * RingArcs * Angle), 0.0f, 1.0f);
	const float Dry = RingDryBase + (Grain((X + 1.0f) * RingGrain, (Y + 1.0f) * RingGrain) - 0.5f) * RingDryAmount;
	const float Breath = RingBreathBase + RingBreath * FMath::Cos(2.0f * PI * Phase);
	return FMath::Clamp((Band * Arc * Dry + Halo * (RingHaloFloor + (1.0f - RingHaloFloor) * Arc)) * Breath * RingOpacity, 0.0f, 1.0f);
}

UTexture2D* PaintedWarningArt::Streak()
{
	if (UTexture2D* Existing = FindObject<UTexture2D>(GetTransientPackage(), StreakName))
	{
		return Existing;
	}
	TArray<FColor> Pixels;
	Pixels.SetNumUninitialized(StreakW * StreakH);
	for (int32 Y = 0; Y < StreakH; ++Y)
	{
		for (int32 X = 0; X < StreakW; ++X)
		{
			const float U = (X + 0.5f) / StreakW;
			const float V = (Y + 0.5f) / StreakH;
			const float Core = Soft(FMath::Abs(V - 0.5f) * 2.0f, CoreBand) * U;
			Pixels[Y * StreakW + X] = Pigment(StreakAlpha(U, V), Core);
		}
	}
	return MakeTexture(StreakW, StreakH, Pixels, StreakName);
}

UTexture2D* PaintedWarningArt::RingSheet()
{
	if (UTexture2D* Existing = FindObject<UTexture2D>(GetTransientPackage(), RingName))
	{
		return Existing;
	}
	const int32 W = CellSize * Frames;
	TArray<FColor> Pixels;
	Pixels.SetNumUninitialized(W * CellSize);
	for (int32 Y = 0; Y < CellSize; ++Y)
	{
		for (int32 X = 0; X < W; ++X)
		{
			const float CX = ((X % CellSize) + 0.5f) / CellSize * 2.0f - 1.0f;
			const float CY = (Y + 0.5f) / CellSize * 2.0f - 1.0f;
			const float Alpha = RingAlpha(CX, CY, X / CellSize);
			Pixels[Y * W + X] = Pigment(Alpha, Alpha * RingCoreShare);
		}
	}
	return MakeTexture(W, CellSize, Pixels, RingName);
}
