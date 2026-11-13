#include "Level/LevelCatalogue.h"
#include "Level/LevelGrammar.h"
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
		using ECatMech = EChunkMechanic;
		// mechanics per authored chunk (A and B share the set; arrangement differs).
		const TArray<TArray<ECatMech>> PerChunk = {
			{ECatMech::Column},				// CH01 drop and catch
			{ECatMech::Warden},				// CH02 rooftop line
			{ECatMech::Courier},				// CH03 yellow crossing
			{ECatMech::Stilt},					// CH04 underbridge
			{ECatMech::Mill},					// CH05 over and under
			{ECatMech::Mill},					// CH06 countercurrent mill
			{ECatMech::Shutter},				// CH07 shutter pocket
			{ECatMech::Bellows},				// CH08 bellows lane
			{ECatMech::BridgeTooth},			// CH09 eave transfer
			{ECatMech::Column},				// CH10 switchback
			{ECatMech::Warden, ECatMech::Mill},		// CH11 warden and mill
			{ECatMech::Stilt, ECatMech::Courier}		// CH12 stilt and courier
		};
		TArray<FChunkVariant> Out;
		for (int32 I = 0; I < PerChunk.Num(); ++I)
		{
			for (const TCHAR Letter : {TEXT('A'), TEXT('B')})
			{
				FChunkVariant V;
				V.Chunk = I + 1;
				V.Variant = Letter;
				V.Mechanics = PerChunk[I];
				Out.Add(V);
			}
		}
		return Out;
	}

	/** Route from a fixture text: labels like "01A" separated by "," or ";". */
	FRoute FromLabels(int64 Seed, const FString& Text)
	{
		TArray<FString> Labels;
		Text.Replace(TEXT(";"), TEXT(",")).ParseIntoArray(Labels, TEXT(","));
		FRoute R;
		R.Seed = Seed;
		for (const FString& L : Labels)
		{
			const FString Label = L.TrimStartAndEnd();
			const int32 LabelDigits = Label.Len() - 1;
			if (LabelDigits < 1)
			{
				continue;
			}
			if (const FChunkVariant* V = LevelCatalogue::Find(FCString::Atoi(*Label.Left(LabelDigits)), Label[LabelDigits]))
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
		TArray<int32> Out;
		if (SlotIndex >= 0 && SlotIndex < UE_ARRAY_COUNT(LevelGrammar::SlotChunks))
		{
			for (const int32 Chunk : LevelGrammar::SlotChunks[SlotIndex])
			{
				if (Chunk != 0)
				{
					Out.Add(Chunk);
				}
			}
		}
		return Out;
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
		for (int32 I = 0; I < Route.Slots.Num(); ++I)
		{
			const FChunkVariant& V = Route.Slots[I];
			if (!SlotOptions(I).Contains(V.Chunk))
			{
				Problems.Add(FString::Printf(TEXT("slot %d: %s not allowed by the nine-slot grammar"), I + 1, *V.Label()));
			}
			if (!V.bInterfaceN || !V.bReturnFlow || !V.bBypass)
			{
				Problems.Add(FString::Printf(TEXT("slot %d: %s breaks interface N / return flow / bypass"), I + 1, *V.Label()));
			}
			if (NewMechanicCount(V, Introduced) > 1)
			{
				Problems.Add(FString::Printf(TEXT("slot %d: %s introduces more than one new mechanic"), I + 1, *V.Label()));
			}
			if (UsedChunks.Contains(V.Chunk))
			{
				Problems.Add(FString::Printf(TEXT("slot %d: chunk %d repeats"), I + 1, V.Chunk));
			}
			UsedChunks.Add(V.Chunk);
			Introduced.Append(V.Mechanics);
		}
		return Problems;
	}

	FRoute BuildCandidate(int64 Seed, int32 Attempt)
	{
		// Separate layout stream: cosmetic and story streams are never drawn from here.
		FRandomStream Layout(static_cast<int32>((Seed * LevelGrammar::SeedMultiplier + Attempt * LevelGrammar::AttemptStride) & LevelGrammar::SeedMask));
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
		// The named fallback is the seed 1001 layout (the first fixture).
		return FromLabels(Tuning().FallbackSeed, LevelGrammar::FixtureRoutes[0]);
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
		return SlotIndex * Tuning().ChunkLength + (SlotIndex / Tuning().SlotsPerCheckpoint) * RefugeLength;
	}

	float RefugeStartX(int32 Checkpoint)
	{
		return SlotStartX(Tuning().SlotsPerCheckpoint * Checkpoint) - Tuning().RefugeLengthFraction * Tuning().ChunkLength;
	}

	float RouteLength()
	{
		return SlotStartX(Tuning().RouteSlotCount);
	}

	bool IsFootprintOnSupport(float Centre, float HalfWidth, float SupportMin, float SupportMax)
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
