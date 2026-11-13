#include "Level/ChunkLayouts.h"
#include "Level/ChunkCatalogueData.h"
#include "Arena/ArenaCameraTuning.h"
#include "Core/UmbrellaTuning.h"
#include "Enemy/EnemyRules.h"
#include "Enemy/EnemyTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Trap/TrapTuning.h"

namespace
{
	using M = EChunkMechanic;
	using R = EWindRole;

	float ChunkLengthUnits() { return GetDefault<UUmbrellaTuning>()->Field.ChunkLength; }
	float ChunkHeightUnits() { return GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaHeight; }

	FBox2D ChunkRect(float X0, float X1, float Z0, float Z1)
	{
		return FBox2D(FVector2D(X0, Z0), FVector2D(X1, Z1));
	}

	FVector2D ChunkDirectionFor(EWindRole Role)
	{
		switch (Role)
		{
		case R::Descent: return FVector2D(0.0, -1.0);
		case R::Lift: return FVector2D(0.0, 1.0);
		case R::Return: return FVector2D(-1.0, 0.0);
		default: return FVector2D(1.0, 0.0);
		}
	}

	EEnemyType ChunkEnemyType(EChunkMechanic Mechanic)
	{
		return Mechanic == M::Stilt ? EEnemyType::Floodstrider : (Mechanic == M::Courier ? EEnemyType::SkyCourier : EEnemyType::Roadwarden);
	}

	FEnemyProfile ChunkEnemyProfile(EChunkMechanic Mechanic)
	{
		return FEnemyRules::MakeProfile(ChunkEnemyType(Mechanic), GetDefault<UUmbrellaTuning>()->Enemy);
	}

	FChunkPiece ChunkPieceFrom(const FChunkPieceRow& Row)
	{
		FChunkPiece P;
		P.Kind = Row.Kind;
		P.Mechanic = Row.Mechanic;
		P.Colour = Row.Colour;
		P.Rect = ChunkRect(Row.X0, Row.X1, Row.Z0, Row.Z1);
		if (Row.Kind == EChunkPieceKind::Wind)
		{
			P.Role = Row.Role;
			P.Direction = ChunkDirectionFor(Row.Role);
			P.bBypass = Row.bBypass;
		}
		if (Row.Kind == EChunkPieceKind::Enemy && Row.bFeetOnLand)
		{
			// The row gives the land top; the enemy's centre sits half a body above it.
			const float HalfBody = 0.5f * ChunkEnemyProfile(Row.Mechanic).Body.Y / ChunkHeightUnits();
			P.Rect = ChunkRect(Row.X0, Row.X1, Row.Z0 + HalfBody, Row.Z1 + HalfBody);
		}
		return P;
	}

	bool ChunkRectsOverlap(const FBox2D& A, const FBox2D& B)
	{
		const double W = FMath::Min(A.Max.X, B.Max.X) - FMath::Max(A.Min.X, B.Min.X);
		const double H = FMath::Min(A.Max.Y, B.Max.Y) - FMath::Max(A.Min.Y, B.Min.Y);
		return W > ChunkLayoutConst::OverlapEpsilon && H > ChunkLayoutConst::OverlapEpsilon;
	}

	bool ChunkContains(const FBox2D& Box, const FVector2D& P)
	{
		return P.X >= Box.Min.X && P.X <= Box.Max.X && P.Y >= Box.Min.Y && P.Y <= Box.Max.Y;
	}

	FBox2D ChunkInterfaceBand(bool bExit)
	{
		return bExit ? ChunkRect(1.0f - ChunkLayoutConst::EdgeBand, 1.0f, ChunkLayoutConst::InterfaceLow, ChunkLayoutConst::InterfaceHigh)
					 : ChunkRect(0.0f, ChunkLayoutConst::EdgeBand, ChunkLayoutConst::InterfaceLow, ChunkLayoutConst::InterfaceHigh);
	}

	/** Where a wind piece hands the player on: its downstream edge, a probe beyond it. */
	FVector2D ChunkWindEnd(const FChunkPiece& P)
	{
		const FVector2D C = P.Centre();
		const FVector2D Half = P.Rect.GetExtent();
		return C + FVector2D(P.Direction.X * (Half.X + ChunkLayoutConst::RejoinProbe), P.Direction.Y * (Half.Y + ChunkLayoutConst::RejoinProbe));
	}
}

TArray<const FChunkPiece*> FChunkLayout::Of(EChunkPieceKind Kind) const
{
	TArray<const FChunkPiece*> Out;
	for (const FChunkPiece& P : Pieces)
	{
		if (P.Kind == Kind)
		{
			Out.Add(&P);
		}
	}
	return Out;
}

TArray<const FChunkPiece*> FChunkLayout::Winds(EWindRole Role) const
{
	TArray<const FChunkPiece*> Out;
	for (const FChunkPiece& P : Pieces)
	{
		if (P.Kind == EChunkPieceKind::Wind && P.Role == Role)
		{
			Out.Add(&P);
		}
	}
	return Out;
}

TArray<const FChunkPiece*> FChunkLayout::Bypass() const
{
	TArray<const FChunkPiece*> Out;
	for (const FChunkPiece& P : Pieces)
	{
		if (P.Kind == EChunkPieceKind::Wind && P.bBypass)
		{
			Out.Add(&P);
		}
	}
	return Out;
}

FString FChunkLayout::Signature() const
{
	TArray<FString> Parts;
	for (const FChunkPiece& P : Pieces)
	{
		Parts.Add(FString::Printf(TEXT("%d/%d/%d/%d:%.2f,%.2f,%.2f,%.2f"), static_cast<int32>(P.Kind), static_cast<int32>(P.Role),
			static_cast<int32>(P.Mechanic), P.bBypass ? 1 : 0, P.Rect.Min.X, P.Rect.Max.X, P.Rect.Min.Y, P.Rect.Max.Y));
	}
	return FString::Join(Parts, TEXT(";"));
}

namespace ChunkLayouts
{
	bool IsChunkEnabled(int32 Chunk)
	{
		// One flag per authored chunk, in chunk order (index 0 is unused: chunks count from 1).
		const bool bEnabled[] = {false, IsFeatureEnabled(EFeatureId::HAZ_25), IsFeatureEnabled(EFeatureId::HAZ_26),
			IsFeatureEnabled(EFeatureId::HAZ_27), IsFeatureEnabled(EFeatureId::HAZ_28), IsFeatureEnabled(EFeatureId::HAZ_29),
			IsFeatureEnabled(EFeatureId::HAZ_30), IsFeatureEnabled(EFeatureId::HAZ_31), IsFeatureEnabled(EFeatureId::HAZ_32),
			IsFeatureEnabled(EFeatureId::HAZ_33), IsFeatureEnabled(EFeatureId::HAZ_34), IsFeatureEnabled(EFeatureId::HAZ_35),
			IsFeatureEnabled(EFeatureId::HAZ_36)};
		return Chunk >= 1 && Chunk < UE_ARRAY_COUNT(bEnabled) && bEnabled[Chunk];
	}

	FChunkLayout Get(int32 Chunk, TCHAR Variant)
	{
		FChunkLayout Layout;
		Layout.Chunk = Chunk;
		Layout.Variant = Variant;
		if (IsChunkEnabled(Chunk) && (Variant == 'A' || Variant == 'B'))
		{
			for (const FChunkPieceRow& Row : ChunkCatalogueData::Rows)
			{
				if (Row.Chunk == Chunk && Row.Variant == Variant)
				{
					Layout.Pieces.Add(ChunkPieceFrom(Row));
				}
			}
			if (!IsFeatureEnabled(EFeatureId::HAZ_38))
			{
				Layout.Pieces.RemoveAll([](const FChunkPiece& P) { return P.bBypass; });
			}
		}
		return Layout;
	}

	FBox2D HazardRect(const FChunkPiece& Piece)
	{
		const float L = ChunkLengthUnits();
		const float H = ChunkHeightUnits();
		FVector2D Size = FVector2D::ZeroVector;
		if (Piece.Kind == EChunkPieceKind::Trap)
		{
			const FTrapTuning& T = GetDefault<UUmbrellaTuning>()->Trap;
			const float Rotor = 2.0f * T.RotorSweptRadius;
			Size = Piece.Mechanic == M::Mill ? FVector2D(Rotor, Rotor)
				: (Piece.Mechanic == M::BridgeTooth ? T.TeethSize : FVector2D(T.TeethSize.X, Rotor));
		}
		else if (Piece.Kind == EChunkPieceKind::Enemy)
		{
			const FEnemyProfile Profile = ChunkEnemyProfile(Piece.Mechanic);
			Size = FVector2D(Profile.Body.X + Profile.PatrolSpan, Profile.Body.Y);
		}
		else
		{
			return Piece.Rect;
		}
		const FVector2D Half(0.5 * Size.X / L, 0.5 * Size.Y / H);
		return FBox2D(Piece.Centre() - Half, Piece.Centre() + Half);
	}

	TArray<FString> Validate(const FChunkLayout& Layout)
	{
		TArray<FString> Problems;
		const FChunkVariant* Variant = LevelCatalogue::Find(Layout.Chunk, Layout.Variant);
		const FString Name = FString::Printf(TEXT("%02d%c"), Layout.Chunk, Layout.Variant);
		if (!Variant || Layout.Pieces.IsEmpty())
		{
			Problems.Add(Name + TEXT(": no authored layout"));
			return Problems;
		}
		const FBox2D Unit(FVector2D(0.0, 0.0), FVector2D(1.0, 1.0));
		for (const FChunkPiece& P : Layout.Pieces)
		{
			const FBox2D Box = HazardRect(P);
			if (Box.Min.X < 0.0 || Box.Max.X > 1.0 || Box.Min.Y < 0.0 || Box.Max.Y > 1.0)
			{
				Problems.Add(Name + TEXT(": a piece leaves the chunk"));
			}
			if (P.Kind != EChunkPieceKind::Wind)
			{
				for (const bool bExit : {false, true})
				{
					if (ChunkRectsOverlap(Box, ChunkInterfaceBand(bExit)))
					{
						Problems.Add(Name + (bExit ? TEXT(": exit") : TEXT(": entrance")) + TEXT(" interface N blocked"));
					}
				}
			}
		}
		const TArray<const FChunkPiece*> Returns = Layout.Winds(EWindRole::Return);
		if (Returns.IsEmpty())
		{
			Problems.Add(Name + TEXT(": no return current"));
		}
		for (const FChunkPiece* P : Returns)
		{
			if (P->Rect.Min.X < ChunkLayoutConst::EdgeBand)
			{
				Problems.Add(Name + TEXT(": a return current strands the player left of the entrance"));
			}
		}
		const TArray<const FChunkPiece*> AllWinds = Layout.Of(EChunkPieceKind::Wind);
		for (int32 I = 0; I < AllWinds.Num(); ++I)
		{
			for (int32 J = I + 1; J < AllWinds.Num(); ++J)
			{
				if (ChunkRectsOverlap(AllWinds[I]->Rect, AllWinds[J]->Rect))
				{
					Problems.Add(Name + TEXT(": two currents overlap"));
				}
			}
			for (const FChunkPiece* S : Layout.Of(EChunkPieceKind::Solid))
			{
				if (ChunkRectsOverlap(AllWinds[I]->Rect, S->Rect))
				{
					Problems.Add(Name + TEXT(": a current runs into land"));
				}
			}
		}
		for (const EChunkMechanic Mech : Variant->Mechanics)
		{
			bool bFound = false;
			for (const FChunkPiece& P : Layout.Pieces)
			{
				if (Mech == M::Column)
				{
					const FVector2D Size = P.Rect.GetSize();
					bFound |= P.Kind == EChunkPieceKind::Wind && !P.bBypass && (P.Role == EWindRole::Descent || P.Role == EWindRole::Lift)
						&& Size.Y >= ChunkLayoutConst::ColumnMinHeight && Size.X <= ChunkLayoutConst::ColumnMaxWidth;
				}
				else
				{
					bFound |= P.Mechanic == Mech && (P.Kind == EChunkPieceKind::Trap || P.Kind == EChunkPieceKind::Enemy);
				}
			}
			if (!bFound)
			{
				Problems.Add(FString::Printf(TEXT("%s: mechanic %d not placed"), *Name, static_cast<int32>(Mech)));
			}
		}
		for (const FChunkPiece* E : Layout.Of(EChunkPieceKind::Enemy))
		{
			const FBox2D Box = HazardRect(*E);
			bool bStands = false;
			bool bResting = false;
			for (const FChunkPiece* S : Layout.Of(EChunkPieceKind::Solid))
			{
				const bool bUnder = Box.Min.X < S->Rect.Max.X && Box.Max.X > S->Rect.Min.X;
				bStands |= FMath::Abs(Box.Min.Y - S->Rect.Max.Y) <= ChunkLayoutConst::StandTolerance && Box.Min.X >= S->Rect.Min.X - ChunkLayoutConst::StandTolerance
					&& Box.Max.X <= S->Rect.Max.X + ChunkLayoutConst::StandTolerance;
				bResting |= bUnder && Box.Min.Y >= S->Rect.Max.Y - ChunkLayoutConst::StandTolerance && Box.Min.Y - S->Rect.Max.Y <= ChunkLayoutConst::CourierClearance;
			}
			if (E->Mechanic == M::Warden && !bStands)
			{
				Problems.Add(Name + TEXT(": a Roadwarden does not stand on land wide enough for its patrol"));
			}
			if (E->Mechanic == M::Courier && bResting)
			{
				Problems.Add(Name + TEXT(": a Sky Courier rests on land (air-only)"));
			}
		}
		return Problems;
	}

	TArray<FString> ValidateBypass(const FChunkLayout& Layout)
	{
		TArray<FString> Problems;
		const FString Name = FString::Printf(TEXT("%02d%c"), Layout.Chunk, Layout.Variant);
		const TArray<const FChunkPiece*> Pieces = Layout.Bypass();
		if (Pieces.IsEmpty())
		{
			Problems.Add(Name + TEXT(": no bypass"));
			return Problems;
		}
		const FChunkPiece* Last = Pieces[0];
		for (const FChunkPiece* B : Pieces)
		{
			if (B->Rect.GetSize().X > ChunkLayoutConst::MaxBypassLength || (B->Rect.Min.X < ChunkLayoutConst::EdgeBand && B->Rect.Max.X > 1.0f - ChunkLayoutConst::EdgeBand))
			{
				Problems.Add(Name + TEXT(": a bypass piece skips the chunk instead of transferring"));
			}
			for (const FChunkPiece& P : Layout.Pieces)
			{
				if ((P.Kind == EChunkPieceKind::Trap || P.Kind == EChunkPieceKind::Enemy) && ChunkRectsOverlap(B->Rect, HazardRect(P)))
				{
					Problems.Add(Name + TEXT(": the bypass rides through a hazard"));
				}
			}
			Last = B->Rect.Max.X > Last->Rect.Max.X ? B : Last;
		}
		// Rejoin N: the last bypass piece hands over to a main current or into the exit corridor.
		const FVector2D End = ChunkWindEnd(*Last);
		bool bRejoins = ChunkContains(ChunkRect(ChunkLayoutConst::ExitCorridorStart, 1.0f, ChunkLayoutConst::InterfaceLow, ChunkLayoutConst::InterfaceHigh), End);
		for (const FChunkPiece* W : Layout.Of(EChunkPieceKind::Wind))
		{
			bRejoins |= !W->bBypass && ChunkContains(W->Rect, End);
		}
		if (!bRejoins)
		{
			Problems.Add(Name + TEXT(": the bypass does not rejoin interface N"));
		}
		return Problems;
	}
}
