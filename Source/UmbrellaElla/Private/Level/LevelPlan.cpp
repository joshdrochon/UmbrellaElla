#include "Level/LevelPlan.h"
#include "Arena/ArenaCameraTuning.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaTuning.h"
#include "Enemy/EnemyRules.h"
#include "Enemy/EnemyTuning.h"
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
		// Gameplay pieces sit in Ella's plane so she collides with land, overlaps currents and traps, and is shot.
		P.Location = FVector(X, UmbrellaDrawOrder::EllaY, Z);
		P.Size = FVector(W, LevelPlanConst::SolidDepth, H);
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
		TArray<int32> FreeColourEnemies;

		for (int32 Slot = 0; Slot < Route.Slots.Num(); ++Slot)
		{
			const FChunkVariant& V = Route.Slots[Slot];
			const float X0 = LevelCatalogue::SlotStartX(Slot);
			Out.Add(MakePlacement(ELevelPlacementKind::Floor, Slot, X0 + 0.5f * Chunk, 0.5f * FloorThick, Chunk, FloorThick));
			const FChunkLayout Layout = ChunkLayouts::Get(V.Chunk, V.Variant);
			for (const FChunkPiece& Piece : Layout.Pieces)
			{
				const FVector2D C = Piece.Centre();
				const FVector2D Size = Piece.Rect.GetSize();
				FLevelPlacement P = MakePlacement(ELevelPlacementKind::Solid, Slot, X0 + C.X * Chunk, C.Y * H, Size.X * Chunk, Size.Y * H);
				P.Mechanic = Piece.Mechanic;
				switch (Piece.Kind)
				{
				case EChunkPieceKind::Wind:
					P.Kind = ELevelPlacementKind::Wind;
					P.WindDirection = Piece.Direction;
					P.WindRole = Piece.Role;
					P.bBypass = Piece.bBypass;
					break;
				case EChunkPieceKind::Trap:
					P.Kind = ELevelPlacementKind::Trap;
					break;
				case EChunkPieceKind::Enemy:
				{
					P.Kind = ELevelPlacementKind::Enemy;
					const FVector2D Body = ChunkLayouts::HazardRect(Piece).GetSize();
					P.Size = FVector(Body.X * Chunk, LevelPlanConst::SolidDepth, Body.Y * H);
					P.bYellowShot = Piece.Colour == EChunkShotColour::Yellow;
					if (Piece.Colour == EChunkShotColour::Any)
					{
						FreeColourEnemies.Add(Out.Num());
					}
					break;
				}
				default:
					break;
				}
				Out.Add(P);
			}
		}
		// Enemies the chunk leaves open get the level-wide red:yellow target from the seeded colour stream.
		const TArray<EUmbrellaShotKind> Assigned = FEnemyRules::AssignShotColors(FreeColourEnemies.Num(), 0,
			GetDefault<UUmbrellaTuning>()->Enemy.RedPerYellow, Colours);
		for (int32 I = 0; I < FreeColourEnemies.Num() && I < Assigned.Num(); ++I)
		{
			Out[FreeColourEnemies[I]].bYellowShot = Assigned[I] == EUmbrellaShotKind::EnemyYellow;
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
