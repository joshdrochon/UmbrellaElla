#include "Level/LevelPlan.h"
#include "Arena/ArenaCameraTuning.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Level/LevelRules.h"
#include "Math/RandomStream.h"

namespace
{
	const FFieldTuning& LevelPlanField()
	{
		return GetDefault<UUmbrellaTuning>()->Field;
	}
	const FArenaCameraTuning& LevelPlanArena()
	{
		return GetDefault<UUmbrellaTuning>()->ArenaCamera;
	}


	FLevelPlacement MakePlacement(ELevelPlacementKind Kind, int32 Slot, float X, float Z, float W, float H)
	{
		FLevelPlacement P;
		P.Kind = Kind;
		P.Slot = Slot;
		P.Location = FVector(X, UmbrellaDrawOrder::HazardY, Z);
		P.Size = FVector(W, LevelPlanConst::DepthSize, H);
		return P;
	}
}

namespace LevelPlan
{
	TArray<FLevelPlacement> Build(const FRoute& Route)
	{
		TArray<FLevelPlacement> Out;
		if (!IsFeatureEnabled(EFeatureId::HAZ_37) || !IsFeatureEnabled(EFeatureId::FLOW_24))
		{
			return Out;
		}
		const float H = LevelPlanArena().ArenaHeight;
		const float Chunk = LevelPlanField().ChunkLength;
		const float FloorThick = LevelPlanConst::FloorThicknessFraction * H;
		// Separate seeded stream for enemy colours, so layout and colour never share draws.
		FRandomStream Colours(static_cast<int32>(Route.Seed & LevelPlanConst::SeedMask));

		for (int32 Slot = 0; Slot < Route.Slots.Num(); ++Slot)
		{
			const FChunkVariant& V = Route.Slots[Slot];
			const float X0 = LevelCatalogue::SlotStartX(Slot);
			const float Mid = X0 + 0.5f * Chunk;
			Out.Add(MakePlacement(ELevelPlacementKind::Floor, Slot, Mid, 0.5f * FloorThick, Chunk, FloorThick));
			// Variant B mirrors the lane arrangement: mechanics sit in the second half.
			const float Shift = V.Variant == 'B' ? LevelPlanConst::VariantShiftFraction * Chunk : -LevelPlanConst::VariantShiftFraction * Chunk;
			int32 Index = 0;
			for (const EChunkMechanic M : V.Mechanics)
			{
				const float X = Mid + Shift + Index * LevelPlanConst::MechanicSpacingFraction * Chunk;
				++Index;
				FLevelPlacement P;
				switch (M)
				{
				case EChunkMechanic::Column:
					P = MakePlacement(ELevelPlacementKind::Column, Slot, X, FloorThick + 0.5f * LevelPlanConst::ColumnHeightFraction * H,
						LevelPlanConst::ColumnWidthFraction * H, LevelPlanConst::ColumnHeightFraction * H);
					break;
				case EChunkMechanic::Mill:
				case EChunkMechanic::Shutter:
				case EChunkMechanic::Bellows:
					P = MakePlacement(ELevelPlacementKind::Trap, Slot, X, LevelPlanConst::MidHeightFraction * H,
						LevelPlanConst::TrapSizeFraction * H, LevelPlanConst::TrapSizeFraction * H);
					break;
				case EChunkMechanic::BridgeTooth:
					P = MakePlacement(ELevelPlacementKind::Trap, Slot, X, H - 0.5f * LevelPlanConst::TrapSizeFraction * H,
						LevelPlanConst::TrapSizeFraction * H, LevelPlanConst::TrapSizeFraction * H);
					break;
				case EChunkMechanic::Warden:
				case EChunkMechanic::Stilt:
					P = MakePlacement(ELevelPlacementKind::Enemy, Slot, X, FloorThick + 0.5f * LevelPlanConst::EnemySizeFraction * H,
						LevelPlanConst::EnemySizeFraction * H, LevelPlanConst::EnemySizeFraction * H);
					break;
				case EChunkMechanic::Courier:
					P = MakePlacement(ELevelPlacementKind::Enemy, Slot, X, LevelPlanConst::HighFraction * H,
						LevelPlanConst::EnemySizeFraction * H, LevelPlanConst::EnemySizeFraction * H);
					break;
				default:
					break;
				}
				P.Mechanic = M;
				if (P.Kind == ELevelPlacementKind::Enemy)
				{
					P.bYellowShot = Colours.FRand() < 0.5f;
				}
				Out.Add(P);
			}
		}

		if (IsFeatureEnabled(EFeatureId::FLOW_27))
		{
			const int32 Checkpoints = LevelPlanField().RouteSlotCount / LevelPlanField().SlotsPerCheckpoint;
			const float RefugeLength = LevelPlanField().RefugeLengthFraction * Chunk;
			for (int32 Cp = 1; Cp <= Checkpoints; ++Cp)
			{
				const float X0 = LevelCatalogue::RefugeStartX(Cp);
				Out.Add(MakePlacement(ELevelPlacementKind::Refuge, Cp, X0 + 0.5f * RefugeLength, 0.5f * FloorThick, RefugeLength, FloorThick));
				if (IsFeatureEnabled(EFeatureId::FLOW_28))
				{
					const FVector Stand = CheckpointStandLocation(Cp);
					Out.Add(MakePlacement(ELevelPlacementKind::Checkpoint, Cp, Stand.X, FloorThick + 0.5f * LevelPlanConst::CheckpointSizeFraction * H,
						LevelPlanConst::CheckpointSizeFraction * H, LevelPlanConst::CheckpointSizeFraction * H));
				}
			}
		}
		return Out;
	}

	FVector CheckpointStandLocation(int32 Checkpoint)
	{
		const float H = LevelPlanArena().ArenaHeight;
		const float RefugeLength = LevelPlanField().RefugeLengthFraction * LevelPlanField().ChunkLength;
		const float X = LevelCatalogue::RefugeStartX(Checkpoint) + LevelPlanConst::StandInsetFraction * RefugeLength;
		return FVector(X, UmbrellaDrawOrder::EllaY, LevelPlanConst::FloorThicknessFraction * H + LevelPlanConst::EnemySizeFraction * H);
	}

	int32 CheckpointReachedAt(float EllaX)
	{
		const int32 Checkpoints = LevelPlanField().RouteSlotCount / LevelPlanField().SlotsPerCheckpoint;
		int32 Reached = 0;
		for (int32 Cp = 1; Cp <= Checkpoints; ++Cp)
		{
			if (EllaX >= LevelCatalogue::RefugeStartX(Cp))
			{
				Reached = Cp;
			}
		}
		return Reached;
	}

	float KeeperHandoffX()
	{
		return LevelCatalogue::RouteLength() - LevelRules::VestibuleLength(LevelPlanArena().ArenaWidth);
	}
}
