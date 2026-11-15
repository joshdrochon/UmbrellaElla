#include "Feedback/Vfx/PaintedWarningArt.h"
#include "Engine/Texture2D.h"
#include "TextureResource.h"

namespace
{
	/** Grain: hash noise in 0..1 on an integer lattice, smoothed (the etched paper tooth). */
	float Hash(int32 X, int32 Y)
	{
		uint32 H = static_cast<uint32>(X) * 374761393u + static_cast<uint32>(Y) * 668265263u;
		H = (H ^ (H >> 13)) * 1274126177u;
		return static_cast<float>((H ^ (H >> 16)) & 0xFFFF) / 65535.0f;
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

	/** Pigment for an alpha: the core runs lighter, the feathered edge stays shot red. */
	FColor Pigment(float Alpha, float Core)
	{
		const float C = FMath::Clamp(Core, 0.0f, 1.0f);
		return FColor(
			static_cast<uint8>(FMath::Lerp(static_cast<float>(PaintedWarningArt::RedR), static_cast<float>(PaintedWarningArt::CoreR), C)),
			static_cast<uint8>(FMath::Lerp(static_cast<float>(PaintedWarningArt::RedG), static_cast<float>(PaintedWarningArt::CoreG), C)),
			static_cast<uint8>(FMath::Lerp(static_cast<float>(PaintedWarningArt::RedB), static_cast<float>(PaintedWarningArt::CoreB), C)),
			static_cast<uint8>(FMath::Clamp(Alpha, 0.0f, 1.0f) * 255.0f));
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
	// Taper: the width narrows toward the tail; the head end is rounded off over its last 8%.
	const float Width = FMath::Lerp(0.35f, 1.0f, FMath::Pow(Along, 0.7f)) * FMath::Clamp((1.0f - Along) / 0.08f, 0.0f, 1.0f);
	const float Across = FMath::Abs(V - 0.5f) * 2.0f;
	// Feathered core (gaussian) plus a faint wide glow.
	const float Core = FMath::Exp(-FMath::Square(Across / FMath::Max(0.3f * Width, 0.02f)) * 2.0f);
	const float Glow = 0.32f * FMath::Exp(-FMath::Square(Across / FMath::Max(0.75f * Width, 0.05f)) * 2.0f);
	// Etched grain: dry-brush breaks along the stroke, stronger toward the tail.
	const float Dry = FMath::Lerp(0.55f, 0.95f, Along) + (Grain(U * 40.0f, V * 12.0f) - 0.5f) * FMath::Lerp(0.9f, 0.45f, Along);
	const float Fade = FMath::Lerp(TailAlpha, HeadAlpha, FMath::Pow(Along, 1.4f));
	return FMath::Clamp((Core * FMath::Clamp(Dry, 0.0f, 1.0f) + Glow) * Fade, 0.0f, 1.0f);
}

float PaintedWarningArt::RingAlpha(float X, float Y, int32 Frame)
{
	const float Phase = static_cast<float>(Frame % Frames) / static_cast<float>(Frames);
	const float R = FMath::Sqrt(X * X + Y * Y);
	// The pulse: the ring breathes out and back over the loop.
	const float Radius = 0.62f + 0.06f * FMath::Sin(2.0f * PI * Phase);
	const float Band = FMath::Exp(-FMath::Square((R - Radius) / 0.07f) * 2.0f);
	const float Halo = 0.22f * FMath::Exp(-FMath::Square((R - Radius) / 0.22f) * 2.0f);
	// Broken: three painted arcs with soft gaps, turning slowly.
	const float Angle = FMath::Atan2(Y, X) / (2.0f * PI) + Phase / 3.0f;
	const float Arc = FMath::Clamp(0.5f + 1.6f * FMath::Sin(2.0f * PI * 3.0f * Angle), 0.0f, 1.0f);
	const float Dry = 0.75f + (Grain((X + 1.0f) * 20.0f, (Y + 1.0f) * 20.0f) - 0.5f) * 0.5f;
	const float Breath = 0.75f + 0.25f * FMath::Cos(2.0f * PI * Phase);
	return FMath::Clamp((Band * Arc * Dry + Halo * (0.4f + 0.6f * Arc)) * Breath * 0.7f, 0.0f, 1.0f);
}

UTexture2D* PaintedWarningArt::Streak()
{
	static TWeakObjectPtr<UTexture2D> Cached;
	if (Cached.IsValid())
	{
		return Cached.Get();
	}
	TArray<FColor> Pixels;
	Pixels.SetNumUninitialized(StreakW * StreakH);
	for (int32 Y = 0; Y < StreakH; ++Y)
	{
		for (int32 X = 0; X < StreakW; ++X)
		{
			const float U = (X + 0.5f) / StreakW;
			const float V = (Y + 0.5f) / StreakH;
			const float Alpha = StreakAlpha(U, V);
			const float Core = FMath::Exp(-FMath::Square(FMath::Abs(V - 0.5f) * 2.0f / 0.12f)) * U;
			Pixels[Y * StreakW + X] = Pigment(Alpha, Core);
		}
	}
	Cached = MakeTexture(StreakW, StreakH, Pixels, TEXT("T_KeeperWarnStreak_Painted"));
	return Cached.Get();
}

UTexture2D* PaintedWarningArt::RingSheet()
{
	static TWeakObjectPtr<UTexture2D> Cached;
	if (Cached.IsValid())
	{
		return Cached.Get();
	}
	const int32 W = CellSize * Frames;
	TArray<FColor> Pixels;
	Pixels.SetNumUninitialized(W * CellSize);
	for (int32 Y = 0; Y < CellSize; ++Y)
	{
		for (int32 X = 0; X < W; ++X)
		{
			const int32 Frame = X / CellSize;
			const float CX = ((X % CellSize) + 0.5f) / CellSize * 2.0f - 1.0f;
			const float CY = (Y + 0.5f) / CellSize * 2.0f - 1.0f;
			const float Alpha = RingAlpha(CX, CY, Frame);
			Pixels[Y * W + X] = Pigment(Alpha, Alpha * 0.5f);
		}
	}
	Cached = MakeTexture(W, CellSize, Pixels, TEXT("T_KeeperWarnRing_Painted"));
	return Cached.Get();
}
