#include "Smoke/AgentPlayHookSubsystem.h"
#include "Core/UmbrellaLog.h"

#if UMBRELLAELLA_WORKBENCH

#include "Attack/AttackEmitterComponent.h"
#include "BrokenMill/BrokenMillRoom.h"
#include "BrokenMill/BrokenMillTuning.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Flow/UmbrellaPlayerController.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "HAL/FileManager.h"
#include "Health/UmbrellaHealthComponent.h"
#include "ImageUtils.h"
#include "InputKeyEventArgs.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Motor/EllaMotorComponent.h"
#include "Widgets/SWindow.h"

namespace
{
	AUmbrellaPlayerController* AgentPlayFlow(UGameInstance* Instance)
	{
		UWorld* World = Instance ? Instance->GetWorld() : nullptr;
		return World ? Cast<AUmbrellaPlayerController>(UGameplayStatics::GetPlayerController(World, 0)) : nullptr;
	}

	float AgentPlayTotalHealth(const AEllaCharacter* Ella)
	{
		const FHealthState& Health = Ella->GetHealth()->GetState();
		return FMath::Max(0, Health.Lives - 1) * Health.Capacity + Health.Active;
	}

	FString AgentPlayJsonString(const FString& Value)
	{
		return TEXT("\"") + Value.ReplaceCharWithEscapedChar() + TEXT("\"");
	}
}

bool UAgentPlayHookSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	return FString(FCommandLine::Get()).Contains(TEXT("-AgentPlay="));
}

void UAgentPlayHookSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	FParse::Value(FCommandLine::Get(), TEXT("-AgentPlay="), Dir);
	Dir = FPaths::ConvertRelativePathToFull(Dir.TrimQuotes());
	FParse::Value(FCommandLine::Get(), TEXT("-AgentPlayMaxSeconds="), MaxGameSeconds);
	FParse::Value(FCommandLine::Get(), TEXT("-AgentPlayIdleTimeout="), IdleTimeoutSeconds);
	bLow = FParse::Param(FCommandLine::Get(), TEXT("AgentPlayLow"));
	IFileManager::Get().MakeDirectory(*FilePath(TEXT("frames")), true);
	WriteStatus(TEXT("waiting"));
}

bool UAgentPlayHookSubsystem::IsTickable() const
{
	return !IsTemplate() && State != EState::Ended;
}

TStatId UAgentPlayHookSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UAgentPlayHookSubsystem, STATGROUP_Tickables);
}

FString UAgentPlayHookSubsystem::FilePath(const FString& Name) const
{
	return FPaths::Combine(Dir, Name);
}

void UAgentPlayHookSubsystem::Tick(float DeltaTime)
{
	switch (State)
	{
	case EState::WaitingForStart:
	{
		AUmbrellaPlayerController* Flow = AgentPlayFlow(GetGameInstance());
		if (Flow && !bSelectedStart && Flow->GetScreen() == EFlowScreen::Title)
		{
			// The Start screen's own path, as the smoke hook does. Setup only: no play happens before the first turn.
			bSelectedStart = true;
			Flow->RequestSmokeStart();
		}
		if (Flow && Flow->GetScreen() == EFlowScreen::Playing)
		{
			State = EState::Setup;
		}
		break;
	}
	case EState::Setup:
		TickSetup();
		break;
	case EState::Paused:
		TickPaused();
		break;
	case EState::Running:
		TickRunning(DeltaTime);
		break;
	default:
		break;
	}
	if (State == EState::Ended && EndedAt > 0.0 && FApp::GetCurrentTime() - EndedAt >= ExitDelaySeconds)
	{
		FPlatformMisc::RequestExit(false);
	}
}

void UAgentPlayHookSubsystem::TickSetup()
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	AEllaCharacter* Pawn = World ? Cast<AEllaCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)) : nullptr;
	if (!Pawn || !Pawn->GetMotor() || !Pawn->GetHealth() || !Pawn->GetAttack())
	{
		return;
	}
	Ella = Pawn;
	Pawn->GetMotor()->ClearPlayBounds();
	ABrokenMillRoom* NewRoom = World->SpawnActor<ABrokenMillRoom>(ABrokenMillRoom::StaticClass(), FTransform(FVector(ScratchRoomX, 0.0, 0.0)));
	if (!NewRoom)
	{
		Finish(TEXT("setup_failed"));
		return;
	}
	NewRoom->BuildRoom();
	Room = NewRoom;

	// Starting placement and health only (the same set-up the scripted run uses); everything after is key presses.
	Pawn->GetHealth()->ResetForRetry();
	if (bLow)
	{
		double Clock = LowHealthClockStart;
		const float Leave = GetDefault<UUmbrellaTuning>()->Health.HitsPerLife * LowHealthShare;
		const float Raw = Pawn->GetHealth()->GetState().Active - Leave;
		if (Raw > 0.0f)
		{
			Pawn->GetHealth()->TakeHitAt(Raw, FName(TEXT("AgentPlayStart")), Clock);
		}
	}
	const FBrokenMillTuning& Mill = NewRoom->GetMillTuning();
	FVector Start = NewRoom->RoomToWorld(FVector2D(RoomStartX, Mill.TargetCentre.Y));
	Start.Y = Pawn->GetActorLocation().Y;
	Pawn->SetActorLocation(Start);
	NewRoom->SetTargetActor(Pawn);
	NewRoom->ResetForRestart();
	NewRoom->SetSimulationPaused(false);

	HealthAtStart = AgentPlayTotalHealth(Pawn);
	StartGuardHp = NewRoom->GetGuardHp();
	ShotsAtStart = Pawn->GetAttack()->GetShotsFired();
	LastLocation = Pawn->GetActorLocation();
	LastSpeed = 0.0f;
	// Let the room and camera settle for a moment of real play-time before the first look; no key is pressed.
	SetPaused(true);
	State = EState::Paused;
	WaitingSince = FApp::GetCurrentTime();
	WriteFrame();
	WriteStatus(TEXT("ready"));
}

void UAgentPlayHookSubsystem::TickPaused()
{
	// Keep the picture fresh while the player thinks (the window may need a few frames to show the room).
	if (AgentPlayRules::IsFrameDue(FApp::GetCurrentTime() - LastFrameReal, FrameIntervalSeconds * PausedFrameFactor))
	{
		WriteFrame();
	}
	if (IFileManager::Get().FileExists(*FilePath(AgentPlayRules::StopFileName())))
	{
		// The player ended the attempt (stop.txt): the numbers are still measured and written.
		Finish(TEXT("stopped"));
		return;
	}
	const FString Path = FilePath(AgentPlayRules::TurnFileName(TurnNumber + 1));
	FString Text;
	if (IFileManager::Get().FileExists(*Path) && FFileHelper::LoadFileToString(Text, *Path))
	{
		const AgentPlayRules::FTurn Turn = AgentPlayRules::ParseTurn(Text);
		++TurnNumber;
		if (!Turn.IsValid())
		{
			// A refused turn does nothing and costs no game time; the player is told why.
			FString Why = FString::Join(Turn.Errors, TEXT("; "));
			WriteTextAtomic(FilePath(FString::Printf(TEXT("turn_%04d.refused.txt"), TurnNumber)), Why);
			WriteStatus(TEXT("paused"));
			return;
		}
		BeginTurn(Turn, TurnNumber);
		return;
	}
	if (FApp::GetCurrentTime() - WaitingSince > IdleTimeoutSeconds)
	{
		Finish(TEXT("abandoned"));
	}
}

void UAgentPlayHookSubsystem::BeginTurn(const AgentPlayRules::FTurn& Turn, int32 Number)
{
	Active = Turn;
	NextEvent = 0;
	TurnMillisElapsed = 0.0;
	++Turns;
	SetPaused(false);
	State = EState::Running;
	WriteStatus(TEXT("running"));
}

void UAgentPlayHookSubsystem::TickRunning(float DeltaTime)
{
	AEllaCharacter* Pawn = Ella.Get();
	ABrokenMillRoom* Mill = Room.Get();
	if (!Pawn || !Mill)
	{
		Finish(TEXT("lost_actor"));
		return;
	}
	TurnMillisElapsed += DeltaTime * MillisPerSecond;
	GameSeconds += DeltaTime;
	while (Active.Events.IsValidIndex(NextEvent) && Active.Events[NextEvent].Millis <= TurnMillisElapsed)
	{
		if (Active.Events[NextEvent].bPressed)
		{
			PressKey(Active.Events[NextEvent].KeyName);
		}
		else
		{
			ReleaseKey(Active.Events[NextEvent].KeyName);
		}
		++NextEvent;
	}

	const FBrokenMillTuning& T = Mill->GetMillTuning();
	const float ErrorZ = T.TargetCentre.Y - Mill->WorldToRoom(Pawn->GetActorLocation()).Y;
	if (FMath::Abs(ErrorZ) > T.TargetSize.Y * 0.5f)
	{
		OffLineSeconds += DeltaTime;
	}
	// Idle: no key down at all this tick (a tap counts while its key is down).
	if (Held.IsEmpty())
	{
		IdleSeconds += DeltaTime;
	}
	const FVector Now = Pawn->GetActorLocation();
	const float Speed = Pawn->GetMotor()->GetVelocity().Size();
	const float Step = static_cast<float>(FVector::Dist(Now, LastLocation));
	if (DeltaTime > 0.0f && Step > FMath::Max(LastSpeed, Speed) * DeltaTime * TeleportSpeedShare + TeleportSlack)
	{
		++TeleportSteps;
	}
	LastLocation = Now;
	LastSpeed = Speed;
	WarningsSeen = Mill->GetEventCount(EMillGuardEvent::WarningStarted);

	if (AgentPlayRules::IsFrameDue(FApp::GetCurrentTime() - LastFrameReal, FrameIntervalSeconds))
	{
		WriteFrame();
	}

	AUmbrellaPlayerController* Flow = AgentPlayFlow(GetGameInstance());
	if (Mill->GetGuardHp() <= 0.0f)
	{
		Finish(TEXT("cleared"));
	}
	else if (Pawn->GetHealth()->GetState().IsDefeated() || (Flow && Flow->GetScreen() == EFlowScreen::Defeat))
	{
		Finish(TEXT("defeated"));
	}
	else if (GameSeconds >= MaxGameSeconds)
	{
		Finish(TEXT("cut"));
	}
	else if (TurnMillisElapsed >= Active.DurationMillis)
	{
		EndTurn();
	}
}

void UAgentPlayHookSubsystem::EndTurn()
{
	if (Active.bReleaseAllAtEnd)
	{
		ReleaseAllKeys();
	}
	SetPaused(true);
	State = EState::Paused;
	WaitingSince = FApp::GetCurrentTime();
	WriteFrame();
	WriteStatus(TEXT("paused"));
}

void UAgentPlayHookSubsystem::Finish(const TCHAR* Outcome)
{
	ReleaseAllKeys();
	WriteFrame();
	WriteResult(Outcome);
	State = EState::Ended;
	EndedAt = FApp::GetCurrentTime();
	WriteStatus(TEXT("ended"));
}

void UAgentPlayHookSubsystem::SetPaused(bool bPaused)
{
	if (UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr)
	{
		UGameplayStatics::SetGamePaused(World, bPaused);
	}
}

void UAgentPlayHookSubsystem::PressKey(const FName& KeyName)
{
	Held.Add(KeyName);
	SendKey(KeyName, IE_Pressed);
}

void UAgentPlayHookSubsystem::ReleaseKey(const FName& KeyName)
{
	Held.Remove(KeyName);
	SendKey(KeyName, IE_Released);
}

void UAgentPlayHookSubsystem::SendKey(const FName& KeyName, EInputEvent Event)
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	APlayerController* Controller = World ? UGameplayStatics::GetPlayerController(World, 0) : nullptr;
	if (!Controller)
	{
		return;
	}
	// The same call a keyboard event ends in (as the smoke hook's input check does).
	FViewport* Viewport = GEngine && GEngine->GameViewport ? GEngine->GameViewport->Viewport : nullptr;
	const FInputDeviceId Device = FInputDeviceId::CreateFromInternalId(0);
	Controller->InputKey(FInputKeyEventArgs(Viewport, Device, FKey(KeyName), Event, 0));
}

void UAgentPlayHookSubsystem::ReleaseAllKeys()
{
	const TArray<FName> Keys = Held.Array();
	for (const FName& Key : Keys)
	{
		ReleaseKey(Key);
	}
}

void UAgentPlayHookSubsystem::WriteFrame()
{
	LastFrameReal = FApp::GetCurrentTime();
	if (!GEngine || !GEngine->GameViewport || !FSlateApplication::IsInitialized())
	{
		return;
	}
	TSharedPtr<SWindow> Window = GEngine->GameViewport->GetWindow();
	if (!Window.IsValid())
	{
		return;
	}
	TArray<FColor> Bitmap;
	FIntVector Size;
	if (!FSlateApplication::Get().TakeScreenshot(Window.ToSharedRef(), Bitmap, Size) || Bitmap.Num() == 0)
	{
		return;
	}
	for (FColor& Color : Bitmap)
	{
		Color.A = OpaqueAlpha;
	}
	const FString Final = FilePath(TEXT("frames/") + AgentPlayRules::FrameFileName(++FrameNumber));
	const FString Temp = FilePath(TEXT("frames/tmp.jpg"));
	const FImageView Image(Bitmap.GetData(), Size.X, Size.Y);
	if (FImageUtils::SaveImageByExtension(*Temp, Image))
	{
		IFileManager::Get().Move(*Final, *Temp, true, true);
	}
}

void UAgentPlayHookSubsystem::WriteTextAtomic(const FString& Path, const FString& Text) const
{
	const FString Temp = Path + TEXT(".tmp");
	if (FFileHelper::SaveStringToFile(Text, *Temp))
	{
		IFileManager::Get().Move(*Path, *Temp, true, true);
	}
}

void UAgentPlayHookSubsystem::WriteStatus(const TCHAR* Word) const
{
	WriteTextAtomic(FilePath(TEXT("status.json")),
		FString::Printf(TEXT("{\"state\":\"%s\",\"turn\":%d,\"frame\":%d,\"game_s\":%.2f}"), Word, TurnNumber, FrameNumber, GameSeconds));
}

void UAgentPlayHookSubsystem::WriteResult(const TCHAR* Outcome) const
{
	const AEllaCharacter* Pawn = Ella.Get();
	const ABrokenMillRoom* Mill = Room.Get();
	float Damage = 0.0f;
	int32 UsefulHits = 0;
	int32 Shots = 0;
	float GuardHp = 0.0f;
	FIntPoint Res = FIntPoint::ZeroValue;
	if (Pawn && Mill)
	{
		Damage = FMath::Max(0.0f, HealthAtStart - AgentPlayTotalHealth(Pawn));
		GuardHp = Mill->GetGuardHp();
		const float HpLost = StartGuardHp - GuardHp;
		const float PerHit = GetDefault<UUmbrellaTuning>()->BrokenMill.FriendlyDamage;
		UsefulHits = HpLost > 0.0f && PerHit > 0.0f ? FMath::CeilToInt(HpLost / PerHit) : 0;
		Shots = Pawn->GetAttack()->GetShotsFired() - ShotsAtStart;
	}
	if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
	{
		Res = GEngine->GameViewport->Viewport->GetSizeXY();
	}
	const bool bComparison = Mill && Mill->GetGuardProfile() == EMillGuardProfile::Comparison;
	const float Play = GameSeconds;
	FString Json = TEXT("{");
	Json += FString::Printf(TEXT("\"outcome\":%s,"), *AgentPlayJsonString(Outcome));
	Json += FString::Printf(TEXT("\"res\":\"%dx%d\",\"debug\":0,\"health\":\"%s\",\"profile\":\"%s\","), Res.X, Res.Y, bLow ? TEXT("low") : TEXT("healthy"), bComparison ? TEXT("comparison") : TEXT("natural"));
	Json += FString::Printf(TEXT("\"turns\":%d,\"game_s\":%.2f,\"shots\":%d,\"useful_hits\":%d,\"damage\":%.2f,"), Turns, Play, Shots, UsefulHits, Damage);
	Json += FString::Printf(TEXT("\"guard_hp_start\":%.1f,\"guard_hp_end\":%.1f,\"warnings\":%d,"), StartGuardHp, GuardHp, WarningsSeen);
	Json += FString::Printf(TEXT("\"reset_s\":%.2f,\"idle_s\":%.2f,\"idle_share\":%.3f,"), OffLineSeconds, IdleSeconds, AgentPlayRules::IdleShare(IdleSeconds, Play));
	Json += FString::Printf(TEXT("\"teleport_steps\":%d,\"autoaim\":0,\"invuln\":0,\"teleport\":%d}"), TeleportSteps, TeleportSteps > 0 ? 1 : 0);
	WriteTextAtomic(FilePath(TEXT("result.json")), Json);
	UE_LOG(LogUmbrellaElla, Log, TEXT("AGENTPLAY_RESULT %s"), *Json);
}

#else // not a workbench build: the subsystem never exists.

bool UAgentPlayHookSubsystem::ShouldCreateSubsystem(UObject* Outer) const { return false; }
void UAgentPlayHookSubsystem::Initialize(FSubsystemCollectionBase& Collection) { Super::Initialize(Collection); }
void UAgentPlayHookSubsystem::Tick(float DeltaTime) {}
bool UAgentPlayHookSubsystem::IsTickable() const { return false; }
TStatId UAgentPlayHookSubsystem::GetStatId() const { RETURN_QUICK_DECLARE_CYCLE_STAT(UAgentPlayHookSubsystem, STATGROUP_Tickables); }

#endif
