#include "Core/UmbrellaDrawOrder.h"
#include "Level/ChunkLayouts.h"
#include "Level/LevelCatalogue.h"
#include "Level/LevelPlan.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#define UMBRELLAELLA_CHUNK_TEST_FLAGS (EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

namespace
{
	constexpr float ChunkTestMidLow = ChunkLayoutConst::InterfaceLow;
	constexpr float ChunkTestMidHigh = ChunkLayoutConst::InterfaceHigh;
	constexpr float ChunkTestNear = 0.03f;

	bool ChunkTestIsMid(float Z) { return Z >= ChunkTestMidLow && Z <= ChunkTestMidHigh; }

	const FChunkPiece* ChunkTestFirst(const FChunkLayout& L, EChunkPieceKind Kind, EChunkMechanic Mech)
	{
		for (const FChunkPiece& P : L.Pieces)
		{
			if (P.Kind == Kind && P.Mechanic == Mech)
			{
				return &P;
			}
		}
		return nullptr;
	}

	/** any wind of Role, not part of the bypass unless bAllowBypass, matching Pred. */
	template <typename TPred>
	bool ChunkTestAnyWind(const FChunkLayout& L, EWindRole Role, TPred Pred, bool bAllowBypass = false)
	{
		for (const FChunkPiece* P : L.Winds(Role))
		{
			if ((bAllowBypass || !P->bBypass) && Pred(*P))
			{
				return true;
			}
		}
		return false;
	}

	template <typename TPred>
	bool ChunkTestAnyBypass(const FChunkLayout& L, TPred Pred)
	{
		for (const FChunkPiece* P : L.Bypass())
		{
			if (Pred(*P))
			{
				return true;
			}
		}
		return false;
	}

	template <typename TPred>
	bool ChunkTestAnySolid(const FChunkLayout& L, TPred Pred)
	{
		for (const FChunkPiece* P : L.Of(EChunkPieceKind::Solid))
		{
			if (Pred(*P))
			{
				return true;
			}
		}
		return false;
	}

	bool ChunkTestReachesExitMid(const FChunkPiece& P)
	{
		return P.Rect.Max.X >= 1.0 - ChunkTestNear && ChunkTestIsMid(P.Centre().Y);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FChunkLayoutsValid, "UmbrellaElla.Level.ChunkLayoutsAllVariantsValid", UMBRELLAELLA_CHUNK_TEST_FLAGS)
bool FChunkLayoutsValid::RunTest(const FString& Parameters)
{
	int32 Checked = 0;
	for (const FChunkVariant& V : LevelCatalogue::All())
	{
		const FChunkLayout L = ChunkLayouts::Get(V.Chunk, V.Variant);
		for (const FString& Problem : ChunkLayouts::Validate(L))
		{
			AddError(Problem);
		}
		for (const FString& Problem : ChunkLayouts::ValidateBypass(L))
		{
			AddError(Problem);
		}
		TestTrue(*FString::Printf(TEXT("%s has its own currents"), *V.Label()), L.Of(EChunkPieceKind::Wind).Num() >= 3);
		if (V.Variant == 'A')
		{
			const FChunkLayout B = ChunkLayouts::Get(V.Chunk, 'B');
			TestNotEqual(*FString::Printf(TEXT("chunk %d: A and B are different arrangements"), V.Chunk), L.Signature(), B.Signature());
		}
		++Checked;
	}
	TestEqual(TEXT("all 24 variants checked"), Checked, 24);
	TestTrue(TEXT("no chunk 13"), ChunkLayouts::Get(13, 'A').Pieces.IsEmpty());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FChunkLayoutsWords, "UmbrellaElla.Level.ChunkLayoutsMatchCatalogue", UMBRELLAELLA_CHUNK_TEST_FLAGS)
bool FChunkLayoutsWords::RunTest(const FString& Parameters)
{
	using K = EChunkPieceKind;
	using M = EChunkMechanic;
	using R = EWindRole;
	{	// CH01A: a middle current ends about 0.45 W, then a drop to the lower right lane.
		const FChunkLayout L = ChunkLayouts::Get(1, 'A');
		TestTrue(TEXT("01A middle current ends near 0.45W"), ChunkTestAnyWind(L, R::Transport, [](const FChunkPiece& P)
			{ return FMath::IsNearlyEqual(P.Rect.Max.X, 0.45, ChunkTestNear) && ChunkTestIsMid(P.Centre().Y); }));
		TestTrue(TEXT("01A lower right lane"), ChunkTestAnyWind(L, R::Transport, [](const FChunkPiece& P)
			{ return P.Rect.Min.X >= 0.45 && P.Centre().Y < ChunkTestMidLow; }));
	}
	{	// CH01B: high lane after the vestibule bends into a broad descent column, middle exit below, lift return.
		const FChunkLayout L = ChunkLayouts::Get(1, 'B');
		TestTrue(TEXT("01B high lane after the vestibule"), ChunkTestAnyWind(L, R::Transport, [](const FChunkPiece& P)
			{ return P.Rect.Min.X >= 0.2 - ChunkTestNear && P.Centre().Y > ChunkTestMidHigh; }));
		TestTrue(TEXT("01B broad descent column"), ChunkTestAnyWind(L, R::Descent, [](const FChunkPiece& P) { return P.Rect.GetSize().X >= 0.15; }));
		TestTrue(TEXT("01B middle exit"), ChunkTestAnyWind(L, R::Transport, &ChunkTestReachesExitMid));
		TestTrue(TEXT("01B lift-current return"), L.Winds(R::Lift).Num() >= 1);
	}
	const FChunkLayout Rooftop2A = ChunkLayouts::Get(2, 'A');
	const FChunkLayout Rooftop2B = ChunkLayouts::Get(2, 'B');
	const FChunkPiece* WardenA = ChunkTestFirst(Rooftop2A, K::Enemy, M::Warden);
	const FChunkPiece* WardenB = ChunkTestFirst(Rooftop2B, K::Enemy, M::Warden);
	if (TestNotNull(TEXT("02A warden"), WardenA) && TestNotNull(TEXT("02B warden"), WardenB))
	{
		const float ZA = WardenA->Centre().Y;
		const float ZB = WardenB->Centre().Y;
		const FChunkLayout& A = Rooftop2A;
		const FChunkLayout& B = Rooftop2B;
		TestTrue(TEXT("02A low right-roof Warden"), ZA < ChunkTestMidLow && WardenA->Centre().X > 0.5);
		TestTrue(TEXT("02A upper bypass"), ChunkTestAnyBypass(A, [ZA](const FChunkPiece& P) { return P.Centre().Y > ZA + 0.3; }));
		TestTrue(TEXT("02B higher bridge-lip Warden"), ZB > ZA);
		TestTrue(TEXT("02B low bypass"), ChunkTestAnyBypass(B, [ZB](const FChunkPiece& P) { return P.Centre().Y < ZB - 0.2; }));
		float LedgeX = 1.0f;
		for (const FChunkPiece* S : B.Of(K::Solid))
		{
			LedgeX = FMath::Min(LedgeX, static_cast<float>(S->Rect.Min.X));
		}
		TestTrue(TEXT("02B firing descent ahead of the ledge"), ChunkTestAnyWind(B, R::Descent, [LedgeX](const FChunkPiece& P) { return P.Rect.Max.X <= LedgeX; }));
		TestTrue(TEXT("02B left reset ahead of the ledge"), ChunkTestAnyWind(B, R::Return, [LedgeX](const FChunkPiece& P) { return P.Rect.Max.X <= LedgeX; }));
	}
	{	// CH03: yellow Courier; A above/right with a middle catch column, B level/right with a lower one and a higher bypass.
		const FChunkLayout A = ChunkLayouts::Get(3, 'A');
		const FChunkLayout B = ChunkLayouts::Get(3, 'B');
		const FChunkPiece* CA = ChunkTestFirst(A, K::Enemy, M::Courier);
		const FChunkPiece* CB = ChunkTestFirst(B, K::Enemy, M::Courier);
		if (TestNotNull(TEXT("03A courier"), CA) && TestNotNull(TEXT("03B courier"), CB))
		{
			TestTrue(TEXT("03A courier above/right, yellow"), CA->Centre().Y > ChunkTestMidHigh && CA->Centre().X > 0.5 && CA->Colour == EChunkShotColour::Yellow);
			TestTrue(TEXT("03B courier level/right, yellow"), ChunkTestIsMid(CB->Centre().Y) && CB->Centre().X > 0.5 && CB->Colour == EChunkShotColour::Yellow);
			TestTrue(TEXT("03A middle catch column"), ChunkTestAnyWind(A, R::Lift, [](const FChunkPiece& P)
				{ return FMath::Abs(P.Centre().X - 0.5) < 0.1 && P.Rect.Min.Y < ChunkTestMidLow && P.Rect.Max.Y > ChunkTestMidHigh; }));
			TestTrue(TEXT("03B lower catch column"), ChunkTestAnyWind(B, R::Lift, [](const FChunkPiece& P)
				{ return FMath::Abs(P.Centre().X - 0.5) < 0.1 && P.Rect.Max.Y < ChunkTestMidLow; }));
			TestTrue(TEXT("03B higher transport bypass"), ChunkTestAnyBypass(B, [](const FChunkPiece& P)
				{ return P.Role == EWindRole::Transport && P.Centre().Y > ChunkTestMidHigh; }));
		}
	}
	{	// CH04: Floodstrider; A feet on a low bridge, body across the middle, low passage open; B on an offset shelf, body high.
		const FChunkLayout A = ChunkLayouts::Get(4, 'A');
		const FChunkLayout B = ChunkLayouts::Get(4, 'B');
		const FChunkPiece* SA = ChunkTestFirst(A, K::Enemy, M::Stilt);
		const FChunkPiece* SB = ChunkTestFirst(B, K::Enemy, M::Stilt);
		if (TestNotNull(TEXT("04A stilt"), SA) && TestNotNull(TEXT("04B stilt"), SB))
		{
			const float XA = SA->Centre().X;
			TestTrue(TEXT("04A body across the middle"), ChunkTestIsMid(SA->Centre().Y));
			TestTrue(TEXT("04A low bridge under the stilt"), ChunkTestAnySolid(A, [XA](const FChunkPiece& P)
				{ return P.Rect.Max.Y < ChunkTestMidLow && P.Rect.Min.X <= XA && P.Rect.Max.X >= XA; }));
			TestTrue(TEXT("04A low passage open under the bridge"), ChunkTestAnyWind(A, R::Transport, [XA](const FChunkPiece& P)
				{ return P.Rect.Max.Y <= 0.26 && P.Rect.Min.X <= XA && P.Rect.Max.X >= XA; }));
			const float XB = SB->Centre().X;
			TestTrue(TEXT("04B body high"), SB->Centre().Y > ChunkTestMidHigh);
			TestTrue(TEXT("04B offset shelf"), ChunkTestAnySolid(B, [XB](const FChunkPiece& P)
				{ return P.Rect.Min.Y >= 0.5 && P.Rect.Min.X <= XB && P.Rect.Max.X >= XB; }));
			TestTrue(TEXT("04B middle passage"), ChunkTestAnyWind(B, R::Transport, [XB](const FChunkPiece& P)
				{ return ChunkTestIsMid(P.Centre().Y) && P.Rect.Max.X > XB; }));
			TestTrue(TEXT("04B lift return beyond"), ChunkTestAnyWind(B, R::Lift, [XB](const FChunkPiece& P) { return P.Rect.Min.X > XB; }));
		}
	}
	for (const int32 Chunk : {5, 6})
	{	// CH05 / CH06: A rotor high, B rotor low.
		const FChunkLayout LA = ChunkLayouts::Get(Chunk, 'A');
		const FChunkLayout LB = ChunkLayouts::Get(Chunk, 'B');
		const FChunkPiece* MA = ChunkTestFirst(LA, K::Trap, M::Mill);
		const FChunkPiece* MB = ChunkTestFirst(LB, K::Trap, M::Mill);
		if (TestNotNull(TEXT("mill A"), MA) && TestNotNull(TEXT("mill B"), MB))
		{
			TestTrue(*FString::Printf(TEXT("%02dA high rotor"), Chunk), MA->Centre().Y > ChunkTestMidHigh);
			TestTrue(*FString::Printf(TEXT("%02dB low rotor"), Chunk), MB->Centre().Y < ChunkTestMidLow);
		}
	}
	{
		const FChunkLayout A = ChunkLayouts::Get(5, 'A');
		const FChunkLayout B = ChunkLayouts::Get(5, 'B');
		const FBox2D RotorA = ChunkLayouts::HazardRect(*ChunkTestFirst(A, K::Trap, M::Mill));
		const FBox2D RotorB = ChunkLayouts::HazardRect(*ChunkTestFirst(B, K::Trap, M::Mill));
		TestTrue(TEXT("05A lower lane below the rotor"), ChunkTestAnyWind(A, R::Transport, [RotorA](const FChunkPiece& P)
			{ return P.Rect.Max.Y <= RotorA.Min.Y && P.Centre().Y < ChunkTestMidLow; }));
		TestTrue(TEXT("05B path above the rotor"), ChunkTestAnyWind(B, R::Transport, [RotorB](const FChunkPiece& P)
			{ return P.Rect.Min.Y >= RotorB.Max.Y && P.Rect.Min.X < RotorB.Max.X && P.Rect.Max.X > RotorB.Min.X; }));
		TestTrue(TEXT("05B lift assists the climb"), B.Winds(R::Lift).Num() >= 1);
		TestFalse(TEXT("05B no long minimum-lift-only climb"), ChunkTestAnyWind(B, R::Lift, [](const FChunkPiece& P) { return P.Rect.GetSize().Y > 0.4; }));
	}
	{	// CH06: A return upstream (left) of the high rotor feeds a lower right exit; B return downstream of the low rotor feeds a lifted exit.
		const FChunkLayout A = ChunkLayouts::Get(6, 'A');
		const FChunkLayout B = ChunkLayouts::Get(6, 'B');
		const float XA = ChunkTestFirst(A, K::Trap, M::Mill)->Centre().X;
		const float XB = ChunkTestFirst(B, K::Trap, M::Mill)->Centre().X;
		TestTrue(TEXT("06A return upstream of the rotor"), ChunkTestAnyWind(A, R::Return, [XA](const FChunkPiece& P) { return P.Centre().X < XA; }));
		TestTrue(TEXT("06A lower right exit lane"), ChunkTestAnyWind(A, R::Transport, [XA](const FChunkPiece& P)
			{ return P.Centre().Y < ChunkTestMidLow && P.Rect.Max.X > XA; }));
		TestTrue(TEXT("06B return downstream of the rotor"), ChunkTestAnyWind(B, R::Return, [XB](const FChunkPiece& P) { return P.Centre().X > XB; }));
		TestTrue(TEXT("06B lifted right exit"), ChunkTestAnyWind(B, R::Transport, [](const FChunkPiece& P)
			{ return P.Rect.Max.X >= 1.0 - ChunkTestNear && P.Centre().Y >= 0.5; }));
	}
	{	// CH07: A upper timed gap with an open broad low detour; B lower timed gap with an assisted upper detour.
		const FChunkLayout A = ChunkLayouts::Get(7, 'A');
		const FChunkLayout B = ChunkLayouts::Get(7, 'B');
		const FBox2D GapA = ChunkLayouts::HazardRect(*ChunkTestFirst(A, K::Trap, M::Shutter));
		const FBox2D GapB = ChunkLayouts::HazardRect(*ChunkTestFirst(B, K::Trap, M::Shutter));
		TestTrue(TEXT("07A upper timed gap"), GapA.GetCenter().Y > 0.5);
		TestTrue(TEXT("07A broad low detour"), ChunkTestAnyBypass(A, [GapA](const FChunkPiece& P)
			{ return P.Role == EWindRole::Transport && P.Rect.Max.Y < GapA.Min.Y && P.Rect.GetSize().X >= 0.4 && P.Rect.GetSize().Y >= 0.2; }));
		TestTrue(TEXT("07B lower timed gap"), GapB.GetCenter().Y < 0.5);
		TestTrue(TEXT("07B assisted upper detour"), ChunkTestAnyBypass(B, [](const FChunkPiece& P) { return P.Role == EWindRole::Lift; })
			&& ChunkTestAnyBypass(B, [GapB](const FChunkPiece& P) { return P.Role == EWindRole::Transport && P.Rect.Min.Y > GapB.Max.Y; }));
	}
	{	// CH08: A middle hostile band with a clear lower crossing; B lower band with a clear upper lift crossing.
		const FChunkLayout A = ChunkLayouts::Get(8, 'A');
		const FChunkLayout B = ChunkLayouts::Get(8, 'B');
		const FBox2D BandA = ChunkLayouts::HazardRect(*ChunkTestFirst(A, K::Trap, M::Bellows));
		const FBox2D BandB = ChunkLayouts::HazardRect(*ChunkTestFirst(B, K::Trap, M::Bellows));
		TestTrue(TEXT("08A middle band"), ChunkTestIsMid(BandA.GetCenter().Y));
		TestTrue(TEXT("08A clear lower crossing"), ChunkTestAnyWind(A, R::Transport, [BandA](const FChunkPiece& P)
			{ return P.Rect.Max.Y <= BandA.Min.Y && P.Rect.Min.X < BandA.Min.X && P.Rect.Max.X > BandA.Max.X; }));
		TestTrue(TEXT("08B lower band"), BandB.GetCenter().Y < ChunkTestMidLow);
		TestTrue(TEXT("08B clear upper lift crossing"), B.Winds(R::Lift).Num() >= 1 && ChunkTestAnyWind(B, R::Transport, [BandB](const FChunkPiece& P)
			{ return P.Rect.Min.Y >= BandB.Max.Y && P.Rect.Min.X <= BandB.Min.X && P.Rect.Max.X >= BandB.Max.X; }));
	}
	{	// CH09: A high eave, drop beneath and recatch the right flow; B low bridge tooth, assisted rise then middle flow.
		const FChunkLayout A = ChunkLayouts::Get(9, 'A');
		const FChunkLayout B = ChunkLayouts::Get(9, 'B');
		const FChunkPiece* ToothA = ChunkTestFirst(A, K::Trap, M::BridgeTooth);
		const FChunkPiece* ToothB = ChunkTestFirst(B, K::Trap, M::BridgeTooth);
		if (TestNotNull(TEXT("09A tooth"), ToothA) && TestNotNull(TEXT("09B tooth"), ToothB))
		{
			TestTrue(TEXT("09A high eave"), ToothA->Centre().Y > 0.6 && ChunkTestAnySolid(A, [](const FChunkPiece& P) { return P.Rect.Min.Y > 0.6; }));
			TestTrue(TEXT("09A drop beneath and recatch right flow"), A.Winds(R::Descent).Num() >= 1 && ChunkTestAnyWind(A, R::Transport,
				[](const FChunkPiece& P) { return P.Rect.Max.Y < 0.6 && P.Rect.Min.X > 0.4; }));
			TestTrue(TEXT("09B low bridge tooth"), ToothB->Centre().Y < ChunkTestMidLow);
			TestTrue(TEXT("09B assisted rise then middle flow"), B.Winds(R::Lift).Num() >= 1 && ChunkTestAnyWind(B, R::Transport, &ChunkTestReachesExitMid));
		}
	}
	{	// CH10 switchback, net progress right.
		const FChunkLayout A = ChunkLayouts::Get(10, 'A');
		const FChunkLayout B = ChunkLayouts::Get(10, 'B');
		TestTrue(TEXT("10A right low"), ChunkTestAnyWind(A, R::Transport, [](const FChunkPiece& P) { return P.Centre().Y < ChunkTestMidLow; }));
		TestTrue(TEXT("10A left middle reset"), ChunkTestAnyWind(A, R::Return, [](const FChunkPiece& P) { return ChunkTestIsMid(P.Centre().Y); }));
		TestTrue(TEXT("10A right upper exit"), ChunkTestAnyWind(A, R::Transport, [](const FChunkPiece& P)
			{ return P.Rect.Max.X >= 1.0 - ChunkTestNear && P.Centre().Y > 0.55; }));
		TestTrue(TEXT("10B right upper"), ChunkTestAnyWind(B, R::Transport, [](const FChunkPiece& P) { return P.Centre().Y > ChunkTestMidHigh; }));
		TestTrue(TEXT("10B left lower reset"), ChunkTestAnyWind(B, R::Return, [](const FChunkPiece& P) { return P.Centre().Y < ChunkTestMidLow; }));
		const FChunkPiece* Exit = nullptr;
		for (const FChunkPiece* P : B.Winds(R::Transport))
		{
			Exit = !P->bBypass && ChunkTestReachesExitMid(*P) ? P : Exit;
		}
		if (TestNotNull(TEXT("10B right middle exit"), Exit))
		{
			const FBox2D E = Exit->Rect;
			TestTrue(TEXT("10B descent column aligned with the exit"), ChunkTestAnyWind(B, R::Descent, [E](const FChunkPiece& P)
				{ return FMath::IsNearlyEqual(P.Rect.Min.Y, E.Max.Y, ChunkTestNear) && P.Rect.Min.X >= E.Min.X && P.Rect.Max.X <= E.Max.X; }));
		}
	}
	{	// CH11: A high mill then a low right Warden; B low mill then a middle right Warden, a recovery flow between.
		const FChunkLayout A = ChunkLayouts::Get(11, 'A');
		const FChunkLayout B = ChunkLayouts::Get(11, 'B');
		const FChunkPiece* MA = ChunkTestFirst(A, K::Trap, M::Mill);
		const FChunkPiece* WA = ChunkTestFirst(A, K::Enemy, M::Warden);
		const FChunkPiece* MB = ChunkTestFirst(B, K::Trap, M::Mill);
		const FChunkPiece* WB = ChunkTestFirst(B, K::Enemy, M::Warden);
		if (TestTrue(TEXT("11 pieces"), MA && WA && MB && WB))
		{
			TestTrue(TEXT("11A high mill then low right Warden"), MA->Centre().Y > ChunkTestMidHigh && WA->Centre().Y < ChunkTestMidLow && MA->Centre().X < WA->Centre().X);
			TestTrue(TEXT("11B low mill then middle right Warden"), MB->Centre().Y < ChunkTestMidLow && ChunkTestIsMid(WB->Centre().Y) && MB->Centre().X < WB->Centre().X);
			const float From = MB->Centre().X;
			const float To = WB->Centre().X;
			TestTrue(TEXT("11B recovery flow separates the demands"), ChunkTestAnyWind(B, R::Lift, [From, To](const FChunkPiece& P)
				{ return P.Centre().X > From && P.Centre().X < To; }));
		}
	}
	{	// CH12: A stilt high/right, Courier middle/right; B stilt middle/right, Courier high/right, separate catch column.
		const FChunkLayout A = ChunkLayouts::Get(12, 'A');
		const FChunkLayout B = ChunkLayouts::Get(12, 'B');
		const FChunkPiece* SA = ChunkTestFirst(A, K::Enemy, M::Stilt);
		const FChunkPiece* CA = ChunkTestFirst(A, K::Enemy, M::Courier);
		const FChunkPiece* SB = ChunkTestFirst(B, K::Enemy, M::Stilt);
		const FChunkPiece* CB = ChunkTestFirst(B, K::Enemy, M::Courier);
		if (TestTrue(TEXT("12 pieces"), SA && CA && SB && CB))
		{
			TestTrue(TEXT("12A stilt high/right, courier middle/right"), SA->Centre().Y > ChunkTestMidHigh && ChunkTestIsMid(CA->Centre().Y) && SA->Centre().X > 0.5 && CA->Centre().X > 0.5);
			TestTrue(TEXT("12B stilt middle/right, courier high/right"), ChunkTestIsMid(SB->Centre().Y) && CB->Centre().Y > ChunkTestMidHigh);
			const FBox2D HS = ChunkLayouts::HazardRect(*SB);
			const FBox2D HC = ChunkLayouts::HazardRect(*CB);
			TestTrue(TEXT("12B separate catch column"), ChunkTestAnyWind(B, R::Lift, [HS, HC](const FChunkPiece& P)
				{ return P.Rect.Max.X <= HS.Min.X && P.Rect.Max.X <= HC.Min.X && P.Rect.GetSize().Y >= ChunkLayoutConst::ColumnMinHeight; }));
			TestTrue(TEXT("12B stilt bypass"), !B.Bypass().IsEmpty());
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FChunkBypassRules, "UmbrellaElla.Level.BypassIsSaferTransfer", UMBRELLAELLA_CHUNK_TEST_FLAGS)
bool FChunkBypassRules::RunTest(const FString& Parameters)
{
	const FChunkLayout Good = ChunkLayouts::Get(5, 'A');
	TestTrue(TEXT("authored bypass passes"), ChunkLayouts::ValidateBypass(Good).IsEmpty());
	for (const FChunkVariant& V : LevelCatalogue::All())
	{
		const FChunkLayout L = ChunkLayouts::Get(V.Chunk, V.Variant);
		for (const FChunkPiece* B : L.Bypass())
		{
			TestTrue(*FString::Printf(TEXT("%s bypass is a transfer, not the whole chunk"), *V.Label()), B->Rect.GetSize().X <= ChunkLayoutConst::MaxBypassLength);
		}
	}
	auto WithBypass = [&Good](const FBox2D& Rect, EWindRole Role)
	{
		FChunkLayout L = Good;
		L.Pieces.RemoveAll([](const FChunkPiece& P) { return P.bBypass; });
		FChunkPiece B;
		B.Kind = EChunkPieceKind::Wind;
		B.Role = Role;
		B.Direction = Role == EWindRole::Descent ? FVector2D(0.0, -1.0) : FVector2D(1.0, 0.0);
		B.bBypass = true;
		B.Rect = Rect;
		L.Pieces.Add(B);
		return L;
	};
	FChunkLayout None = Good;
	None.Pieces.RemoveAll([](const FChunkPiece& P) { return P.bBypass; });
	TestFalse(TEXT("missing bypass is caught"), ChunkLayouts::ValidateBypass(None).IsEmpty());
	TestFalse(TEXT("a straight skip of the whole chunk is caught"),
		ChunkLayouts::ValidateBypass(WithBypass(FBox2D(FVector2D(0.0, 0.40), FVector2D(1.0, 0.52)), EWindRole::Transport)).IsEmpty());
	const FBox2D Rotor = ChunkLayouts::HazardRect(*Good.Of(EChunkPieceKind::Trap)[0]);
	TestFalse(TEXT("a bypass through the rotor is caught"),
		ChunkLayouts::ValidateBypass(WithBypass(FBox2D(FVector2D(0.45, Rotor.Min.Y), FVector2D(0.82, Rotor.Max.Y)), EWindRole::Transport)).IsEmpty());
	TestFalse(TEXT("a bypass that never rejoins N is caught"),
		ChunkLayouts::ValidateBypass(WithBypass(FBox2D(FVector2D(0.10, 0.88), FVector2D(0.40, 0.95)), EWindRole::Transport)).IsEmpty());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FChunkPlanPlacesLayouts, "UmbrellaElla.Level.PlanPlacesChunkLayouts", UMBRELLAELLA_CHUNK_TEST_FLAGS)
bool FChunkPlanPlacesLayouts::RunTest(const FString& Parameters)
{
	const FRoute Route = LevelCatalogue::Generate(1002);
	const TArray<FLevelPlacement> Plan = LevelPlan::Build(Route);
	for (int32 Slot = 0; Slot < Route.Slots.Num(); ++Slot)
	{
		const FChunkLayout L = ChunkLayouts::Get(Route.Slots[Slot].Chunk, Route.Slots[Slot].Variant);
		int32 Winds = 0;
		int32 Returns = 0;
		int32 Pieces = 0;
		for (const FLevelPlacement& P : Plan)
		{
			if (P.Slot != Slot || P.Kind == ELevelPlacementKind::Floor || P.Kind == ELevelPlacementKind::Refuge || P.Kind == ELevelPlacementKind::Checkpoint)
			{
				continue;
			}
			++Pieces;
			Winds += P.Kind == ELevelPlacementKind::Wind;
			Returns += P.Kind == ELevelPlacementKind::Wind && P.WindRole == EWindRole::Return;
			TestEqual(TEXT("gameplay pieces sit in Ella's plane"), static_cast<float>(P.Location.Y), UmbrellaDrawOrder::EllaY);
			TestTrue(TEXT("piece inside its chunk"), P.Location.X >= LevelCatalogue::SlotStartX(Slot) && P.Location.X <= LevelCatalogue::SlotStartX(Slot) + LevelCatalogue::SlotStartX(1));
		}
		TestEqual(*FString::Printf(TEXT("slot %d places its variant's pieces"), Slot + 1), Pieces, L.Pieces.Num());
		TestEqual(TEXT("slot winds match the layout"), Winds, L.Of(EChunkPieceKind::Wind).Num());
		TestTrue(TEXT("slot has a return current"), Returns >= 1);
	}
	int32 Yellow = 0;
	int32 Enemies = 0;
	for (const FLevelPlacement& P : Plan)
	{
		Enemies += P.Kind == ELevelPlacementKind::Enemy;
		Yellow += P.Kind == ELevelPlacementKind::Enemy && P.bYellowShot;
	}
	TestTrue(TEXT("route has enemies"), Enemies > 0);
	TestTrue(TEXT("route has yellow opportunities"), Yellow >= 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelSeedFixtures, "UmbrellaElla.Level.SeedFixtures1001To1003", UMBRELLAELLA_CHUNK_TEST_FLAGS)
bool FLevelSeedFixtures::RunTest(const FString& Parameters)
{
	// Seeds 1001-1003 run the generator; the GDD routes are illustrative proposals, not expected output.
	for (const int64 Seed : {1001LL, 1002LL, 1003LL})
	{
		const FRoute Route = LevelCatalogue::Generate(Seed);
		TestFalse(TEXT("generator found a route, not the fallback"), Route.bFromFallback);
		TestTrue(TEXT("route passes the route gate"), LevelCatalogue::ValidateRoute(Route).IsEmpty());
		TestEqual(TEXT("same seed, same route"), LevelCatalogue::Generate(Seed).Signature(), Route.Signature());
		for (const FChunkVariant& V : Route.Slots)
		{
			const FChunkLayout L = ChunkLayouts::Get(V.Chunk, V.Variant);
			TestTrue(*FString::Printf(TEXT("seed %lld %s has a valid authored layout"), Seed, *V.Label()),
				ChunkLayouts::Validate(L).IsEmpty() && ChunkLayouts::ValidateBypass(L).IsEmpty());
		}
		const FRoute Next = LevelCatalogue::GenerateAvoiding(Seed, Route.Signature());
		TestNotEqual(TEXT("a new run avoids repeating the route"), Next.Signature(), Route.Signature());
	}
	return true;
}

#endif
