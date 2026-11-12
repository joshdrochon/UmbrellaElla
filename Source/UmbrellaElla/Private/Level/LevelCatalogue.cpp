#include "Level/LevelCatalogue.h"
#include "Core/UmbrellaTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Math/RandomStream.h"

namespace
{
	const FFieldTuning& Tuning()
	{
		return GetDefault<UUmbrellaTuning>()->Field;
	}

	TArray<FChunkVariant> BuildAll()
	{
		using M = EChunkMechanic;
		// HAZ-25..36: mechanics per authored chunk (A and B share the set; arrangement differs).
		const TArray<TArray<M>> PerChunk = {
			{M::Column},				// CH01 drop and catch
			{M::Warden},				// CH02 rooftop line
			{M::Courier},				// CH03 yellow crossing
			{M::Stilt},					// CH04 underbridge
			{M::Mill},					// CH05 over and under
			{M::Mill},					// CH06 countercurrent mill
			{M::Shutter},				// CH07 shutter pocket
			{M::Bellows},				// CH08 bellows lane
			{M::BridgeTooth},			// CH09 eave transfer
			{M::Column},				// CH10 switchback
			{M::Warden, M::Mill},		// CH11 warden and mill
			{M::Stilt, M::Courier}		// CH12 stilt and courier
		};
		TArray<FChunkVariant> Out;
		for (int32 i = 0; i < PerChunk.Num(); ++i)
		{
			for (const TCHAR Letter : {TEXT('A'), TEXT('B')})
			{
				FChunkVariant V;
				V.Chunk = i + 1;
				V.Variant = Letter;
				V.Mechanics = PerChunk[i];
				Out.Add(V);
			}
		}
		return Out;
	}

	FRoute FromLabels(int64 Seed, const TArray<FString>& Labels)
	{
		FRoute R;
		R.Seed = Seed;
		for (const FString& L : Labels)
		{
			if (const FChunkVariant* V = LevelCatalogue::Find(FCString::Atoi(*L.Left(2)), L[2]))
			{
				R.Slots.Add(*V);
			}
		}
		return R;
	}
}

FString FRoute::Signature() const
{
	TArray<FString> Parts;
	for (const FChunkVariant& V : Slots)
	{
		Parts.Add(V.Label());
	}
	return FString::Join(Parts, TEXT(","));
}

namespace LevelCatalogue
{
	const TArray<FChunkVariant>& All()
	{
		static const TArray<FChunkVariant> Catalogue = BuildAll();
		return Catalogue;
	}

	const FChunkVariant* Find(int32 Chunk, TCHAR Variant)
	{
		return All().FindByPredicate([=](const FChunkVariant& V) { return V.Chunk == Chunk && V.Variant == Variant; });
	}

	TArray<int32> SlotOptions(int32 SlotIndex)
	{
		switch (SlotIndex)
		{
		case 0: return {1};
		case 1: return {2};
		case 2: return {3};
		case 3: return {4};
		case 4: return {5, 6};
		case 5: return {7, 8};
		case 6: return {9, 10};
		case 7: return {5, 6, 7, 8};	// a not-yet-used one, filtered when drawing
		case 8: return {11, 12};
		default: return {};
		}
	}

	int32 NewMechanicCount(const FChunkVariant& V, const TSet<EChunkMechanic>& Introduced)
	{
		int32 Count = 0;
		for (const EChunkMechanic M : V.Mechanics)
		{
			Count += Introduced.Contains(M) ? 0 : 1;
		}
		return Count;
	}

	TArray<FString> ValidateRoute(const FRoute& Route)
	{
		TArray<FString> Problems;
		if (!IsFeatureEnabled(EFeatureId::FLOW_47))
		{
			return Problems;
		}
		if (Route.Slots.Num() != Tuning().RouteSlotCount)
		{
			Problems.Add(FString::Printf(TEXT("slot count %d, expected %d"), Route.Slots.Num(), Tuning().RouteSlotCount));
			return Problems;
		}
		TSet<EChunkMechanic> Introduced;
		TSet<int32> UsedChunks;
		for (int32 i = 0; i < Route.Slots.Num(); ++i)
		{
			const FChunkVariant& V = Route.Slots[i];
			if (!SlotOptions(i).Contains(V.Chunk))
			{
				Problems.Add(FString::Printf(TEXT("slot %d: %s not allowed by the nine-slot grammar"), i + 1, *V.Label()));
			}
			if (!V.bInterfaceN || !V.bReturnFlow || !V.bBypass)
			{
				Problems.Add(FString::Printf(TEXT("slot %d: %s breaks interface N / return flow / bypass"), i + 1, *V.Label()));
			}
			if (NewMechanicCount(V, Introduced) > 1)
			{
				Problems.Add(FString::Printf(TEXT("slot %d: %s introduces more than one new mechanic"), i + 1, *V.Label()));
			}
			if (UsedChunks.Contains(V.Chunk))
			{
				Problems.Add(FString::Printf(TEXT("slot %d: chunk %d repeats"), i + 1, V.Chunk));
			}
			UsedChunks.Add(V.Chunk);
			Introduced.Append(V.Mechanics);
		}
		return Problems;
	}

	FRoute BuildCandidate(int64 Seed, int32 Attempt)
	{
		// Separate layout stream: cosmetic and story streams are never drawn from here (HAZ-40).
		FRandomStream Layout(static_cast<int32>((Seed * 2654435761LL + Attempt * 40503LL) & 0x7fffffff));
		FRoute R;
		R.Seed = Seed;
		TSet<int32> Used;
		for (int32 Slot = 0; Slot < Tuning().RouteSlotCount; ++Slot)
		{
			TArray<int32> Options = SlotOptions(Slot);
			Options.RemoveAll([&](int32 C) { return Used.Contains(C); });
			if (Options.IsEmpty())
			{
				break;
			}
			const int32 Chunk = Options[Layout.RandRange(0, Options.Num() - 1)];
			const TCHAR Variant = Layout.RandRange(0, 1) == 0 ? TEXT('A') : TEXT('B');
			Used.Add(Chunk);
			if (const FChunkVariant* V = Find(Chunk, Variant))
			{
				R.Slots.Add(*V);
			}
		}
		R.Attempts = Attempt + 1;
		return R;
	}

	FRoute FallbackRoute()
	{
		return FromLabels(1001, {TEXT("01A"), TEXT("02A"), TEXT("03A"), TEXT("04A"), TEXT("05A"), TEXT("07A"), TEXT("09A"), TEXT("08A"), TEXT("11A")});
	}

	FRoute Generate(int64 Seed)
	{
		return GenerateAvoiding(Seed, FString());
	}

	FRoute GenerateAvoiding(int64 Seed, const FString& PreviousSignature)
	{
		const int32 Max = Tuning().MaxCandidateAttempts;
		for (int32 Attempt = 0; Attempt < Max; ++Attempt)
		{
			FRoute Candidate = BuildCandidate(Seed, Attempt);
			if (ValidateRoute(Candidate).IsEmpty() && (PreviousSignature.IsEmpty() || Candidate.Signature() != PreviousSignature))
			{
				return Candidate;
			}
		}
		FRoute Fallback = FallbackRoute();
		Fallback.Seed = Seed;
		Fallback.bFromFallback = true;
		Fallback.Attempts = Max;
		return Fallback;
	}

	float SlotStartX(int32 SlotIndex)
	{
		const float RefugeLength = Tuning().RefugeLengthFraction * Tuning().ChunkLength;
		return SlotIndex * Tuning().ChunkLength + (SlotIndex / 3) * RefugeLength;
	}

	float RefugeStartX(int32 Checkpoint)
	{
		return SlotStartX(3 * Checkpoint) - Tuning().RefugeLengthFraction * Tuning().ChunkLength;
	}

	float RouteLength()
	{
		return SlotStartX(Tuning().RouteSlotCount);
	}

	bool FootprintOnSupport(float Centre, float HalfWidth, float SupportMin, float SupportMax)
	{
		return Centre - HalfWidth >= SupportMin && Centre + HalfWidth <= SupportMax;
	}

	float ClampPatrolCentre(float Centre, float HalfWidth, float SupportMin, float SupportMax)
	{
		if (SupportMax - SupportMin < 2.0f * HalfWidth)
		{
			return 0.5f * (SupportMin + SupportMax);
		}
		return FMath::Clamp(Centre, SupportMin + HalfWidth, SupportMax - HalfWidth);
	}
}

namespace CameraRules
{
	float ScrollCentreX(float EllaX, int32 TravelDirection, float ViewWidth, float RouteMinX, float RouteMaxX)
	{
		const float Dir = static_cast<float>(FMath::Sign(TravelDirection));
		const float Target = EllaX + Dir * Tuning().CameraLeadFraction * ViewWidth;
		const float Half = 0.5f * ViewWidth;
		if (RouteMaxX - RouteMinX <= ViewWidth)
		{
			return 0.5f * (RouteMinX + RouteMaxX);
		}
		return FMath::Clamp(Target, RouteMinX + Half, RouteMaxX - Half);
	}

	float RevealLeadSeconds(float DistanceInView, float ClosingSpeed)
	{
		return ClosingSpeed > KINDA_SMALL_NUMBER ? DistanceInView / ClosingSpeed : TNumericLimits<float>::Max();
	}
}
