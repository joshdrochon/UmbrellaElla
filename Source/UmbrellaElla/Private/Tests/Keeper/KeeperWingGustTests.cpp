#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Anim/KeeperPresenterSubsystem.h"
#include "Feedback/Art/ArtSlot.h"
#include "Feedback/Vfx/UmbrellaVfxDirectorSubsystem.h"
#include "Feedback/Vfx/VfxCatalog.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/AutomationTest.h"
#include "Owl/KeeperOfTime.h"

// Wing-gust cue (OWL-15: wing gather / load, then flap, readable direction and front; GDD line 333: warning 1.1 s, band
// width 120; line 375: the gust's own animation and VFX, cleared when the wings are disabled).

namespace
{
	constexpr EAutomationTestFlags WingGustFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter;
	constexpr float WingGustDt = 1.0f / 120.0f;

	/** A model with the talon off (the gust is then the wing phase's only physical move), anchored at the origin. */
	void WingGustModel(FKeeperFightModel& Model, TArray<FKeeperCommand>& Commands)
	{
		const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
		FKeeperRuleSwitches Switches;
		Switches.bTalon = false;
		Model.Init(Tuning->Keeper, Tuning->Encounter, Switches);
		Model.SetAnchor(FVector2D::ZeroVector);
		Model.BeginPhase(EKeeperPhase::Wings, Commands);
	}

	FKeeperTickInput WingGustInput()
	{
		FKeeperTickInput Input;
		Input.PlayerPos = FVector2D(-600.0f, 40.0f);
		Input.PlayerRadius = 10.0f;
		return Input;
	}

	/** Step until the gust warning starts (true) or 20 s pass; the warning command lands in OutWarning. */
	bool StepToGustWarning(FKeeperFightModel& Model, TArray<FKeeperCommand>& Commands, FKeeperCommand& OutWarning)
	{
		const FKeeperTickInput Input = WingGustInput();
		for (float T = 0.0f; T < 20.0f; T += WingGustDt)
		{
			Commands.Reset();
			Model.Step(WingGustDt, Input, Commands);
			for (const FKeeperCommand& Command : Commands)
			{
				if (Command.Type == EKeeperCommandType::PhysicalWarning && Command.Physical == EKeeperPhysical::Gust)
				{
					OutWarning = Command;
					return true;
				}
			}
		}
		return false;
	}

	UWorld* WingGustWorld()
	{
		UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
		if (World)
		{
			GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
		}
		return World;
	}

	void WingGustEnd(UWorld* World)
	{
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}

	FLinearColor TintOf(const UStaticMeshComponent* Mesh)
	{
		FLinearColor Out = FLinearColor::Transparent;
		if (const UMaterialInstanceDynamic* Dynamic = Mesh ? Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)) : nullptr)
		{
			Dynamic->GetVectorParameterValue(FName(TEXT("Tint")), Out);
		}
		return Out;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWingGustTiming, "UmbrellaElla.Keeper.WingGust.CueFollowsTheWarning", WingGustFlags)

bool FKeeperWingGustTiming::RunTest(const FString& Parameters)
{
	const FKeeperTuning& T = GetDefault<UUmbrellaTuning>()->Keeper;
	// Timing unchanged (GDD line 333).
	TestEqual(TEXT("gust warning stays 1.1 s"), T.GustWarningSeconds, 1.1f, 1e-4f);
	TestEqual(TEXT("gust band stays 120 wide"), T.GustBandWidth, 120.0f, 1e-4f);

	const float W = T.GustWarningSeconds;
	auto Warn = [&](float Elapsed) { return AKeeperOfTime::WingGustCellFor(EKeeperPhysical::Gust, EKeeperStage::Warning, W - Elapsed, true, T); };
	auto Travel = [&](float Elapsed) { return AKeeperOfTime::WingGustCellFor(EKeeperPhysical::Gust, EKeeperStage::Stroke, T.GustLifetimeSeconds - Elapsed, true, T); };
	TestEqual(TEXT("warning starts on the first gather cell"), Warn(0.0f), 0);
	TestEqual(TEXT("last gather cell just before the flap"), Warn(W * KeeperWingGustConst::GatherShare - 0.01f), KeeperWingGustConst::GatherCells - 1);
	TestEqual(TEXT("flap starts at the gather share"), Warn(W * KeeperWingGustConst::GatherShare + 0.001f), KeeperWingGustConst::GatherCells);
	int32 Last = -1;
	for (float E = 0.0f; E < W; E += 0.01f)
	{
		const int32 Cell = Warn(E);
		TestTrue(*FString::Printf(TEXT("cells never step back in the warning (%.2f s)"), E), Cell >= Last);
		Last = Cell;
	}
	TestTrue(TEXT("the warning ends inside the flap"), Last >= KeeperWingGustConst::GatherCells && Last < KeeperWingGustConst::GatherCells + KeeperWingGustConst::FlapCells);
	TestTrue(TEXT("the launch is still the flap"), Travel(0.0f) >= KeeperWingGustConst::GatherCells && Travel(0.0f) < KeeperWingGustConst::GatherCells + KeeperWingGustConst::FlapCells);
	TestTrue(TEXT("launch does not step back from the warning's end"), Travel(0.0f) >= Last);
	TestEqual(TEXT("flap ends on its last cell"), Travel(KeeperWingGustConst::FlapAfterLaunchSeconds - 0.001f), KeeperWingGustConst::GatherCells + KeeperWingGustConst::FlapCells - 1);
	TestEqual(TEXT("recover after the flap"), Travel(KeeperWingGustConst::FlapAfterLaunchSeconds + 0.001f), KeeperWingGustConst::GatherCells + KeeperWingGustConst::FlapCells);
	TestEqual(TEXT("last recover cell"), Travel(KeeperWingGustConst::FlapAfterLaunchSeconds + KeeperWingGustConst::RecoverSeconds - 0.001f), KeeperWingGustConst::Cells - 1);
	TestEqual(TEXT("idle again while the gust still travels"), Travel(KeeperWingGustConst::FlapAfterLaunchSeconds + KeeperWingGustConst::RecoverSeconds + 0.01f), INDEX_NONE);
	TestEqual(TEXT("no cue with the wings disabled"), AKeeperOfTime::WingGustCellFor(EKeeperPhysical::Gust, EKeeperStage::Warning, W * 0.5f, false, T), INDEX_NONE);
	TestEqual(TEXT("no cue for the talon"), AKeeperOfTime::WingGustCellFor(EKeeperPhysical::Talon, EKeeperStage::Warning, 0.5f, true, T), INDEX_NONE);
	TestEqual(TEXT("no cue in recovery"), AKeeperOfTime::WingGustCellFor(EKeeperPhysical::Gust, EKeeperStage::Recovery, 0.5f, true, T), INDEX_NONE);

	// The model's own warning: the cue spans exactly the warning the rules run (1.1 s), gather first, flap at launch.
	FKeeperFightModel Model;
	TArray<FKeeperCommand> Commands;
	FKeeperCommand Warning;
	WingGustModel(Model, Commands);
	if (!TestTrue(TEXT("the model starts a gust warning"), StepToGustWarning(Model, Commands, Warning)))
	{
		return false;
	}
	const FKeeperTickInput Input = WingGustInput();
	float WarningSeconds = 0.0f;
	bool bSawGather = false;
	while (Model.GetStage() == EKeeperStage::Warning && WarningSeconds < 5.0f)
	{
		const int32 Cell = AKeeperOfTime::WingGustCellFor(Model.GetPhysical(), Model.GetStage(), Model.GetStageRemaining(), true, T);
		bSawGather |= Cell >= 0 && Cell < KeeperWingGustConst::GatherCells;
		Model.Step(WingGustDt, Input, Commands);
		WarningSeconds += WingGustDt;
	}
	TestEqual(TEXT("model warning lasts 1.1 s"), WarningSeconds, T.GustWarningSeconds, 2.0f * WingGustDt);
	TestTrue(TEXT("the wings gather during the warning"), bSawGather);
	TestTrue(TEXT("gust launches"), Model.IsGustTravelling());
	const int32 LaunchCell = AKeeperOfTime::WingGustCellFor(Model.GetPhysical(), Model.GetStage(), Model.GetStageRemaining(), true, T);
	TestTrue(TEXT("the flap lands on the launch"), LaunchCell >= KeeperWingGustConst::GatherCells && LaunchCell < KeeperWingGustConst::GatherCells + KeeperWingGustConst::FlapCells);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWingGustStrokes, "UmbrellaElla.Keeper.WingGust.RibbonsShowDirectionAndFront", WingGustFlags)

bool FKeeperWingGustStrokes::RunTest(const FString& Parameters)
{
	const FKeeperTuning& T = GetDefault<UUmbrellaTuning>()->Keeper;
	const FVector2D Start(400.0f, 150.0f);
	const float Lane = T.GustSpeed * T.GustLifetimeSeconds;
	const float Half = T.GustBandWidth * 0.5f;
	TArray<FKeeperGustStroke> Strokes;
	auto InBand = [&](const TArray<FKeeperGustStroke>& S, float MaxX, const TCHAR* What)
	{
		for (const FKeeperGustStroke& Stroke : S)
		{
			for (const FVector2D& P : {Stroke.A, Stroke.B})
			{
				if (FMath::Abs(P.Y - Start.Y) > Half || P.X > MaxX + 0.01f || P.X < Start.X - Lane - 0.01f)
				{
					AddError(FString::Printf(TEXT("%s: point (%.1f, %.1f) outside the 120-wide lane"), What, P.X, P.Y));
					return;
				}
			}
		}
	};
	auto MinX = [](const TArray<FKeeperGustStroke>& S)
	{
		float X = TNumericLimits<float>::Max();
		for (const FKeeperGustStroke& Stroke : S)
		{
			X = FMath::Min(X, static_cast<float>(FMath::Min(Stroke.A.X, Stroke.B.X)));
		}
		return X;
	};
	// Each ribbon is a run of strokes going +X; its first stroke is the head (thick), its last the tail (thin).
	auto CheckRibbons = [&](const TArray<FKeeperGustStroke>& S, const TCHAR* What)
	{
		int32 Ribbons = 0;
		int32 First = 0;
		for (int32 Index = 1; Index <= S.Num(); ++Index)
		{
			if (Index == S.Num() || S[Index].A.X < S[Index - 1].B.X - 0.01f)
			{
				++Ribbons;
				const FKeeperGustStroke& Head = S[First];
				const FKeeperGustStroke& Tail = S[Index - 1];
				TestTrue(*FString::Printf(TEXT("%s ribbon %d: head leads toward -X"), What, Ribbons), Head.A.X < Tail.B.X);
				float Thickest = 0.0f;
				int32 ThickestAt = First;
				for (int32 K = First; K < Index; ++K)
				{
					ThickestAt = S[K].Thick > Thickest ? K : ThickestAt;
					Thickest = FMath::Max(Thickest, S[K].Thick);
				}
				TestTrue(*FString::Printf(TEXT("%s ribbon %d: thickest in its front third"), What, Ribbons), ThickestAt - First <= (Index - First) / 3);
				TestTrue(*FString::Printf(TEXT("%s ribbon %d: tapers to a thin tail"), What, Ribbons), Tail.Thick < Thickest * 0.5f);
				float MinY = TNumericLimits<float>::Max();
				float MaxY = -TNumericLimits<float>::Max();
				for (int32 K = First; K < Index; ++K)
				{
					MinY = FMath::Min(MinY, static_cast<float>(S[K].A.Y));
					MaxY = FMath::Max(MaxY, static_cast<float>(S[K].A.Y));
				}
				TestTrue(*FString::Printf(TEXT("%s ribbon %d: wavy, not a ruled line"), What, Ribbons), MaxY - MinY > 5.0f);
				First = Index;
			}
		}
		return Ribbons;
	};

	AKeeperOfTime::GustStrokes(Start, Lane, T.GustBandWidth, false, 0.0f, 0.0f, T.GustFrontThickness, 0.0f, Strokes);
	TestEqual(TEXT("nothing drawn at the warning's first instant"), Strokes.Num(), 0);
	AKeeperOfTime::GustStrokes(Start, Lane, T.GustBandWidth, false, 0.25f, 0.0f, T.GustFrontThickness, 0.3f, Strokes);
	const float ReachEarly = static_cast<float>(Start.X) - MinX(Strokes);
	InBand(Strokes, Start.X, TEXT("warning 0.25"));
	AKeeperOfTime::GustStrokes(Start, Lane, T.GustBandWidth, false, 0.75f, 0.0f, T.GustFrontThickness, 0.8f, Strokes);
	const float ReachLate = static_cast<float>(Start.X) - MinX(Strokes);
	InBand(Strokes, Start.X, TEXT("warning 0.75"));
	TestEqual(TEXT("warning ribbons"), CheckRibbons(Strokes, TEXT("warning")), KeeperWingGustConst::WarningRibbons);
	TestTrue(TEXT("the warning lane draws out toward -X (the gust's direction)"), ReachLate > ReachEarly && ReachEarly > 0.0f);
	AKeeperOfTime::GustStrokes(Start, Lane, T.GustBandWidth, false, 1.0f, 0.0f, T.GustFrontThickness, 1.1f, Strokes);
	TestEqual(TEXT("at the launch the lane covers its full length"), static_cast<float>(Start.X) - MinX(Strokes), Lane, 0.5f);
	TestTrue(TEXT("pool holds a warning frame"), Strokes.Num() <= KeeperWingGustConst::PoolSize);

	// Travelling: ribbon heads at the hit front's leading edge, thick, tails trailing +X.
	const float FrontX = Start.X - 500.0f;
	AKeeperOfTime::GustStrokes(Start, Lane, T.GustBandWidth, true, 1.0f, FrontX, T.GustFrontThickness, 2.0f, Strokes);
	InBand(Strokes, FrontX + KeeperWingGustConst::TravelLength, TEXT("travel"));
	TestEqual(TEXT("travel ribbons"), CheckRibbons(Strokes, TEXT("travel")), KeeperWingGustConst::TravelRibbons);
	TestTrue(TEXT("pool holds a travel frame"), Strokes.Num() <= KeeperWingGustConst::PoolSize);
	TestEqual(TEXT("front at the hit front's leading edge"), MinX(Strokes), FrontX - T.GustFrontThickness * 0.5f, 0.01f);
	float Thickest = 0.0f;
	for (const FKeeperGustStroke& Stroke : Strokes)
	{
		Thickest = FMath::Max(Thickest, Stroke.Thick);
	}
	TestTrue(TEXT("the travelling gust is heavier than the warning lane"), Thickest > KeeperWingGustConst::WarningThick);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWingGustWorld, "UmbrellaElla.Keeper.WingGust.WarningDrawsRibbonsNotABox", WingGustFlags)

bool FKeeperWingGustWorld::RunTest(const FString& Parameters)
{
	UWorld* World = WingGustWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	AKeeperOfTime* Keeper = World->SpawnActor<AKeeperOfTime>();
	if (TestNotNull(TEXT("keeper"), Keeper))
	{
		if (!Keeper->HasActorBegunPlay())
		{
			Keeper->DispatchBeginPlay();
		}
		const UStaticMeshComponent* Telegraph = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("TelegraphVisual")));
		const UStaticMeshComponent* GustCube = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("GustVisual")));
		FKeeperFightModel Model;
		TArray<FKeeperCommand> Commands;
		FKeeperCommand Warning;
		WingGustModel(Model, Commands);
		if (TestTrue(TEXT("gust warning"), StepToGustWarning(Model, Commands, Warning)))
		{
			Keeper->ShowTelegraph(Warning);
			const FKeeperTickInput Input = WingGustInput();
			for (int32 Step = 0; Step < 40; ++Step)
			{
				Model.Step(WingGustDt, Input, Commands);
			}
			Keeper->Refresh(Model, 0.4f);
			TestEqual(TEXT("still warning"), Model.GetStage(), EKeeperStage::Warning);
			TestTrue(TEXT("warning draws gust ribbons"), Keeper->GetVisibleGustRibbonCount() > 0);
			TestFalse(TEXT("no flat telegraph box for the gust"), Telegraph && Telegraph->IsVisible());
			TestFalse(TEXT("no flat gust cube"), GustCube && GustCube->IsVisible());
			TestTrue(TEXT("wing cue gathers"), Keeper->GetWingGustCell() >= 0 && Keeper->GetWingGustCell() < KeeperWingGustConst::GatherCells);
			if (Keeper->GetGustRibbons().Num() > 0)
			{
				const FLinearColor Expected = FLinearColor::FromSRGBColor(FColor(0x55, 0x5E, 0x60));
				const FLinearColor Tint = TintOf(Keeper->GetGustRibbons()[0]);
				TestTrue(TEXT("ribbons are ash blue #555e60"), Tint.Equals(Expected, 0.01f));
			}
			while (Model.GetStage() == EKeeperStage::Warning)
			{
				Model.Step(WingGustDt, Input, Commands);
			}
			Keeper->Refresh(Model, 1.2f);
			TestTrue(TEXT("travelling gust draws ribbons"), Model.IsGustTravelling() && Keeper->GetVisibleGustRibbonCount() > KeeperWingGustConst::TravelRibbons);
			TestFalse(TEXT("travelling gust: no flat cube"), GustCube && GustCube->IsVisible());

			// Wings disabled mid-gust: the model clears the gust; ribbons and the wing cue clear with it (GDD line 375).
			Commands.Reset();
			Model.ApplyPlayerHit(EKeeperPart::Wings, 100000.0f, Commands);
			TestTrue(TEXT("model: wings broken"), Model.IsPartBroken(EKeeperPart::Wings));
			for (const FKeeperCommand& Command : Commands)
			{
				if (Command.Type == EKeeperCommandType::ClearGusts)
				{
					Keeper->ClearGusts();
				}
			}
			Keeper->Refresh(Model, 1.3f);
			TestEqual(TEXT("no ribbons once the wings are disabled"), Keeper->GetVisibleGustRibbonCount(), 0);
			TestEqual(TEXT("no wing cue once the wings are disabled"), Keeper->GetWingGustCell(), INDEX_NONE);
		}
	}
	WingGustEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWingGustLayer, "UmbrellaElla.Feedback.World.KeeperWingGustPlaysOverBody", WingGustFlags)

bool FKeeperWingGustLayer::RunTest(const FString& Parameters)
{
	// Placement: the clip's owl lands on the idle owl (crop vs idle box, clip pixels -> body units).
	FVector Box;
	FVector Offset;
	UKeeperPresenterSubsystem::WingGustPlacement(FVector(6.0, 0.1, 6.0 * UmbrellaKeeperPresenterConst::WingGustIdleBoxH / UmbrellaKeeperPresenterConst::WingGustIdleBoxW), Box, Offset);
	const double UnitsPerPx = 600.0 / UmbrellaKeeperPresenterConst::WingGustIdleBoxW;
	TestEqual(TEXT("layer width = crop width in body units"), Box.X * 100.0, UmbrellaKeeperPresenterConst::WingGustCropW * UnitsPerPx, 0.01);
	TestEqual(TEXT("layer height = crop height in body units"), Box.Z * 100.0, UmbrellaKeeperPresenterConst::WingGustCropH * UnitsPerPx, 0.01);
	TestEqual(TEXT("layer centre X"), Offset.X, ((UmbrellaKeeperPresenterConst::WingGustCropX + UmbrellaKeeperPresenterConst::WingGustCropW * 0.5) - (UmbrellaKeeperPresenterConst::WingGustIdleBoxX + UmbrellaKeeperPresenterConst::WingGustIdleBoxW * 0.5)) * UnitsPerPx, 0.01);
	TestEqual(TEXT("layer centre Z (pixels down = units up)"), Offset.Z, -((UmbrellaKeeperPresenterConst::WingGustCropY + UmbrellaKeeperPresenterConst::WingGustCropH * 0.5) - (UmbrellaKeeperPresenterConst::WingGustIdleBoxY + UmbrellaKeeperPresenterConst::WingGustIdleBoxH * 0.5)) * UnitsPerPx, 0.01);

	UWorld* World = WingGustWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UKeeperPresenterSubsystem* Presenter = World->GetSubsystem<UKeeperPresenterSubsystem>();
	AKeeperOfTime* Keeper = World->SpawnActor<AKeeperOfTime>();
	if (TestNotNull(TEXT("presenter"), Presenter) && TestNotNull(TEXT("keeper"), Keeper))
	{
		if (!Keeper->HasActorBegunPlay())
		{
			Keeper->DispatchBeginPlay();
		}
		Presenter->ShowStandIn(Keeper);
		UStaticMeshComponent* Body = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("KeeperStandIn")));
		UTexture2D* Picture = UTexture2D::CreateTransient(28, 2);
		Picture->AddToRoot();
		if (Body && !ArtSlot::HasArt(Body))
		{
			Presenter->ShowArt(Keeper, Picture);
		}
		Presenter->ShowWingGustLayer(Keeper, Picture);
		UStaticMeshComponent* Layer = FindObjectFast<UStaticMeshComponent>(Keeper, FName(UmbrellaKeeperPresenterConst::WingGustLayerName));
		if (TestNotNull(TEXT("body"), Body) && TestNotNull(TEXT("wing-gust layer"), Layer))
		{
			TestFalse(TEXT("layer hidden at idle"), Layer->IsVisible());
			FKeeperFightModel Model;
			TArray<FKeeperCommand> Commands;
			FKeeperCommand Warning;
			WingGustModel(Model, Commands);
			if (TestTrue(TEXT("gust warning"), StepToGustWarning(Model, Commands, Warning)))
			{
				Keeper->ShowTelegraph(Warning);
				Keeper->Refresh(Model, 0.0f);
				Presenter->PlayWingGust(Keeper);
				TestTrue(TEXT("warning: the clip plays"), Layer->IsVisible());
				TestFalse(TEXT("warning: the idle body hides under it"), Body->IsVisible());
				float Frame = -1.0f;
				if (const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Layer->GetMaterial(0)))
				{
					Dynamic->GetScalarParameterValue(FName(TEXT("Frame")), Frame);
				}
				TestEqual(TEXT("layer shows the Keeper's cue cell"), static_cast<int32>(Frame), Keeper->GetWingGustCell());
				// Run past the flap and recovery: back to the idle body.
				const FKeeperTickInput Input = WingGustInput();
				const float Until = GetDefault<UUmbrellaTuning>()->Keeper.GustWarningSeconds + KeeperWingGustConst::FlapAfterLaunchSeconds + KeeperWingGustConst::RecoverSeconds + 0.1f;
				for (float T = 0.0f; T < Until; T += WingGustDt)
				{
					Model.Step(WingGustDt, Input, Commands);
				}
				Keeper->Refresh(Model, Until);
				Presenter->PlayWingGust(Keeper);
				TestFalse(TEXT("after recovery: the clip hides"), Layer->IsVisible());
				TestTrue(TEXT("after recovery: the idle body is back"), Body->IsVisible());
			}
		}
		Picture->RemoveFromRoot();
	}
	WingGustEnd(World);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWingGustClipPuff, "UmbrellaElla.Keeper.WingGust.NoRibbonBehindThePuff", WingGustFlags)

bool FKeeperWingGustClipPuff::RunTest(const FString& Parameters)
{
	// Josh 22:47: the grey ribbons behind the white gust plume look tacky. The plume sits on the gust front.
	const FKeeperTuning& T = GetDefault<UUmbrellaTuning>()->Keeper;
	const FVector2D Start(1400.0f, 600.0f);
	const FVector2D Front(Start.X - 500.0f, Start.Y);
	// The puff sprite's box (catalog large size, centred on the front) plus a clear margin of 25% of its width (Josh, Nov 14:
	// grey touching or starting at the white edge reads as part of the plume).
	const float PuffHalf = VfxCatalogData::LargeSize * 0.5f;
	const FVector2D Half = AKeeperOfTime::PuffClearHalf();
	TestTrue(TEXT("the clear box is at least the puff plus 25% of its width"), Half.X >= PuffHalf + 0.25f * VfxCatalogData::LargeSize - KINDA_SMALL_NUMBER);
	TArray<FKeeperGustStroke> Strokes;
	AKeeperOfTime::GustStrokes(Start, T.GustSpeed * T.GustLifetimeSeconds, T.GustBandWidth, true, 1.0f, Front.X, T.GustFrontThickness, 2.0f, Strokes);
	const int32 Before = Strokes.Num();
	AKeeperOfTime::ClipStrokesOutside(Front, Half, Strokes);
	TestTrue(TEXT("strokes behind the plume are dropped"), Strokes.Num() < Before);
	TestTrue(TEXT("the ribbons clearly further back toward the owl stay"), Strokes.Num() > 0);
	for (const FKeeperGustStroke& Stroke : Strokes)
	{
		const float Pad = Stroke.Thick * 0.5f;
		const bool bInside = FMath::Max(Stroke.A.X, Stroke.B.X) + Pad > Front.X - Half.X && FMath::Min(Stroke.A.X, Stroke.B.X) - Pad < Front.X + Half.X
			&& FMath::Max(Stroke.A.Y, Stroke.B.Y) + Pad > Front.Y - Half.Y && FMath::Min(Stroke.A.Y, Stroke.B.Y) - Pad < Front.Y + Half.Y;
		if (bInside)
		{
			AddError(FString::Printf(TEXT("a ribbon stroke (%.0f,%.0f)-(%.0f,%.0f) is within the clear margin of the plume"), Stroke.A.X, Stroke.A.Y, Stroke.B.X, Stroke.B.Y));
			break;
		}
	}

	// In a world: a live travelling-gust puff sprite. No drawn ribbon piece's bounds come within 25% of the puff's width of
	// the puff's drawn bounds; pieces further back toward the owl are still drawn.
	UWorld* World = WingGustWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	AKeeperOfTime* Keeper = World->SpawnActor<AKeeperOfTime>();
	UUmbrellaVfxDirectorSubsystem* Director = World->GetSubsystem<UUmbrellaVfxDirectorSubsystem>();
	if (TestNotNull(TEXT("keeper"), Keeper) && TestNotNull(TEXT("effect director"), Director))
	{
		if (!Keeper->HasActorBegunPlay())
		{
			Keeper->DispatchBeginPlay();
		}
		FKeeperFightModel Model;
		TArray<FKeeperCommand> Commands;
		FKeeperCommand Warning;
		WingGustModel(Model, Commands);
		if (TestTrue(TEXT("gust warning"), StepToGustWarning(Model, Commands, Warning)))
		{
			Keeper->ShowTelegraph(Warning);
			const FKeeperTickInput Input = WingGustInput();
			while (Model.GetStage() == EKeeperStage::Warning)
			{
				Model.Step(WingGustDt, Input, Commands);
			}
			for (int32 Step = 0; Step < 30; ++Step)
			{
				Model.Step(WingGustDt, Input, Commands);
			}
			TestTrue(TEXT("the gust travels"), Model.IsGustTravelling());
			// The drawn puff sits ahead of the front in the game (frame 01:03: sheet 828..949 px, ribbon heads ~973 px):
			// place it so its box covers the ribbon heads.
			const FVector2D At = Model.GetGustFront() + FVector2D(VfxCatalogData::LargeSize * 0.5f, 0.0f);
			Director->Play(TEXT("GustTravel"), FVector(At.X, 0.0f, At.Y), nullptr);
			const AActor* Puff = Director->GetLiveActor(TEXT("GustTravel"));
			const UPrimitiveComponent* PuffVisual = Puff ? Cast<UPrimitiveComponent>(Puff->GetRootComponent()) : nullptr;
			if (TestNotNull(TEXT("the travelling puff is drawn"), PuffVisual))
			{
				Keeper->Refresh(Model, 1.2f);
				const FBox PuffBox = PuffVisual->Bounds.GetBox();
				const FBox2D Clear = AKeeperOfTime::PuffClearBox(PuffBox);
				TestTrue(TEXT("clear box"), Clear.bIsValid);
				TestTrue(TEXT("the margin is 25% of the puff width"), FMath::IsNearlyEqual(static_cast<float>(Clear.GetExtent().X - PuffBox.GetExtent().X),
					KeeperWingGustConst::PuffClearShare * static_cast<float>(PuffBox.GetSize().X), 0.5f));
				int32 Drawn = 0;
				for (const TObjectPtr<UStaticMeshComponent>& Ribbon : Keeper->GetGustRibbons())
				{
					if (!Ribbon || !Ribbon->IsVisible())
					{
						continue;
					}
					++Drawn;
					const FBox R = Ribbon->Bounds.GetBox();
					const FBox2D R2(FVector2D(R.Min.X, R.Min.Z), FVector2D(R.Max.X, R.Max.Z));
					if (R2.Intersect(Clear))
					{
						AddError(FString::Printf(TEXT("ribbon %s (%.0f..%.0f, %.0f..%.0f) is within the puff's clear margin (%.0f..%.0f, %.0f..%.0f)"), *Ribbon->GetName(),
							R2.Min.X, R2.Max.X, R2.Min.Y, R2.Max.Y, Clear.Min.X, Clear.Max.X, Clear.Min.Y, Clear.Max.Y));
					}
				}
				TestTrue(TEXT("ribbon pieces further back toward the owl are still drawn"), Drawn > 0);
			}
			Director->StopAll();
		}
	}
	WingGustEnd(World);
	return true;
}
