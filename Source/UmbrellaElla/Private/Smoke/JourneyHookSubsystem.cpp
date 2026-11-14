#include "Smoke/JourneyHookSubsystem.h"
#include "Core/UmbrellaLog.h"
#include "Flow/FlowRules.h"

namespace JourneyRules
{
	TArray<FJourneyStep> ParseScript(const FString& Text, TArray<FString>& OutErrors)
	{
		static const TArray<FString> Known = { TEXT("wait"), TEXT("trywait"), TEXT("shot"), TEXT("key"), TEXT("hold"), TEXT("click"),
			TEXT("music"), TEXT("idle"), TEXT("hits"), TEXT("assistwin"), TEXT("retrycheck"), TEXT("log"), TEXT("end"), TEXT("firstrun"), TEXT("keyuntil"), TEXT("console"), TEXT("texts"), TEXT("route"), TEXT("routeassist"), TEXT("skipunless") };
		TArray<FJourneyStep> Out;
		TArray<FString> Lines;
		Text.ParseIntoArrayLines(Lines, false);
		for (int32 Index = 0; Index < Lines.Num(); ++Index)
		{
			FString Line = Lines[Index];
			int32 Hash = INDEX_NONE;
			if (Line.FindChar(TEXT('#'), Hash))
			{
				Line.LeftInline(Hash);
			}
			Line.TrimStartAndEndInline();
			if (Line.IsEmpty())
			{
				continue;
			}
			TArray<FString> Words;
			Line.ParseIntoArrayWS(Words);
			FJourneyStep Step;
			Step.Line = Index + 1;
			Step.Command = Words[0].ToLower();
			if (!Known.Contains(Step.Command))
			{
				OutErrors.Add(FString::Printf(TEXT("line %d: unknown command '%s'"), Step.Line, *Words[0]));
				continue;
			}
			// Trailing numeric words are the numbers; the words between the command and them are the argument.
			int32 FirstNumber = Words.Num();
			while (FirstNumber > 1 && Words[FirstNumber - 1].IsNumeric())
			{
				--FirstNumber;
			}
			TArray<FString> ArgWords;
			for (int32 W = 1; W < FirstNumber; ++W)
			{
				ArgWords.Add(Words[W]);
			}
			Step.Arg = FString::Join(ArgWords, TEXT(" "));
			for (int32 W = FirstNumber; W < Words.Num(); ++W)
			{
				Step.Numbers.Add(FCString::Atof(*Words[W]));
			}
			Out.Add(Step);
		}
		return Out;
	}

	bool HasScreenNamed(const FString& Word, uint8& OutScreen)
	{
		const UEnum* Enum = StaticEnum<EFlowScreen>();
		for (int32 Index = 0; Index < Enum->NumEnums() - 1; ++Index)
		{
			if (Enum->GetNameStringByIndex(Index).Equals(Word, ESearchCase::IgnoreCase))
			{
				OutScreen = static_cast<uint8>(Enum->GetValueByIndex(Index));
				return true;
			}
		}
		return false;
	}

	FString ScreenName(uint8 Screen)
	{
		return StaticEnum<EFlowScreen>()->GetNameStringByValue(Screen);
	}

	bool IsLabelMatch(const FString& Shown, const FString& Wanted)
	{
		return !Wanted.TrimStartAndEnd().IsEmpty() && Shown.TrimStartAndEnd().Equals(Wanted.TrimStartAndEnd(), ESearchCase::IgnoreCase);
	}

	EJourneyClickNext ClickNext(bool bScreenChanged, bool bButtonShown, double SecondsSinceLastPress, int32 Clicks)
	{
		if (bScreenChanged || !bButtonShown)
		{
			return EJourneyClickNext::Done;
		}
		if (SecondsSinceLastPress < ClickSettleSeconds)
		{
			return EJourneyClickNext::Wait;
		}
		if (Clicks < ClickMouseTries)
		{
			return EJourneyClickNext::ClickAgain;
		}
		return Clicks == ClickMouseTries ? EJourneyClickNext::PressAccept : EJourneyClickNext::Fail;
	}
}

#if UMBRELLAELLA_WORKBENCH

#include "Arena/UmbrellaArena.h"
#include "Attack/AttackEmitterComponent.h"
#include "Core/UmbrellaGameMode.h"
#include "Level/LevelPlan.h"
#include "Level/UmbrellaLevelDirector.h"
#include "Core/EllaCharacter.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Flow/UmbrellaPlayerController.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/FileManager.h"
#include "Health/UmbrellaHealthComponent.h"
#include "ImageUtils.h"
#include "UnrealClient.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "GameFramework/PlayerInput.h"
#include "Owl/KeeperOfTime.h"
#include "Owl/KeeperPartComponent.h"
#include "Sound/SoundBase.h"
#include "Components/AudioComponent.h"
#include "Widgets/SViewport.h"
#include "Widgets/SWindow.h"
#include "Widgets/Text/STextBlock.h"

bool UJourneyHookSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	return FString(FCommandLine::Get()).Contains(TEXT("-SmokeJourney="));
}

void UJourneyHookSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	FString ScriptPath;
	FParse::Value(FCommandLine::Get(), TEXT("-SmokeJourney="), ScriptPath);
	ScriptPath = ScriptPath.TrimQuotes();
	if (FPaths::IsRelative(ScriptPath))
	{
		ScriptPath = FPaths::Combine(FPaths::ProjectDir(), ScriptPath);
	}
	if (!FParse::Value(FCommandLine::Get(), TEXT("-SmokeJourneyOut="), OutDir))
	{
		OutDir = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Journey"));
	}
	OutDir = OutDir.TrimQuotes();
	if (FPaths::IsRelative(OutDir))
	{
		OutDir = FPaths::Combine(FPaths::ProjectDir(), OutDir);
	}
	OutDir = FPaths::ConvertRelativePathToFull(OutDir);
	IFileManager::Get().MakeDirectory(*OutDir, true);

	FString Text;
	TArray<FString> Errors;
	if (!FFileHelper::LoadFileToString(Text, *ScriptPath))
	{
		Errors.Add(FString::Printf(TEXT("no script at %s"), *ScriptPath));
	}
	Steps = JourneyRules::ParseScript(Text, Errors);
	Log(FString::Printf(TEXT("JOURNEY_BEGIN script=%s steps=%d out=%s"), *FPaths::GetCleanFilename(ScriptPath), Steps.Num(), *OutDir));
	if (Errors.Num() > 0)
	{
		EndJourney(TEXT("script: ") + FString::Join(Errors, TEXT("; ")));
	}
}

bool UJourneyHookSubsystem::IsTickable() const
{
	return !IsTemplate() && !(bEnded && EndedAt < 0.0);
}

TStatId UJourneyHookSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UJourneyHookSubsystem, STATGROUP_Tickables);
}

void UJourneyHookSubsystem::Log(const FString& Line)
{
	UE_LOG(LogUmbrellaElla, Display, TEXT("%s"), *Line);
	LogText += Line + LINE_TERMINATOR;
	FFileHelper::SaveStringToFile(LogText, *FPaths::Combine(OutDir, TEXT("journey.log")));
}

AUmbrellaPlayerController* UJourneyHookSubsystem::GetFlow() const
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	return World ? Cast<AUmbrellaPlayerController>(UGameplayStatics::GetPlayerController(World, 0)) : nullptr;
}

AEllaCharacter* UJourneyHookSubsystem::GetElla() const
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	return World ? Cast<AEllaCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)) : nullptr;
}

uint8 UJourneyHookSubsystem::CurrentScreen() const
{
	const AUmbrellaPlayerController* Flow = GetFlow();
	return Flow ? static_cast<uint8>(Flow->GetScreen()) : MAX_uint8;
}

FString UJourneyHookSubsystem::DescribeState() const
{
	FString Out = FString::Printf(TEXT("screen=%s"), CurrentScreen() == MAX_uint8 ? TEXT("none") : *JourneyRules::ScreenName(CurrentScreen()));
	if (const AUmbrellaPlayerController* Flow = GetFlow())
	{
		Out += FString::Printf(TEXT(" mode=%s retries=%d"), Flow->GetPlayMode() == EUmbrellaPlayMode::DirectorsCut ? TEXT("dc") : TEXT("start"), Flow->GetRetryCount());
		if (Flow->PlayerInput)
		{
			// Keys the game's PlayerInput still counts as held (Resuming waits for these to be released).
			TArray<FString> Held;
			for (const FKey& Key : { EKeys::Enter, EKeys::SpaceBar, EKeys::LeftMouseButton, EKeys::Escape, EKeys::F1, EKeys::J, EKeys::K })
			{
				if (Flow->PlayerInput->IsPressed(Key))
				{
					Held.Add(Key.ToString());
				}
			}
			Out += FString::Printf(TEXT(" held=[%s]"), *FString::Join(Held, TEXT(",")));
		}
	}
	if (const AEllaCharacter* Ella = GetElla())
	{
		if (const UUmbrellaHealthComponent* Health = Ella->GetHealth())
		{
			const FHealthState& S = Health->GetState();
			Out += FString::Printf(TEXT(" lives=%d/%d active=%.2f/%.2f"), S.Lives, S.MaxLives, S.Active, S.Capacity);
		}
		Out += FString::Printf(TEXT(" ella=(%.0f,%.0f)"), Ella->GetActorLocation().X, Ella->GetActorLocation().Z);
	}
	if (RouteProgress() >= 0)
	{
		Out += FString::Printf(TEXT(" route_cp=%d"), RouteProgress());
	}
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (const UEncounterDirectorSubsystem* Director = World ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr)
	{
		Out += FString::Printf(TEXT(" encounter=%d phase=%s"), static_cast<int32>(Director->GetState()), *UEncounterDirectorSubsystem::PhaseName(Director->GetPhase()).ToString());
	}
	return Out;
}

void UJourneyHookSubsystem::Tick(float DeltaTime)
{
	if (bEnded)
	{
		if (EndedAt >= 0.0 && FApp::GetCurrentTime() - EndedAt >= JourneyExitDelaySeconds)
		{
			EndedAt = -1.0;
			FPlatformMisc::RequestExit(false);
		}
		return;
	}
	if (StepIndex < 0)
	{
		// Begin once the game's own Start screen is up (or any flow screen, for a script that starts later).
		if (!GetFlow())
		{
			return;
		}
		StepIndex = 0;
		StartStep();
	}
	if (!Steps.IsValidIndex(StepIndex))
	{
		EndJourney(TEXT("none"));
		return;
	}
	const FJourneyStep& Step = Steps[StepIndex];
	const double Now = FApp::GetCurrentTime();
	const double Elapsed = Now - StepStart;
	if (Now - LastOverlayCheck >= JourneyOverlayCheckSeconds && GEngine && GEngine->GameViewport && GEngine->GameViewport->GetWindow().IsValid())
	{
		LastOverlayCheck = Now;
		MakeOverlayClickThrough(GEngine->GameViewport->GetWindow().ToSharedRef());
	}
	const float N0 = Step.Numbers.IsValidIndex(0) ? Step.Numbers[0] : 0.0f;
	++StepFrames;

	if (Step.Command == TEXT("wait") || Step.Command == TEXT("trywait"))
	{
		uint8 Want = 0;
		JourneyRules::HasScreenNamed(Step.Arg, Want);
		if (CurrentScreen() == Want)
		{
			FinishStep(EJourneyResult::Pass, FString::Printf(TEXT("after %.1fs"), Elapsed));
		}
		else if (Elapsed >= N0)
		{
			FinishStep(EJourneyResult::Fail, FString::Printf(TEXT("timeout %.0fs, still %s"), N0, *JourneyRules::ScreenName(CurrentScreen())));
		}
	}
	else if (Step.Command == TEXT("keyuntil"))
	{
		// keyuntil <Screen> <Key> <interval> <timeout>: tap the key every interval until the screen shows (tutorial pages).
		FString ScreenWord, KeyWord;
		Step.Arg.Split(TEXT(" "), &ScreenWord, &KeyWord);
		uint8 Want = 0;
		JourneyRules::HasScreenNamed(ScreenWord, Want);
		const float Timeout = Step.Numbers.IsValidIndex(1) ? Step.Numbers[1] : JourneyDefaultKeyTimeoutSeconds;
		if (CurrentScreen() == Want)
		{
			FinishStep(EJourneyResult::Pass, FString::Printf(TEXT("taps=%d after %.1fs"), AssistHits, Elapsed));
		}
		else if (Elapsed >= Timeout)
		{
			FinishStep(EJourneyResult::Fail, FString::Printf(TEXT("taps=%d timeout %.0fs, still %s"), AssistHits, Timeout, *JourneyRules::ScreenName(CurrentScreen())));
		}
		else if (Now - LastAssist >= N0)
		{
			LastAssist = Now;
			++AssistHits;
			const uint8 Before = CurrentScreen();
			PressSlateKey(FKey(*KeyWord));
			ReleaseSlateKey(FKey(*KeyWord));
			Log(FString::Printf(TEXT("JOURNEY_TAP key=%s n=%d focus=%s from=%s to=%s"), *KeyWord, AssistHits, *LastKeyFocus, *JourneyRules::ScreenName(Before), *JourneyRules::ScreenName(CurrentScreen())));
		}
	}
	else if (Step.Command == TEXT("click"))
	{
		if (ClickPresses == 0)
		{
			FString Detail;
			bool bOk = false;
			const uint8 Before = CurrentScreen();
			ClickLabel(Step.Arg, Detail, bOk);
			if (bOk)
			{
				ClickPresses = 1;
				LastClickPress = Now;
				ClickFrom = Before;
				ClickDetail = Detail;
			}
			else if (Elapsed >= JourneyClickWaitSeconds)
			{
				FinishStep(EJourneyResult::Fail, Detail);
			}
		}
		else
		{
			const JourneyRules::EJourneyClickNext Next = JourneyRules::ClickNext(CurrentScreen() != ClickFrom, IsButtonShown(Step.Arg), Now - LastClickPress, ClickPresses);
			if (Next == JourneyRules::EJourneyClickNext::Done)
			{
				FinishStep(EJourneyResult::Pass, ClickDetail + FString::Printf(TEXT(" presses=%d"), ClickPresses));
			}
			else if (Next == JourneyRules::EJourneyClickNext::ClickAgain || Next == JourneyRules::EJourneyClickNext::PressAccept)
			{
				const bool bMouse = Next == JourneyRules::EJourneyClickNext::ClickAgain;
				FString Detail;
				bool bOk = false;
				if (bMouse)
				{
					ClickLabel(Step.Arg, Detail, bOk);
				}
				else
				{
					PressAcceptOn(Step.Arg, bOk);
				}
				++ClickPresses;
				LastClickPress = Now;
				Log(FString::Printf(TEXT("JOURNEY_CLICK_RETRY label=\"%s\" n=%d by=%s sent=%d still=%s %s"), *Step.Arg, ClickPresses, bMouse ? TEXT("mouse") : TEXT("enter"), bOk ? 1 : 0,
					*JourneyRules::ScreenName(CurrentScreen()), *Detail));
			}
			else if (Next == JourneyRules::EJourneyClickNext::Fail)
			{
				FinishStep(EJourneyResult::Fail, FString::Printf(TEXT("clicked %d times (mouse, then Enter), still %s: %s"), ClickPresses, *JourneyRules::ScreenName(CurrentScreen()), *ClickDetail));
			}
		}
	}
	else if (Step.Command == TEXT("idle"))
	{
		if (Elapsed >= N0)
		{
			FinishStep(EJourneyResult::Pass, FString());
		}
	}
	else if (Step.Command == TEXT("shot"))
	{
		if (StepFrames >= JourneyShotSettleFrames)
		{
			FString Detail;
			bool bOk = false;
			SaveShot(Step.Arg, Detail, bOk);
			FinishStep(bOk ? EJourneyResult::Pass : EJourneyResult::Fail, Detail);
		}
	}
	else if (Step.Command == TEXT("hold"))
	{
		if (Elapsed >= N0)
		{
			ReleaseSlateKey(HeldKey);
			HeldKey = FKey();
			FinishStep(EJourneyResult::Pass, FString::Printf(TEXT("held %.2fs"), Elapsed));
		}
	}
	else if (Step.Command == TEXT("hits"))
	{
		// hits <Screen> <damage> <interval> <timeout>: assisted damage through Ella's own Health hit path.
		uint8 Want = 0;
		JourneyRules::HasScreenNamed(Step.Arg, Want);
		const float Interval = Step.Numbers.IsValidIndex(1) ? Step.Numbers[1] : JourneyDefaultHitIntervalSeconds;
		const float Timeout = Step.Numbers.IsValidIndex(2) ? Step.Numbers[2] : JourneyDefaultHitsTimeoutSeconds;
		if (CurrentScreen() == Want)
		{
			FinishStep(EJourneyResult::Pass, FString::Printf(TEXT("assisted_hits=%d after %.1fs"), AssistHits, Elapsed));
		}
		else if (Elapsed >= Timeout)
		{
			FinishStep(EJourneyResult::Fail, FString::Printf(TEXT("assisted_hits=%d timeout %.0fs, still %s"), AssistHits, Timeout, *JourneyRules::ScreenName(CurrentScreen())));
		}
		else if (Now - LastAssist >= Interval)
		{
			LastAssist = Now;
			AEllaCharacter* Ella = GetElla();
			if (Ella && Ella->GetHealth())
			{
				const EHitResult Result = Ella->GetHealth()->TakeHit(N0, FName(TEXT("JourneyAssist")));
				++AssistHits;
				Log(FString::Printf(TEXT("JOURNEY_ASSIST hit=%d damage=%.2f landed=%d %s"), AssistHits, N0, Result == EHitResult::Landed ? 1 : 0, *DescribeState()));
			}
		}
	}
	else if (Step.Command == TEXT("route"))
	{
		// route <N> <timeout>: real keys only (D held, Space and E tapped) until the director reports checkpoint N.
		const int32 Want = FMath::RoundToInt(N0);
		const float Timeout = Step.Numbers.IsValidIndex(1) ? Step.Numbers[1] : JourneyDefaultWinTimeoutSeconds;
		const AEllaCharacter* Ella = GetElla();
		const float X = Ella ? static_cast<float>(Ella->GetActorLocation().X) : 0.0f;
		RouteBestX = FMath::Max(RouteBestX, X);
		const int32 Progress = RouteProgress();
		if (Progress >= Want)
		{
			ReleaseSlateKey(EKeys::D);
			ReleaseSlateKey(EKeys::J);
			bRouteSinking = false;
			FinishStep(EJourneyResult::Pass, FString::Printf(TEXT("cp=%d after %.1fs real_input x_start=%.0f x_best=%.0f heals=%d"), Progress, Elapsed, RouteStartX, RouteBestX, RouteHeals));
		}
		else if (Elapsed >= Timeout || Progress < 0)
		{
			ReleaseSlateKey(EKeys::D);
			ReleaseSlateKey(EKeys::J);
			bRouteSinking = false;
			FinishStep(EJourneyResult::Fail, FString::Printf(TEXT("cp=%d want=%d %s after %.1fs real_input x_start=%.0f x_best=%.0f heals=%d"), Progress, Want,
				Progress < 0 ? TEXT("no route") : TEXT("timeout"), Elapsed, RouteStartX, RouteBestX, RouteHeals));
		}
		else if (CurrentScreen() == static_cast<uint8>(EFlowScreen::LevelUp) || CurrentScreen() == static_cast<uint8>(EFlowScreen::Story)
			|| CurrentScreen() == static_cast<uint8>(EFlowScreen::Purchase))
		{
			// A level-up or story card on the route: Enter, as a player would; a refuge purchase screen: Escape (leave
			// without spending). Logged with the screen it closed.
			if (Now - LastRouteHop >= JourneyRouteHopSeconds)
			{
				LastRouteHop = Now;
				const uint8 Before = CurrentScreen();
				const FKey Key = Before == static_cast<uint8>(EFlowScreen::Purchase) ? EKeys::Escape : EKeys::Enter;
				PressSlateKey(Key);
				ReleaseSlateKey(Key);
				Log(FString::Printf(TEXT("JOURNEY_ROUTE_CARD key=%s from=%s to=%s"), *Key.ToString(), *JourneyRules::ScreenName(Before), *JourneyRules::ScreenName(CurrentScreen())));
			}
		}
		else if (CurrentScreen() == static_cast<uint8>(EFlowScreen::Playing))
		{
			if (Now - LastRouteHop >= JourneyRouteHopSeconds)
			{
				LastRouteHop = Now;
				PressSlateKey(EKeys::SpaceBar);
				ReleaseSlateKey(EKeys::SpaceBar);
			}
			if (Now - LastRouteDash >= JourneyRouteDashSeconds)
			{
				LastRouteDash = Now;
				PressSlateKey(EKeys::E);
				ReleaseSlateKey(EKeys::E);
			}
			// route <N> <timeout> 1: hold Shoot (J, real key) while Ella is above the route's stand height, so she sinks
			// back instead of rising off the top; without it she rises as long as nothing is held (GDD controls).
			const bool bTrim = Step.Numbers.IsValidIndex(2) && Step.Numbers[2] > 0.0f;
			const bool bHigh = Ella && Ella->GetActorLocation().Z > LevelPlan::CheckpointStandLocation(1).Z + JourneyRouteTrimAbove;
			if (bTrim && bHigh != bRouteSinking)
			{
				bRouteSinking = bHigh;
				bHigh ? PressSlateKey(EKeys::J) : ReleaseSlateKey(EKeys::J);
			}
			if (AEllaCharacter* Hurt = GetElla(); Hurt && Hurt->GetHealth())
			{
				const FHealthState& S = Hurt->GetHealth()->GetState();
				if (!S.IsDefeated() && (S.Active < S.Capacity || S.Lives < S.MaxLives))
				{
					Hurt->GetHealth()->ResetForRetry();
					++RouteHeals;
					Log(FString::Printf(TEXT("JOURNEY_ASSIST route_heal=%d %s"), RouteHeals, *DescribeState()));
				}
			}
			if (Now - LastRouteLog >= JourneyRouteLogSeconds)
			{
				LastRouteLog = Now;
				Log(FString::Printf(TEXT("JOURNEY_ROUTE t=%.1f %s"), Elapsed, *DescribeState()));
			}
		}
	}
	else if (Step.Command == TEXT("assistwin"))
	{
		const float Timeout = N0 > 0.0f ? N0 : JourneyDefaultWinTimeoutSeconds;
		if (CurrentScreen() == static_cast<uint8>(EFlowScreen::Story))
		{
			ReleaseSlateKey(HeldKey);
			HeldKey = FKey();
			FinishStep(EJourneyResult::Pass, FString::Printf(TEXT("assisted_part_hits=%d after %.1fs"), AssistHits, Elapsed));
		}
		else if (Elapsed >= Timeout)
		{
			ReleaseSlateKey(HeldKey);
			HeldKey = FKey();
			FinishStep(EJourneyResult::Fail, FString::Printf(TEXT("assisted_part_hits=%d timeout %.0fs %s"), AssistHits, Timeout, *DescribeState()));
		}
		else if (Now - LastAssist >= JourneyRouteHopSeconds && CurrentScreen() == static_cast<uint8>(EFlowScreen::LevelUp))
		{
			// Director's Cut level-up card mid-fight: Enter, as a player would (logged).
			LastAssist = Now;
			PressSlateKey(EKeys::Enter);
			ReleaseSlateKey(EKeys::Enter);
			Log(FString::Printf(TEXT("JOURNEY_FIGHT_CARD key=Enter from=LevelUp to=%s"), *JourneyRules::ScreenName(CurrentScreen())));
		}
		else if (Now - LastAssist >= JourneyAssistIntervalSeconds && CurrentScreen() == static_cast<uint8>(EFlowScreen::Playing))
		{
			LastAssist = Now;
			AEllaCharacter* Ella = GetElla();
			UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
			UEncounterDirectorSubsystem* Director = World ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr;
			if (Ella && Ella->GetHealth())
			{
				const FHealthState& S = Ella->GetHealth()->GetState();
				if (!S.IsDefeated() && (S.Active < S.Capacity || S.Lives < S.MaxLives))
				{
					Ella->GetHealth()->ResetForRetry();
				}
			}
			const EKeeperPhase PhaseBefore = Director ? Director->GetPhase() : EKeeperPhase::Wings;
			FUmbrellaShotSpec Spec = Ella && Ella->GetAttack() ? Ella->GetAttack()->GetLastShot() : FUmbrellaShotSpec();
			Spec.Kind = EUmbrellaShotKind::PlayerBlast;
			Spec.Damage = Spec.Damage > 0.0f ? Spec.Damage : 1.0f;
			int32 Consumed = 0;
			for (TActorIterator<AKeeperOfTime> It(World); World && It; ++It)
			{
				for (int32 Part = 0; Part < static_cast<int32>(EKeeperPart::Count); ++Part)
				{
					for (UKeeperPartComponent* Component : { It->GetPartComponent(static_cast<EKeeperPart>(Part)), It->GetHeadComponent(static_cast<EKeeperPart>(Part)) })
					{
						if (Component && Component->ReceiveShot(Spec, Component->GetComponentLocation()) == EUmbrellaShotResult::Consumed)
						{
							++Consumed;
						}
					}
				}
			}
			AssistHits += Consumed;
			if (Director && Director->GetPhase() != PhaseBefore)
			{
				Log(FString::Printf(TEXT("JOURNEY_PHASE from=%s to=%s part_hits=%d %s"), *UEncounterDirectorSubsystem::PhaseName(PhaseBefore).ToString(),
					*UEncounterDirectorSubsystem::PhaseName(Director->GetPhase()).ToString(), AssistHits, *DescribeState()));
			}
		}
	}
}

void UJourneyHookSubsystem::StartStep()
{
	if (!Steps.IsValidIndex(StepIndex))
	{
		EndJourney(TEXT("none"));
		return;
	}
	const FJourneyStep& Step = Steps[StepIndex];
	StepStart = FApp::GetCurrentTime();
	StepFrames = 0;
	LastAssist = 0.0;
	AssistHits = 0;
	ClickPresses = 0;
	LastClickPress = 0.0;
	ClickDetail.Reset();
	const float N0 = Step.Numbers.IsValidIndex(0) ? Step.Numbers[0] : 0.0f;

	if (Step.Command == TEXT("wait") || Step.Command == TEXT("trywait") || Step.Command == TEXT("hits"))
	{
		uint8 Want = 0;
		if (!JourneyRules::HasScreenNamed(Step.Arg, Want))
		{
			FinishStep(EJourneyResult::Fail, FString::Printf(TEXT("no screen named '%s'"), *Step.Arg));
		}
	}
	else if (Step.Command == TEXT("key"))
	{
		const FKey Key(*Step.Arg);
		if (!Key.IsValid())
		{
			FinishStep(EJourneyResult::Fail, TEXT("no such key"));
			return;
		}
		const uint8 Before = CurrentScreen();
		PressSlateKey(Key);
		ReleaseSlateKey(Key);
		FinishStep(EJourneyResult::Pass, FString::Printf(TEXT("from=%s focus=%s"), *JourneyRules::ScreenName(Before), *LastKeyFocus));
	}
	else if (Step.Command == TEXT("hold"))
	{
		HeldKey = FKey(*Step.Arg);
		if (!HeldKey.IsValid())
		{
			FinishStep(EJourneyResult::Fail, TEXT("no such key"));
			return;
		}
		PressSlateKey(HeldKey);
	}
	else if (Step.Command == TEXT("route"))
	{
		const AEllaCharacter* Ella = GetElla();
		RouteStartX = Ella ? static_cast<float>(Ella->GetActorLocation().X) : 0.0f;
		RouteBestX = RouteStartX;
		RouteHeals = 0;
		LastRouteHop = 0.0;
		LastRouteDash = 0.0;
		LastRouteLog = 0.0;
		PressSlateKey(EKeys::D);
	}
	else if (Step.Command == TEXT("routeassist"))
	{
		// routeassist <N>: place Ella at checkpoint N through the director's own PlaceAtCheckpoint (4: past the handoff line).
		const int32 Want = FMath::RoundToInt(N0);
		UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
		AUmbrellaGameMode* Mode = World ? World->GetAuthGameMode<AUmbrellaGameMode>() : nullptr;
		AUmbrellaLevelDirector* Level = Mode ? Mode->GetLevelDirector() : nullptr;
		AEllaCharacter* Ella = GetElla();
		bool bOk = false;
		FString Detail = TEXT("no route or no Ella");
		if (Level && Ella && RouteProgress() >= Want)
		{
			bOk = true;
			Detail = FString::Printf(TEXT("not needed: real input already reached %d"), RouteProgress());
		}
		else if (Level && Ella)
		{
			const float FromX = static_cast<float>(Ella->GetActorLocation().X);
			if (Want >= JourneyRouteHandoff)
			{
				FVector Past = LevelPlan::CheckpointStandLocation(LevelPlanConst::MaxCheckpoint);
				Past.X = LevelPlan::KeeperHandoffX() + 1.0f;
				bOk = Ella->SetActorLocation(Past, false, nullptr, ETeleportType::TeleportPhysics);
			}
			else
			{
				bOk = Level->PlaceAtCheckpoint(Ella, Want) == Want;
			}
			Detail = FString::Printf(TEXT("ASSIST placed at %s from x=%.0f to x=%.0f"), Want >= JourneyRouteHandoff ? TEXT("handoff") : *FString::Printf(TEXT("CP%d"), Want),
				FromX, static_cast<float>(Ella->GetActorLocation().X));
		}
		Log(FString::Printf(TEXT("JOURNEY_ASSIST routeassist=%d ok=%d %s"), Want, bOk ? 1 : 0, *Detail));
		FinishStep(bOk ? EJourneyResult::Pass : EJourneyResult::Fail, Detail);
	}
	else if (Step.Command == TEXT("assistwin"))
	{
		HeldKey = EKeys::J;
		PressSlateKey(HeldKey);
	}
	else if (Step.Command == TEXT("click"))
	{
		// Clicked from Tick once the button has been laid out and painted (a just-opened menu has no geometry yet).
	}
	else if (Step.Command == TEXT("music"))
	{
		UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
		const UUmbrellaCueSubsystem* Cues = World ? World->GetSubsystem<UUmbrellaCueSubsystem>() : nullptr;
		const FName Id = Cues ? Cues->GetMusicId() : NAME_None;
		const UAudioComponent* Component = Cues ? Cues->GetMusicComponent() : nullptr;
		const FString Sound = Component && Component->Sound ? Component->Sound->GetName() : TEXT("none");
		const bool bWantNone = Step.Arg.Equals(TEXT("none"), ESearchCase::IgnoreCase);
		// run_game.sh runs with -nosound: no audio device, so no music component can play. The cue system still picks the
		// row and loads its take (LastSoundId); that is what is measured then, and the line says so (playback=unmeasured).
		const bool bNoDevice = !Component;
		const FName Picked = Id.IsNone() && bNoDevice && Cues ? Cues->GetLastSoundId() : Id;
		const bool bIsMusic = !Picked.IsNone() && Picked.ToString().StartsWith(TEXT("Music"));
		const bool bOk = bWantNone ? Id.IsNone() : (bIsMusic && (Step.Arg.IsEmpty() || Step.Arg.Equals(TEXT("any"), ESearchCase::IgnoreCase) || Picked.ToString().Equals(Step.Arg, ESearchCase::IgnoreCase)));
		FinishStep(bOk ? EJourneyResult::Pass : EJourneyResult::Fail, FString::Printf(TEXT("music_id=%s picked=%s sound=%s starts=%d sound_cues=%d playback=%s"), *Id.ToString(), *Picked.ToString(), *Sound,
			Cues ? Cues->GetMusicStartCount() : -1, Cues ? Cues->GetSoundCueCount() : -1, bNoDevice ? TEXT("unmeasured_nosound") : TEXT("measured")));
	}
	else if (Step.Command == TEXT("retrycheck"))
	{
		// After Retry: full health, max lives, the run playing again.
		const AEllaCharacter* Ella = GetElla();
		const UUmbrellaHealthComponent* Health = Ella ? Ella->GetHealth() : nullptr;
		const bool bFull = Health && Health->GetState().Lives == Health->GetState().MaxLives && FMath::IsNearlyEqual(Health->GetState().Active, Health->GetState().Capacity);
		FinishStep(bFull ? EJourneyResult::Pass : EJourneyResult::Fail, bFull ? TEXT("full health, max lives") : TEXT("not full after retry"));
	}
	else if (Step.Command == TEXT("firstrun"))
	{
		// A first-time player: the tutorial shows on the first Start (kept in memory; the settings file is not touched).
		AUmbrellaPlayerController* Flow = GetFlow();
		if (Flow)
		{
			Flow->KeepTutorialInMemoryOnly();
			Flow->ClearTutorialSeen();
		}
		FinishStep(Flow != nullptr ? EJourneyResult::Pass : EJourneyResult::Fail, TEXT("tutorial not seen (memory only)"));
	}
	else if (Step.Command == TEXT("console"))
	{
		// Diagnostics only (e.g. "viewmode unlit"); named in the log so a capture after it is never taken for the game's look.
		AUmbrellaPlayerController* Flow = GetFlow();
		const bool bOk = Flow != nullptr;
		if (Flow)
		{
			Flow->ConsoleCommand(Step.Arg, true);
		}
		FinishStep(bOk ? EJourneyResult::Pass : EJourneyResult::Fail, FString::Printf(TEXT("DIAGNOSTIC console '%s'"), *Step.Arg));
	}
	else if (Step.Command == TEXT("texts"))
	{
		// What text the window holds now, in paint order with each text's painted size (0x0 = never painted).
		TArray<FString> Texts;
		if (GEngine && GEngine->GameViewport && GEngine->GameViewport->GetWindow().IsValid())
		{
			CollectTexts(GEngine->GameViewport->GetWindow().ToSharedRef(), Texts);
		}
		FinishStep(EJourneyResult::Pass, FString::Join(Texts, TEXT(" | ")));
	}
	else if (Step.Command == TEXT("skipunless"))
	{
		// skipunless <Screen> <n>: when the screen is not <Screen>, the next n steps are skipped (logged), e.g. the
		// Director's Cut purchase screen that only shows once points are earned.
		uint8 Want = 0;
		const bool bKnown = JourneyRules::HasScreenNamed(Step.Arg, Want);
		const int32 Count = FMath::RoundToInt(N0);
		const bool bShown = bKnown && CurrentScreen() == Want;
		SkipAfterStep = bKnown && !bShown ? FMath::Max(0, Count) : 0;
		FinishStep(bKnown ? EJourneyResult::Pass : EJourneyResult::Fail,
			bShown ? FString::Printf(TEXT("%s shown, next %d steps run"), *Step.Arg, Count) : FString::Printf(TEXT("%s not shown, next %d steps skipped"), *Step.Arg, Count));
	}
	else if (Step.Command == TEXT("log"))
	{
		FinishStep(EJourneyResult::Pass, Step.Arg);
	}
	else if (Step.Command == TEXT("end"))
	{
		EndJourney(TEXT("none"));
	}
	(void)N0;
}

void UJourneyHookSubsystem::FinishStep(EJourneyResult Result, const FString& Detail)
{
	if (bEnded || !Steps.IsValidIndex(StepIndex))
	{
		return;
	}
	const FJourneyStep& Step = Steps[StepIndex];
	const bool bPass = Result == EJourneyResult::Pass;
	bPass ? ++Passed : ++Failed;
	Log(FString::Printf(TEXT("JOURNEY_STEP n=%d line=%d cmd=\"%s %s\" result=%s %s detail=\"%s\""), StepIndex + 1, Step.Line, *Step.Command, *Step.Arg,
		bPass ? TEXT("PASS") : TEXT("FAIL"), *DescribeState(), *Detail));
	if (!bPass && Step.Command != TEXT("music") && Step.Command != TEXT("retrycheck") && Step.Command != TEXT("shot") && Step.Command != TEXT("trywait") && Step.Command != TEXT("route"))
	{
		EndJourney(FString::Printf(TEXT("line %d %s %s: %s"), Step.Line, *Step.Command, *Step.Arg, *Detail));
		return;
	}
	StepIndex = FMath::Min(Steps.Num(), StepIndex + 1 + SkipAfterStep);
	SkipAfterStep = 0;
	StartStep();
}

void UJourneyHookSubsystem::EndJourney(const FString& Blocker)
{
	if (bEnded)
	{
		return;
	}
	if (HeldKey.IsValid())
	{
		ReleaseSlateKey(HeldKey);
	}
	bEnded = true;
	EndedAt = FApp::GetCurrentTime();
	Log(FString::Printf(TEXT("JOURNEY_END passed=%d failed=%d blocker=\"%s\" %s"), Passed, Failed, *Blocker, *DescribeState()));
}

void UJourneyHookSubsystem::PressSlateKey(const FKey& Key)
{
	SendSlateKey(Key, IE_Pressed);
}

void UJourneyHookSubsystem::ReleaseSlateKey(const FKey& Key)
{
	SendSlateKey(Key, IE_Released);
}

void UJourneyHookSubsystem::SendSlateKey(const FKey& Key, EInputEvent Event)
{
	if (!Key.IsValid() || !FSlateApplication::IsInitialized())
	{
		return;
	}
	// The keyboard's own entry point: Slate gives it to the focused menu, or to the game viewport and the controller.
	const FKeyEvent KeyEvent(Key, FModifierKeysState(), 0, false, 0, 0);
	if (Event == IE_Pressed)
	{
		const TSharedPtr<SWidget> Focused = FSlateApplication::Get().GetUserFocusedWidget(0);
		LastKeyFocus = Focused.IsValid() ? Focused->GetTypeAsString() : TEXT("none");
		FSlateApplication::Get().ProcessKeyDownEvent(KeyEvent);
	}
	else
	{
		FSlateApplication::Get().ProcessKeyUpEvent(KeyEvent);
	}
}

TSharedPtr<SWidget> UJourneyHookSubsystem::FindButtonWithLabel(const TSharedRef<SWidget>& Root, const FString& Label) const
{
	if (Root->GetType() == FName(TEXT("STextBlock")) && Root->GetVisibility().IsVisible()
		&& JourneyRules::IsLabelMatch(StaticCastSharedRef<STextBlock>(Root)->GetText().ToString(), Label))
	{
		for (TSharedPtr<SWidget> Up = Root->GetParentWidget(); Up.IsValid(); Up = Up->GetParentWidget())
		{
			if (Up->GetType().ToString().Contains(TEXT("Button")))
			{
				return Up;
			}
		}
	}
	FChildren* Children = Root->GetChildren();
	for (int32 Index = 0; Children && Index < Children->Num(); ++Index)
	{
		if (TSharedPtr<SWidget> Found = FindButtonWithLabel(Children->GetChildAt(Index), Label))
		{
			return Found;
		}
	}
	return nullptr;
}

void UJourneyHookSubsystem::CollectTexts(const TSharedRef<SWidget>& Root, TArray<FString>& Out) const
{
	if (!Root->GetVisibility().IsVisible())
	{
		return;
	}
	if (Root->GetType() == FName(TEXT("STextBlock")))
	{
		const FString Text = StaticCastSharedRef<STextBlock>(Root)->GetText().ToString();
		if (!Text.TrimStartAndEnd().IsEmpty())
		{
			const FVector2D Size = Root->GetPaintSpaceGeometry().GetLocalSize();
			Out.Add(FString::Printf(TEXT("%s(%.0fx%.0f)"), *Text.Left(JourneyTextLogChars), Size.X, Size.Y));
		}
	}
	FChildren* Children = Root->GetChildren();
	for (int32 Index = 0; Children && Index < Children->Num(); ++Index)
	{
		CollectTexts(Children->GetChildAt(Index), Out);
	}
}

void UJourneyHookSubsystem::MakeOverlayClickThrough(const TSharedRef<SWidget>& Root)
{
	if (Root->GetType() == FName(TEXT("SSoundLabelList")) && Root->GetVisibility() != EVisibility::HitTestInvisible)
	{
		Root->SetVisibility(EVisibility::HitTestInvisible);
		Log(TEXT("JOURNEY_WORKAROUND SSoundLabelList (workbench dev overlay) set HitTestInvisible: it covered the screen and took every mouse click"));
	}
	FChildren* Children = Root->GetChildren();
	for (int32 Index = 0; Children && Index < Children->Num(); ++Index)
	{
		MakeOverlayClickThrough(Children->GetChildAt(Index));
	}
}

bool UJourneyHookSubsystem::IsButtonShown(const FString& Label) const
{
	TSharedPtr<SWindow> Window = GEngine && GEngine->GameViewport ? GEngine->GameViewport->GetWindow() : nullptr;
	return Window.IsValid() && FindButtonWithLabel(Window.ToSharedRef(), Label).IsValid();
}

void UJourneyHookSubsystem::PressAcceptOn(const FString& Label, bool& bOutSent)
{
	bOutSent = false;
	TSharedPtr<SWindow> Window = GEngine && GEngine->GameViewport ? GEngine->GameViewport->GetWindow() : nullptr;
	const TSharedPtr<SWidget> Button = Window.IsValid() && FSlateApplication::IsInitialized() ? FindButtonWithLabel(Window.ToSharedRef(), Label) : nullptr;
	if (!Button.IsValid())
	{
		return;
	}
	// SlateApplication.h (5.8.4): SetKeyboardFocus(const TSharedPtr<SWidget>&, EFocusCause). SButton::OnKeyDown presses on
	// the Accept navigation action, which Enter maps to.
	FSlateApplication::Get().SetKeyboardFocus(Button, EFocusCause::SetDirectly);
	PressSlateKey(EKeys::Enter);
	ReleaseSlateKey(EKeys::Enter);
	bOutSent = true;
}

void UJourneyHookSubsystem::ClickLabel(const FString& Label, FString& OutDetail, bool& bOutClicked)
{
	TSharedPtr<SWindow> Window = GEngine && GEngine->GameViewport ? GEngine->GameViewport->GetWindow() : nullptr;
	if (!Window.IsValid() || !FSlateApplication::IsInitialized())
	{
		OutDetail = TEXT("no window");
		bOutClicked = false;
		return;
	}
	TSharedPtr<SWidget> Button = FindButtonWithLabel(Window.ToSharedRef(), Label);
	if (!Button.IsValid())
	{
		OutDetail = FString::Printf(TEXT("no visible button labelled '%s'"), *Label);
		bOutClicked = false;
		return;
	}
	// Workbench builds lay the dev sound-label list (Feedback/Audio/SoundLabelHud.cpp) over the whole viewport, hit-testable,
	// so it takes every click; the packaged game (UMBRELLAELLA_WORKBENCH=0) has no such list. Let clicks through it, logged
	// (docs/build/requests/agentplay.md asks its lane for HitTestInvisible).
	// A real mouse: move over the button's centre, press and release the left button there (Slate hit-tests it).
	const FGeometry Geometry = Button->GetTickSpaceGeometry();
	if (Geometry.GetLocalSize().X <= 0.0f || Geometry.GetLocalSize().Y <= 0.0f)
	{
		OutDetail = FString::Printf(TEXT("button '%s' not laid out yet"), *Label);
		bOutClicked = false;
		return;
	}
	const FVector2D Centre = Geometry.GetAbsolutePositionAtCoordinates(FVector2D(0.5, 0.5));
	const uint8 Before = CurrentScreen();
	FSlateApplication& Slate = FSlateApplication::Get();
	const TSet<FKey> None;
	TSet<FKey> Left;
	Left.Add(EKeys::LeftMouseButton);
	Slate.ProcessMouseMoveEvent(FPointerEvent(0, Centre, Centre, None, FKey(), 0.0f, FModifierKeysState()));
	Slate.ProcessMouseButtonDownEvent(Window->GetNativeWindow(), FPointerEvent(0, Centre, Centre, Left, EKeys::LeftMouseButton, 0.0f, FModifierKeysState()));
	Slate.ProcessMouseButtonUpEvent(FPointerEvent(0, Centre, Centre, None, EKeys::LeftMouseButton, 0.0f, FModifierKeysState()));
	const FWidgetPath Under = Slate.LocateWindowUnderMouse(Centre, Slate.GetInteractiveTopLevelWindows());
	const FString UnderName = Under.IsValid() ? Under.GetLastWidget()->GetTypeAsString() : TEXT("none");
	const TSharedPtr<SWidget> Focused = Slate.GetUserFocusedWidget(0);
	OutDetail = FString::Printf(TEXT("mouse at (%.0f,%.0f) on %s, under=%s focus=%s active=%d window_pos=%s from=%s"), Centre.X, Centre.Y, *Button->GetType().ToString(), *UnderName,
		Focused.IsValid() ? *Focused->GetTypeAsString() : TEXT("none"), Slate.IsActive() ? 1 : 0, *Window->GetPositionInScreen().ToString(), *JourneyRules::ScreenName(Before));
	bOutClicked = true;
}

int32 UJourneyHookSubsystem::RouteProgress() const
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	const AUmbrellaGameMode* Mode = World ? World->GetAuthGameMode<AUmbrellaGameMode>() : nullptr;
	const AUmbrellaLevelDirector* Level = Mode ? Mode->GetLevelDirector() : nullptr;
	if (!Level || Level->GetSlotsSpawned() == 0)
	{
		return -1;
	}
	return Level->HasHandedOff() ? JourneyRouteHandoff : Level->GetCheckpointReached();
}

FString UJourneyHookSubsystem::MeasureView(const TArray<FColor>& Bitmap, const FIntVector& Size) const
{
	AUmbrellaPlayerController* Flow = GetFlow();
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (!Flow || !World || Size.X <= 0 || Size.Y <= 0 || Bitmap.Num() != Size.X * Size.Y)
	{
		return TEXT("view=unmeasured");
	}
	int32 ViewW = 0;
	int32 ViewH = 0;
	Flow->GetViewportSize(ViewW, ViewH);
	const double ScaleX = ViewW > 0 ? static_cast<double>(Size.X) / ViewW : 1.0;
	const double ScaleY = ViewH > 0 ? static_cast<double>(Size.Y) / ViewH : 1.0;
	auto Luma = [](const FColor& C) { return JourneyLumaR * C.R + JourneyLumaG * C.G + JourneyLumaB * C.B; };
	double FrameSum = 0.0;
	for (const FColor& C : Bitmap)
	{
		FrameSum += Luma(C);
	}
	const double FrameMean = FrameSum / Bitmap.Num();
	const int32 Half = FMath::Max(2, FMath::RoundToInt(Size.Y * JourneyViewBoxFraction));
	auto Measure = [&](const TCHAR* Name, const AActor* Actor) -> FString
	{
		if (!Actor)
		{
			return FString::Printf(TEXT("%s=absent"), Name);
		}
		FVector Origin, Extent;
		Actor->GetActorBounds(true, Origin, Extent);
		FVector2D Px;
		if (!Flow->ProjectWorldLocationToScreen(Origin, Px))
		{
			return FString::Printf(TEXT("%s=behind_camera"), Name);
		}
		const int32 Cx = FMath::RoundToInt(Px.X * ScaleX);
		const int32 Cy = FMath::RoundToInt(Px.Y * ScaleY);
		if (Cx < 0 || Cy < 0 || Cx >= Size.X || Cy >= Size.Y)
		{
			return FString::Printf(TEXT("%s=offscreen(%d,%d)"), Name, Cx, Cy);
		}
		double Sum = 0.0, Sq = 0.0;
		int32 N = 0;
		for (int32 Y = FMath::Max(0, Cy - Half); Y <= FMath::Min(Size.Y - 1, Cy + Half); ++Y)
		{
			for (int32 X = FMath::Max(0, Cx - Half); X <= FMath::Min(Size.X - 1, Cx + Half); ++X)
			{
				const double L = Luma(Bitmap[Y * Size.X + X]);
				Sum += L;
				Sq += L * L;
				++N;
			}
		}
		const double Mean = N > 0 ? Sum / N : 0.0;
		const double Spread = N > 0 ? FMath::Sqrt(FMath::Max(0.0, Sq / N - Mean * Mean)) : 0.0;
		const bool bDrawn = Spread >= JourneyViewContrastMin || FMath::Abs(Mean - FrameMean) >= JourneyViewContrastMin;
		return FString::Printf(TEXT("%s=%s(%d,%d) spread=%.0f mean=%.0f"), Name, bDrawn ? TEXT("drawn") : TEXT("flat"), Cx, Cy, Spread, Mean);
	};
	TActorIterator<AKeeperOfTime> KeeperIt(World);
	const AKeeperOfTime* Keeper = KeeperIt ? *KeeperIt : nullptr;
	TActorIterator<AUmbrellaArena> ArenaIt(World);
	const AUmbrellaArena* Arena = ArenaIt ? *ArenaIt : nullptr;
	return FString::Printf(TEXT("view frame_mean=%.0f %s %s %s"), FrameMean, *Measure(TEXT("ella"), Flow->GetPawn()), *Measure(TEXT("keeper"), Keeper), *Measure(TEXT("arena"), Arena));
}

void UJourneyHookSubsystem::SaveShot(const FString& Name, FString& OutDetail, bool& bOutSaved)
{
	TSharedPtr<SWindow> Window = GEngine && GEngine->GameViewport ? GEngine->GameViewport->GetWindow() : nullptr;
	TArray<FColor> Bitmap;
	FIntVector Size;
	if (!Window.IsValid() || !FSlateApplication::Get().TakeScreenshot(Window.ToSharedRef(), Bitmap, Size) || Bitmap.Num() == 0)
	{
		OutDetail = TEXT("no window read-back");
		bOutSaved = false;
		return;
	}
	// The window read-back carries the UI; the 3D scene shows where the UI drew nothing (as the agent play hook does).
	FViewport* SceneViewport = GEngine->GameViewport->Viewport;
	TArray<FColor> Scene;
	if (SceneViewport && SceneViewport->GetSizeXY() == FIntPoint(Size.X, Size.Y) && SceneViewport->ReadPixels(Scene) && Scene.Num() == Bitmap.Num())
	{
		for (int32 Index = 0; Index < Bitmap.Num(); ++Index)
		{
			const FColor& Ui = Bitmap[Index];
			if (Ui.R <= JourneyEmptyPixelMax && Ui.G <= JourneyEmptyPixelMax && Ui.B <= JourneyEmptyPixelMax)
			{
				Bitmap[Index] = Scene[Index];
			}
		}
	}
	for (FColor& Color : Bitmap)
	{
		Color.A = JourneyOpaqueAlpha;
	}
	// The viewport widget alone (how the UI art loop captures; UMG screens live in the viewport's overlay).
	if (TSharedPtr<SViewport> ViewportWidget = GEngine->GameViewport->GetGameViewportWidget())
	{
		TArray<FColor> Pixels;
		FIntVector VpSize;
		if (FSlateApplication::Get().TakeScreenshot(ViewportWidget.ToSharedRef(), Pixels, VpSize) && Pixels.Num() > 0)
		{
			for (FColor& Pixel : Pixels)
			{
				Pixel.A = JourneyOpaqueAlpha;
			}
			FImageUtils::SaveImageByExtension(*FPaths::Combine(OutDir, Name + TEXT("_vp.png")), FImageView(Pixels.GetData(), VpSize.X, VpSize.Y));
		}
	}
	// The engine's own screenshot (scene + UI, written a frame later) as a second capture to compare with the composite.
	FScreenshotRequest::RequestScreenshot(FPaths::Combine(OutDir, Name + TEXT("_engine.png")), true, false);
	const FString Path = FPaths::Combine(OutDir, Name + TEXT(".png"));
	bOutSaved = FImageUtils::SaveImageByExtension(*Path, FImageView(Bitmap.GetData(), Size.X, Size.Y));
	OutDetail = FString::Printf(TEXT("%s %dx%d %s"), *FPaths::GetCleanFilename(Path), Size.X, Size.Y, *MeasureView(Bitmap, Size));
}

#else // not a workbench build: the subsystem never exists.

bool UJourneyHookSubsystem::ShouldCreateSubsystem(UObject* Outer) const { return false; }
void UJourneyHookSubsystem::Initialize(FSubsystemCollectionBase& Collection) { Super::Initialize(Collection); }
void UJourneyHookSubsystem::Tick(float DeltaTime) {}
bool UJourneyHookSubsystem::IsTickable() const { return false; }
TStatId UJourneyHookSubsystem::GetStatId() const { RETURN_QUICK_DECLARE_CYCLE_STAT(UJourneyHookSubsystem, STATGROUP_Tickables); }

#endif
