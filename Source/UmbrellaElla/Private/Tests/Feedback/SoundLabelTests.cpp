#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Feedback/Audio/SoundLabelBoard.h"
#include "Feedback/Audio/SoundLabelHud.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Misc/FileHelper.h"
#include "Misc/OutputDevice.h"
#include "Misc/Paths.h"

#if UMBRELLAELLA_WORKBENCH

namespace
{
	/** Collects every log line while alive. */
	class FSoundLabelLogCapture final : public FOutputDevice
	{
	public:
		FSoundLabelLogCapture() { GLog->AddOutputDevice(this); }
		virtual ~FSoundLabelLogCapture() override { GLog->RemoveOutputDevice(this); }
		virtual void Serialize(const TCHAR* Text, ELogVerbosity::Type, const FName&) override { Lines.Add(Text); }
		bool HasLine(const FString& Wanted) const
		{
			GLog->FlushThreadedLogs();
			return Lines.ContainsByPredicate([&Wanted](const FString& Line) { return Line.Contains(Wanted); });
		}
		TArray<FString> Lines;
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSoundLabelFormats, "UmbrellaElla.SoundLabel.LinesAndTakeNumbers",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FSoundLabelFormats::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("log line"), FUmbrellaSoundLabelBoard::FormatLogLine(TEXT("WandBolt"), TEXT("ProjectileSpawned"), 2),
		FString(TEXT("SOUND_LABEL id=WandBolt event=ProjectileSpawned take=02")));
	FUmbrellaSoundLabel Label;
	Label.Id = TEXT("HitWing");
	Label.Event = TEXT("BossTargetHit");
	Label.Take = 1;
	TestEqual(TEXT("screen line"), FUmbrellaSoundLabelBoard::FormatScreenLine(Label), FString(TEXT("HitWing | BossTargetHit | take 01")));
	TestEqual(TEXT("take from asset name"), FUmbrellaSoundLabelBoard::TakeFromAssetName(TEXT("SW_WandBolt_02")), 2);
	TestEqual(TEXT("no suffix is take 0"), FUmbrellaSoundLabelBoard::TakeFromAssetName(TEXT("Shot")), 0);
	TestEqual(TEXT("fresh line is opaque"), FUmbrellaSoundLabelBoard::OpacityForAge(0.0f), 1.0f);
	TestEqual(TEXT("expired line is clear"), FUmbrellaSoundLabelBoard::OpacityForAge(UmbrellaSoundLabel::LineLifetimeSeconds), 0.0f);
	const float Mid = UmbrellaSoundLabel::LineLifetimeSeconds - UmbrellaSoundLabel::LineFadeSeconds * 0.5f;
	TestEqual(TEXT("half way through the fade"), FUmbrellaSoundLabelBoard::OpacityForAge(Mid), 0.5f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSoundLabelBoardRules, "UmbrellaElla.SoundLabel.ToggleFadeAndLimit",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FSoundLabelBoardRules::RunTest(const FString& Parameters)
{
	FSoundLabelLogCapture Capture;
	FUmbrellaSoundLabelBoard Board;
	TestFalse(TEXT("off by default"), Board.IsShown());
	Board.Note(TEXT("WandBolt"), TEXT("ProjectileSpawned"), 1);
	TestEqual(TEXT("a note adds a line"), Board.GetLabelCount(), 1);
	TestEqual(TEXT("hidden shows nothing"), Board.GetVisibleLabels().Num(), 0);
	TestTrue(TEXT("the log line is written even while hidden"), Capture.HasLine(TEXT("SOUND_LABEL id=WandBolt event=ProjectileSpawned take=01")));
	Board.Toggle();
	TestEqual(TEXT("shown lists the line"), Board.GetVisibleLabels().Num(), 1);
	Board.Toggle();
	TestEqual(TEXT("toggled off hides it"), Board.GetVisibleLabels().Num(), 0);
	Board.Toggle();
	Board.Advance(UmbrellaSoundLabel::LineLifetimeSeconds * 0.5f);
	TestEqual(TEXT("still there at half life"), Board.GetVisibleLabels().Num(), 1);
	Board.Advance(UmbrellaSoundLabel::LineLifetimeSeconds);
	TestEqual(TEXT("gone after the lifetime"), Board.GetLabelCount(), 0);
	for (int32 Index = 0; Index < UmbrellaSoundLabel::MaxLines + 3; ++Index)
	{
		Board.Note(FName(*FString::Printf(TEXT("S%d"), Index)), TEXT("Direct"), 0);
	}
	TestEqual(TEXT("the list is capped"), Board.GetVisibleLabels().Num(), UmbrellaSoundLabel::MaxLines);
	TestEqual(TEXT("the oldest drops first"), Board.GetVisibleLabels()[0].Id, FName(TEXT("S3")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSoundLabelHudKey, "UmbrellaElla.SoundLabel.ToggleKeyIsF9AndNeedsAPlayer",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FSoundLabelHudKey::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("F9"), FUmbrellaSoundLabelHud::GetToggleKey(), FKey(EKeys::F9));
	FUmbrellaSoundLabelHud Hud(MakeShared<FUmbrellaSoundLabelBoard>());
	Hud.Connect(nullptr);
	TestFalse(TEXT("no world, no attach"), Hud.IsAttached());
	TestFalse(TEXT("not attached"), Hud.IsAttached());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSoundLabelViewOrigin, "UmbrellaElla.SoundLabel.ListSitsInsideThe16By9View",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FSoundLabelViewOrigin::RunTest(const FString& Parameters)
{
	const FVector2D Exact = UmbrellaSoundLabel::ViewOrigin(FVector2D(1920.0, 1080.0));
	TestEqual(TEXT("16:9 viewport, no offset"), Exact.X + Exact.Y, 0.0, 0.01);
	TestTrue(TEXT("viewport wider than 16:9: bars at the sides"), UmbrellaSoundLabel::ViewOrigin(FVector2D(2000.0, 900.0)).X > 0.0);
	TestEqual(TEXT("side bar is half the spare width"), UmbrellaSoundLabel::ViewOrigin(FVector2D(2000.0, 900.0)).X, (2000.0 - 1600.0) * 0.5, 0.01);
	TestEqual(TEXT("tall viewport: bar at the top"), UmbrellaSoundLabel::ViewOrigin(FVector2D(1600.0, 1000.0)).Y, (1000.0 - 900.0) * 0.5, 0.01);
	TestEqual(TEXT("empty viewport"), UmbrellaSoundLabel::ViewOrigin(FVector2D::ZeroVector).X, 0.0, 0.01);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSoundLabelCuePlay, "UmbrellaElla.SoundLabel.World.PlayingACueAddsALabelAndALogLine",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FSoundLabelCuePlay::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UUmbrellaCueSubsystem* Cues = World->GetSubsystem<UUmbrellaCueSubsystem>();
	if (TestNotNull(TEXT("cue subsystem"), Cues))
	{
		const TSharedPtr<FUmbrellaSoundLabelBoard> Board = Cues->GetSoundLabelBoard();
		if (TestTrue(TEXT("the workbench build has a board"), Board.IsValid()))
		{
			FSoundLabelLogCapture Capture;
			TestFalse(TEXT("off by default"), Board->IsShown());
			// A real take when one is imported; otherwise the hook seam both play paths call.
			const FName Id(TEXT("WandBolt"));
			if (Cues->CanPlaySound(Id))
			{
				Cues->PlaySoundById(Id);
			}
			else
			{
				Cues->NoteSoundLabel(Id, 0);
			}
			TestEqual(TEXT("one label"), Board->GetLabelCount(), 1);
			TestTrue(TEXT("the log line"), Capture.HasLine(TEXT("SOUND_LABEL id=WandBolt event=Direct take=")));
			Board->Toggle();
			TestEqual(TEXT("shown"), Board->GetVisibleLabels().Num(), 1);
			Board->Toggle();
			TestEqual(TEXT("the toggle hides it"), Board->GetVisibleLabels().Num(), 0);

			if (Cues->CanPlaySound(Id))
			{
				UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(Cues);
				if (TestNotNull(TEXT("bus"), Bus))
				{
					FUmbrellaEvent Event;
					Event.Type = EUmbrellaEventType::ProjectileSpawned;
					Event.Detail = TEXT("PlayerBlast");
					Bus->Broadcast(Event);
					TestTrue(TEXT("a bus event names its event in the log"), Capture.HasLine(TEXT("SOUND_LABEL id=WandBolt event=ProjectileSpawned")));
				}
			}
		}
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif // UMBRELLAELLA_WORKBENCH

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSoundLabelCompiledOut, "UmbrellaElla.SoundLabel.EveryFileIsGuardedByTheWorkbenchSwitch",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FSoundLabelCompiledOut::RunTest(const FString& Parameters)
{
	// With UMBRELLAELLA_WORKBENCH=0 nothing of the labels is built: each file's body sits in exactly that #if.
	const TCHAR* Files[] = {
		TEXT("Source/UmbrellaElla/Public/Feedback/Audio/SoundLabelBoard.h"),
		TEXT("Source/UmbrellaElla/Public/Feedback/Audio/SoundLabelHud.h"),
		TEXT("Source/UmbrellaElla/Private/Feedback/Audio/SoundLabelBoard.cpp"),
		TEXT("Source/UmbrellaElla/Private/Feedback/Audio/SoundLabelHud.cpp"),
	};
	for (const TCHAR* Relative : Files)
	{
		FString Text;
		if (!FFileHelper::LoadFileToString(Text, *FPaths::Combine(FPaths::ProjectDir(), Relative)))
		{
			AddWarning(FString::Printf(TEXT("%s not found next to the project; the python check covers it"), Relative));
			continue;
		}
		TArray<FString> Lines;
		Text.ParseIntoArrayLines(Lines);
		int32 Opens = 0;
		FString FirstGuard;
		int32 Depth = 0;
		for (const FString& Raw : Lines)
		{
			const FString Line = Raw.TrimStartAndEnd();
			if (Line.StartsWith(TEXT("#if")))
			{
				if (Depth == 0)
				{
					FirstGuard = Line;
				}
				++Depth;
			}
			else if (Line.StartsWith(TEXT("#endif")))
			{
				--Depth;
			}
			else if (Depth == 0 && !Line.IsEmpty() && !Line.StartsWith(TEXT("#include")) && !Line.StartsWith(TEXT("#pragma"))
				&& !Line.StartsWith(TEXT("//")) && !Line.StartsWith(TEXT("/*")) && !Line.StartsWith(TEXT("*")))
			{
				++Opens;
			}
		}
		TestEqual(*FString::Printf(TEXT("%s: top-level guard"), Relative), FirstGuard, FString(TEXT("#if UMBRELLAELLA_WORKBENCH")));
		TestEqual(*FString::Printf(TEXT("%s: no code outside the guard"), Relative), Opens, 0);
	}
	return true;
}

#endif // WITH_AUTOMATION_TESTS
