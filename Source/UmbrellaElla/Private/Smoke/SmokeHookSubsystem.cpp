#include "Smoke/SmokeHookSubsystem.h"
#include "Enemy/EnemyTypes.h"
#include "Core/UmbrellaLog.h"
#include "Core/UmbrellaTuning.h"
#include "Core/EllaCharacter.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Art/ArtSlot.h"
#include "Engine/Texture2D.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "InputKeyEventArgs.h"
#include "Motor/EllaMotorComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "Flow/UmbrellaPlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "UnrealClient.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/FileManager.h"
#include "ImageUtils.h"
#include "Widgets/SWindow.h"
#include "SceneView.h"
#include "SceneView.h"
#include "UObject/UnrealType.h"
#include "Misc/Paths.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Encounter/KeeperFightModel.h"
#include "Owl/KeeperOfTime.h"
#include "Owl/KeeperPartComponent.h"
#include "Core/UmbrellaGameMode.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Arena/UmbrellaArena.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "ShaderCompiler.h"
#include "ContentStreaming.h"
#include "AssetCompilingManager.h"
#include "EngineUtils.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/PrimitiveComponent.h"
#include "Materials/MaterialInterface.h"
#include "Engine/Texture.h"

/** Texture parameter every art slot and stand-in material uses (ArtSlot.cpp). */
static const FName SmokeDrawArtParam(TEXT("Art"));
/** Texture parameter of the VFX sheet material (VfxSheetVisual.cpp). */
static const FName SmokeDrawSheetParam(TEXT("Sheet"));

#ifndef UMBRELLAELLA_BUILD_COMMIT
#define UMBRELLAELLA_BUILD_COMMIT "unknown"
#endif

namespace
{

	AUmbrellaPlayerController* FindFlowController(UGameInstance* Instance)
	{
		UWorld* World = Instance ? Instance->GetWorld() : nullptr;
		return World ? Cast<AUmbrellaPlayerController>(UGameplayStatics::GetPlayerController(World, 0)) : nullptr;
	}
}

bool USmokeHookSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	return FString(FCommandLine::Get()).Contains(TEXT("-SmokeQuitAfter="));
}

void USmokeHookSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	InitTime = FApp::GetCurrentTime();
	FParse::Value(FCommandLine::Get(), TEXT("-SmokeQuitAfter="), QuitAfterSeconds);
	FParse::Value(FCommandLine::Get(), TEXT("-SmokeShot="), ShotPath);
	if (!ShotPath.IsEmpty())
	{
		ShotPath = ResolveShotPath(ShotPath, FPaths::ProjectDir());
	}
	int32 RequestedFrames = 0;
	FParse::Value(FCommandLine::Get(), TEXT("-SmokeShotFrames="), RequestedFrames);
	ShotFrames = ResolveShotFrames(RequestedFrames);
	FParse::Value(FCommandLine::Get(), TEXT("-SmokeShotWhen="), ShotWhen);
	FParse::Value(FCommandLine::Get(), TEXT("-SmokeShotMomentFrames="), ShotMomentFrames);
	ShotMomentFrames = FMath::Max(1, ShotMomentFrames);
}

bool USmokeHookSubsystem::IsKeeperShotMoment(const FString& When, EKeeperPhysical Physical, EKeeperStage Stage, bool bGustTravelling)
{
	if (When.IsEmpty())
	{
		return true;
	}
	const bool bWarning = Stage == EKeeperStage::Warning;
	if (When.Equals(TEXT("Talon"), ESearchCase::IgnoreCase))
	{
		return bWarning && Physical == EKeeperPhysical::Talon;
	}
	if (When.Equals(TEXT("Cast"), ESearchCase::IgnoreCase))
	{
		return bWarning && (Physical == EKeeperPhysical::FrontCast || Physical == EKeeperPhysical::MiddleCurve || Physical == EKeeperPhysical::RearTwoStage);
	}
	if (When.Equals(TEXT("GustWarning"), ESearchCase::IgnoreCase))
	{
		return bWarning && Physical == EKeeperPhysical::Gust;
	}
	if (When.Equals(TEXT("GustTravel"), ESearchCase::IgnoreCase))
	{
		return bGustTravelling;
	}
	return false;
}

bool USmokeHookSubsystem::IsKeeperMomentNow() const
{
	if (ShotWhen.IsEmpty())
	{
		return true;
	}
	const UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	const UEncounterDirectorSubsystem* Director = World ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr;
	if (!Director || Director->GetState() != EEncounterState::Active)
	{
		return false;
	}
	const FKeeperFightModel& Model = Director->GetModel();
	return IsKeeperShotMoment(ShotWhen, Model.GetPhysical(), Model.GetStage(), Model.IsGustTravelling());
}

void USmokeHookSubsystem::HoldEllaNearClaw(AUmbrellaPlayerController* Flow) const
{
#if UMBRELLAELLA_WORKBENCH
	const UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	const UEncounterDirectorSubsystem* Director = World ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr;
	APawn* Ella = Flow ? Flow->GetPawn() : nullptr;
	if (!Director || !Ella || Director->GetState() != EEncounterState::Active)
	{
		return;
	}
	const FVector2D Claw = Director->GetModel().GetClaw();
	Ella->SetActorLocation(FVector(Claw.X + SmokeClawOffsetX, Ella->GetActorLocation().Y, Claw.Y));
#endif
}

void USmokeHookSubsystem::BreakKeeperWings() const
{
#if UMBRELLAELLA_WORKBENCH
	const UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	const UEncounterDirectorSubsystem* Director = World ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr;
	if (!Director || Director->GetState() != EEncounterState::Active || Director->GetPhase() != EKeeperPhase::Wings)
	{
		return;
	}
	// Straight to the mechanisms (their chain casts), through the part's own hit path; ignored until damage is let in.
	if (UKeeperPartComponent* Wings = Director->GetKeeper() ? Director->GetKeeper()->GetPartComponent(EKeeperPart::Wings) : nullptr)
	{
		FUmbrellaShotSpec Shot;
		Shot.Kind = EUmbrellaShotKind::PlayerBlast;
		Shot.Damage = SmokeBreakDamage;
		Wings->ReceiveShot(Shot, FVector::ZeroVector);
	}
#endif
}

void USmokeHookSubsystem::LogShotKeeper() const
{
	const UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	const UEncounterDirectorSubsystem* Director = World ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr;
	if (!Director)
	{
		return;
	}
	const FKeeperFightModel& Model = Director->GetModel();
	UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_KEEPER active=%d phase=%d physical=%d stage=%d gust_travelling=%d when=%s"),
		Director->GetState() == EEncounterState::Active ? 1 : 0, static_cast<int32>(Director->GetPhase()), static_cast<int32>(Model.GetPhysical()),
		static_cast<int32>(Model.GetStage()), Model.IsGustTravelling() ? 1 : 0, ShotWhen.IsEmpty() ? TEXT("-") : *ShotWhen);
}

bool USmokeHookSubsystem::IsShotDue(bool bLevelReady, int32 FramesSinceReady, int32 RequiredFrames)
{
	return bLevelReady && FramesSinceReady >= RequiredFrames;
}

bool USmokeHookSubsystem::IsShotReady(int32 PendingShaderJobs, int32 StreamingResources, int32 PendingAssets, bool bPlayerAlive)
{
	return PendingShaderJobs <= 0 && StreamingResources <= 0 && PendingAssets <= 0 && bPlayerAlive;
}

FString USmokeHookSubsystem::ResolveShotPath(const FString& Path, const FString& ProjectDir)
{
	if (Path.IsEmpty() || !FPaths::IsRelative(Path))
	{
		return Path;
	}
	return FPaths::ConvertRelativePathToFull(ProjectDir, Path);
}

bool USmokeHookSubsystem::HasEnemyFamilyName(const FString& Name, EEnemyType& OutType)
{
	if (Name.Equals(TEXT("Roadwarden"), ESearchCase::IgnoreCase))
	{
		OutType = EEnemyType::Roadwarden;
		return true;
	}
	if (Name.Equals(TEXT("Floodstrider"), ESearchCase::IgnoreCase))
	{
		OutType = EEnemyType::Floodstrider;
		return true;
	}
	if (Name.Equals(TEXT("SkyCourier"), ESearchCase::IgnoreCase))
	{
		OutType = EEnemyType::SkyCourier;
		return true;
	}
	return false;
}

int32 USmokeHookSubsystem::ResolveShotFrames(int32 Requested)
{
	return Requested >= 1 ? Requested : DefaultShotFrames;
}

void USmokeHookSubsystem::ApplySceneSwitches()
{
#if UMBRELLAELLA_WORKBENCH
	bSceneApplied = true;
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	AUmbrellaPlayerController* Flow = FindFlowController(GetGameInstance());
	if (!World || !Flow)
	{
		return;
	}
	if (FParse::Param(FCommandLine::Get(), TEXT("SmokeKeeper")))
	{
		UEncounterDirectorSubsystem* Director = World->GetSubsystem<UEncounterDirectorSubsystem>();
		if (Director && Director->GetState() != EEncounterState::Active)
		{
			if (AUmbrellaGameMode* Mode = World->GetAuthGameMode<AUmbrellaGameMode>())
			{
				Mode->BeginFight(Flow);
			}
		}
		UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_SCENE keeper=%d phase=%d"), Director && Director->GetState() == EEncounterState::Active ? 1 : 0,
			Director ? static_cast<int32>(Director->GetPhase()) : -1);
	}
	FString Family;
	if (FParse::Value(FCommandLine::Get(), TEXT("-SmokeEnemy="), Family))
	{
		EEnemyType Type = EEnemyType::Roadwarden;
		const APawn* Ella = Flow->GetPawn();
		if (HasEnemyFamilyName(Family, Type) && Ella)
		{
			const FVector At = Ella->GetActorLocation() + FVector(SmokeEnemyOffsetX, 0.0, 0.0);
			AUmbrellaEnemy* Enemy = World->SpawnActor<AUmbrellaEnemy>(AUmbrellaEnemy::StaticClass(), FTransform(At));
			if (Enemy)
			{
				Enemy->Configure(Type, EEnemyGender::Male, EUmbrellaShotKind::EnemyRed);
			}
			UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_SCENE enemy=%s spawned=%d"), *Family, Enemy ? 1 : 0);
		}
		else
		{
			UE_LOG(LogUmbrellaElla, Warning, TEXT("SMOKE_SCENE enemy=%s unknown family or no player"), *Family);
		}
	}
#else
	bSceneApplied = true;
#endif
}

bool USmokeHookSubsystem::IsTickable() const
{
	return !IsTemplate() && Stage != EStage::Finished;
}

TStatId USmokeHookSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USmokeHookSubsystem, STATGROUP_Tickables);
}

float USmokeHookSubsystem::ComputeLowFps(const TArray<float>& Frames, float LowShare)
{
	if (Frames.IsEmpty())
	{
		return 0.0f;
	}
	TArray<float> Sorted = Frames;
	Sorted.Sort([](float A, float B) { return A > B; });
	const int32 Count = FMath::Max(1, FMath::CeilToInt(Sorted.Num() * LowShare));
	double Sum = 0.0;
	for (int32 Index = 0; Index < Count; ++Index)
	{
		Sum += Sorted[Index];
	}
	const double MeanSlow = Sum / Count;
	return MeanSlow > 0.0 ? static_cast<float>(1.0 / MeanSlow) : 0.0f;
}

USmokeHookSubsystem::EInputStep USmokeHookSubsystem::NextInputStep(EInputStep Step, double InStepSeconds, double SinceStartSeconds, float ShotDelaySeconds, bool bHasMotor, bool bHasController)
{
	switch (Step)
	{
	case EInputStep::Idle:
		if (!bHasController || SinceStartSeconds < ShotDelaySeconds + InputGapSeconds)
		{
			return Step;
		}
		return bHasMotor ? EInputStep::KeyHold : EInputStep::Done;
	case EInputStep::KeyHold:
		return InStepSeconds >= InputHoldSeconds ? EInputStep::KeyGap : Step;
	case EInputStep::KeyGap:
		return InStepSeconds >= InputGapSeconds ? EInputStep::PadHold : Step;
	case EInputStep::PadHold:
		return InStepSeconds >= InputHoldSeconds ? EInputStep::PadDash : Step;
	case EInputStep::PadDash:
		return InStepSeconds >= InputHoldSeconds ? EInputStep::PadGap : Step;
	case EInputStep::PadGap:
		return InStepSeconds >= InputGapSeconds ? EInputStep::Done : Step;
	case EInputStep::Done:
	default:
		return EInputStep::Done;
	}
}

bool USmokeHookSubsystem::IsPixelInFrame(bool bProjected, const FVector2D& Pixel, const FVector2D& ViewSize)
{
	return bProjected && ViewSize.X > 0.0 && ViewSize.Y > 0.0 && Pixel.X >= 0.0 && Pixel.Y >= 0.0 && Pixel.X < ViewSize.X && Pixel.Y < ViewSize.Y;
}

void USmokeHookSubsystem::LogShotView(AUmbrellaPlayerController* Flow) const
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (!Flow || !World)
	{
		UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_VIEW controller=0"));
		return;
	}
	int32 ViewW = 0;
	int32 ViewH = 0;
	Flow->GetViewportSize(ViewW, ViewH);
	const FVector2D ViewSize(ViewW, ViewH);
	const AActor* Target = Flow->GetViewTarget();
	const FVector Cam = Flow->PlayerCameraManager ? Flow->PlayerCameraManager->GetCameraLocation() : FVector::ZeroVector;
	const APawn* Pawn = Flow->GetPawn();
	FVector2D EllaPx(-1.0, -1.0);
	const bool bEllaProjected = Pawn && Flow->ProjectWorldLocationToScreen(Pawn->GetActorLocation(), EllaPx);
	TActorIterator<AUmbrellaArena> ArenaIt(World);
	const AUmbrellaArena* Arena = ArenaIt ? *ArenaIt : nullptr;
	FVector2D ArenaPx(-1.0, -1.0);
	const bool bArenaProjected = Arena && Flow->ProjectWorldLocationToScreen(Arena->LocalPoint(0.5f, 0.5f), ArenaPx);
	UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_VIEW map=%s view_target=%s cam=%s ella=%d ella_px=%.0f,%.0f ella_in_frame=%d arena=%d arena_px=%.0f,%.0f arena_in_frame=%d w=%d h=%d"),
		*World->GetMapName(), Target ? *Target->GetName() : TEXT("none"), *Cam.ToCompactString(), Pawn ? 1 : 0, EllaPx.X, EllaPx.Y,
		IsPixelInFrame(bEllaProjected, EllaPx, ViewSize) ? 1 : 0, Arena ? 1 : 0, ArenaPx.X, ArenaPx.Y,
		IsPixelInFrame(bArenaProjected, ArenaPx, ViewSize) ? 1 : 0, ViewW, ViewH);
	LogShotDraws(Flow, ViewSize);
}

void USmokeHookSubsystem::LogShotDraws(AUmbrellaPlayerController* Flow, const FVector2D& ViewSize) const
{
	UWorld* World = Flow ? Flow->GetWorld() : nullptr;
	if (!World)
	{
		return;
	}
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		const AActor* Actor = *It;
		if (!Actor || Actor->IsHidden())
		{
			continue;
		}
		TInlineComponentArray<UPrimitiveComponent*> Prims(Actor);
		for (const UPrimitiveComponent* Prim : Prims)
		{
			if (!Prim || !Prim->IsRegistered() || !Prim->IsVisible() || Prim->bHiddenInGame)
			{
				continue;
			}
			const FBox Box = Prim->Bounds.GetBox();
			FVector2D Min(TNumericLimits<double>::Max(), TNumericLimits<double>::Max());
			FVector2D Max(-TNumericLimits<double>::Max(), -TNumericLimits<double>::Max());
			bool bAny = false;
			for (const double X : { Box.Min.X, Box.Max.X })
			{
				for (const double Y : { Box.Min.Y, Box.Max.Y })
				{
					for (const double Z : { Box.Min.Z, Box.Max.Z })
					{
						FVector2D Px;
						if (Flow->ProjectWorldLocationToScreen(FVector(X, Y, Z), Px))
						{
							bAny = true;
							Min = FVector2D::Min(Min, Px);
							Max = FVector2D::Max(Max, Px);
						}
					}
				}
			}
			if (!bAny || Max.X < 0.0 || Max.Y < 0.0 || Min.X >= ViewSize.X || Min.Y >= ViewSize.Y)
			{
				continue;
			}
			const UMaterialInterface* Mat = Prim->GetNumMaterials() > 0 ? Prim->GetMaterial(0) : nullptr;
			UTexture* ArtTexture = nullptr;
			if (Mat)
			{
				if (!Mat->GetTextureParameterValue(FHashedMaterialParameterInfo(SmokeDrawArtParam), ArtTexture))
				{
					Mat->GetTextureParameterValue(FHashedMaterialParameterInfo(SmokeDrawSheetParam), ArtTexture);
				}
			}
			const FString TextureNames = ArtTexture ? ArtTexture->GetName() : FString(TEXT("none"));
			UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_DRAW actor=%s class=%s comp=%s y=%.0f..%.0f px=%.0f,%.0f..%.0f,%.0f mat=%s tex=%s"),
				*Actor->GetName(), *Actor->GetClass()->GetName(), *Prim->GetName(), Box.Min.Y, Box.Max.Y, Min.X, Min.Y, Max.X, Max.Y,
				Mat ? *Mat->GetName() : TEXT("none"), *TextureNames);
		}
	}
}

void USmokeHookSubsystem::Tick(float DeltaTime)
{
	AUmbrellaPlayerController* Flow = FindFlowController(GetGameInstance());

	if (Stage == EStage::WaitingForStart)
	{
		if (Flow && !bSelectedStart && Flow->GetScreen() == EFlowScreen::Title)
		{
			bSelectedStart = true;
			Flow->RequestSmokeStart();
		}
		if (Flow && Flow->GetScreen() == EFlowScreen::Playing)
		{
			Stage = EStage::Running;
			StartTime = FApp::GetCurrentTime();
			LoadMs = static_cast<float>(StartTime - InitTime) * MillisecondsPerSecond;
			UE_LOG(LogUmbrellaElla, Log, TEXT("%s"), *BuildEffectiveLine(TEXT("start"), nullptr));
		}
		return;
	}

	FrameSeconds.Add(DeltaTime);
	const float Elapsed = static_cast<float>(FApp::GetCurrentTime() - StartTime);
	if (!bSceneApplied)
	{
		ApplySceneSwitches();
	}
#if UMBRELLAELLA_WORKBENCH
	// -SmokeHurt: hold Ella in her Hurt look (what a hit shows) so the shot captures it.
	if (FParse::Param(FCommandLine::Get(), TEXT("SmokeHurt")))
	{
		const AEllaCharacter* Hurt = Flow ? Cast<AEllaCharacter>(Flow->GetPawn()) : nullptr;
		UEllaAnimPresenterComponent* Look = Hurt ? Hurt->GetAnimPresenter() : nullptr;
		if (Look && Look->GetVisualState() != EEllaVisualState::Hurt)
		{
			Look->SetVisualState(EEllaVisualState::Hurt);
			UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_SCENE hurt=1"));
			for (const TCHAR* Visual : { TEXT("ella-state:Hurt"), TEXT("ella-state:Idle") })
			{
				const FArtSlotRow* Row = ArtSlot::Find(Visual);
				const UTexture2D* T = Row ? ArtSlot::LoadTexture(*Row) : nullptr;
				if (T)
				{
					UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_TEX %s %s size=%dx%d comp=%d noalpha=%d srgb=%d pf=%s group=%d"), Visual, *T->GetName(), T->GetSizeX(), T->GetSizeY(),
						static_cast<int32>(T->CompressionSettings), T->CompressionNoAlpha ? 1 : 0, T->SRGB ? 1 : 0, GetPixelFormatString(T->GetPixelFormat()), static_cast<int32>(T->LODGroup));
				}
			}
		}
	}
#endif
	{
		const int32 ShaderJobs = GShaderCompilingManager ? GShaderCompilingManager->GetNumRemainingJobs() : 0;
		const int32 Streaming = IStreamingManager::Get().GetTextureStreamingManager().GetNumWantingResources();
		const int32 Assets = FAssetCompilingManager::Get().GetNumRemainingAssets();
		const APawn* Pawn = Flow ? Flow->GetPawn() : nullptr;
		const bool bAlive = Pawn && IsValid(Pawn) && Flow->GetScreen() == EFlowScreen::Playing;
		if (IsShotReady(ShaderJobs, Streaming, Assets, bAlive))
		{
			++FramesSinceReady;
			if (!bShotReadyLogged)
			{
				bShotReadyLogged = true;
				UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_SHOT_READY at_s=%.1f"), Elapsed);
			}
		}
		else
		{
			// Anything pending again restarts the count: the frames must be consecutive and settled.
			FramesSinceReady = 0;
		}
	}
	const bool bShotPending = !ShotPath.IsEmpty() && !bShotChecked && Elapsed < QuitAfterSeconds + ShotMaxWaitSeconds;

	if (!bShotTaken && FParse::Param(FCommandLine::Get(), TEXT("SmokeHoldNearClaw")))
	{
		HoldEllaNearClaw(Flow);
	}
	if (!bShotTaken && FParse::Param(FCommandLine::Get(), TEXT("SmokeKeeperBreakWings")))
	{
		BreakKeeperWings();
	}
	MomentFrames = IsKeeperMomentNow() ? MomentFrames + 1 : 0;
	// A -SmokeShotWhen moment is short (a 1 s warning) and new effects stream in as it starts, which restarts the settled
	// count: once the scene has settled one time, the moment itself is the trigger.
	const bool bDue = ShotWhen.IsEmpty() ? IsShotDue(true, FramesSinceReady, ShotFrames) : (bShotReadyLogged && MomentFrames >= ShotMomentFrames);
	if (!bShotTaken && !ShotPath.IsEmpty() && bDue)
	{
		bShotTaken = true;
		// Whole window (bars and UI): bShowUI=true takes the Slate window, not the bare scene render target.
		FScreenshotRequest::RequestScreenshot(ShotPath, true, false);
		ShotRequestedAt = FApp::GetCurrentTime();
		const FVector2D Size = GEngine && GEngine->GameViewport ? FVector2D(GEngine->GameViewport->Viewport->GetSizeXY()) : FVector2D::ZeroVector;
		UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_SHOT at_s=%.1f frames=%d w=%d h=%d"), Elapsed, FramesSinceReady, static_cast<int32>(Size.X), static_cast<int32>(Size.Y));
		LogShotView(Flow);
		LogShotKeeper();
	}

	if (bShotTaken && !bShotChecked && FApp::GetCurrentTime() - ShotRequestedAt >= ShotWriteWaitSeconds)
	{
		bShotChecked = true;
		if (!IFileManager::Get().FileExists(*ShotPath))
		{
			// The engine request wrote nothing (packaged Mac): read the Slate window back ourselves.
			SaveWindowShotDirect();
		}
		UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_SHOT_FILE written=%d path_bytes=%lld"), IFileManager::Get().FileExists(*ShotPath) ? 1 : 0,
			IFileManager::Get().FileSize(*ShotPath));
	}

	if (!bShotPending)
	{
		TickInputCheck(Flow);
	}

	if (FParse::Param(FCommandLine::Get(), TEXT("SmokePlaytest")))
	{
		if (!Playtest)
		{
			Playtest = MakeUnique<FPlaytestRun>();
		}
		// Start once the shot is out and the input check is over, so neither disturbs the other.
		if (!bPlaytestStarted && (ShotPath.IsEmpty() || bShotChecked) && InputStep == EInputStep::Done && Flow && Flow->GetScreen() != EFlowScreen::Defeat)
		{
			bPlaytestStarted = true;
			Playtest->Start(GetWorld());
		}
		else if (bPlaytestStarted && !Playtest->IsDone())
		{
			Playtest->Advance(DeltaTime);
		}
	}
	const bool bPlaytestSettled = !Playtest || (bPlaytestStarted && Playtest->IsDone());

	const bool bInputSettled = InputStep == EInputStep::Done && bPlaytestSettled;
	const float GraceSeconds = Playtest ? InputGraceSeconds + FPlaytestRun::HazRunSeconds + FPlaytestRun::PlaytestSetupGraceSeconds : InputGraceSeconds;
	if (Flow && Flow->GetScreen() == EFlowScreen::Defeat && (bInputSettled || Elapsed >= QuitAfterSeconds + GraceSeconds))
	{
		LogEnd(TEXT("fail"));
	}
	else if (Flow && (Flow->GetScreen() == EFlowScreen::Story || Flow->GetScreen() == EFlowScreen::Credits) && (bInputSettled || Elapsed >= QuitAfterSeconds + GraceSeconds))
	{
		LogEnd(TEXT("survived"));
	}
	else if (Elapsed >= QuitAfterSeconds && !bShotPending && (bInputSettled || Elapsed >= QuitAfterSeconds + GraceSeconds))
	{
		LogEnd(TEXT("quit"));
	}
}

void USmokeHookSubsystem::SaveWindowShotDirect()
{
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
	if (FSlateApplication::Get().TakeScreenshot(Window.ToSharedRef(), Bitmap, Size) && Bitmap.Num() > 0)
	{
		for (FColor& Color : Bitmap)
		{
			Color.A = OpaqueAlpha;
		}
		const FImageView Image(Bitmap.GetData(), Size.X, Size.Y);
		FImageUtils::SaveImageByExtension(*ShotPath, Image);
	}
}

void USmokeHookSubsystem::LogEnd(const TCHAR* Outcome)
{
	Stage = EStage::Finished;
	UE_LOG(LogUmbrellaElla, Log, TEXT("%s"), *BuildEffectiveLine(TEXT("end"), Outcome));

	const FFlowTuning& Tuning = GetDefault<UUmbrellaTuning>()->Flow;
	float WorstSeconds = 0.0f;
	for (const float Seconds : FrameSeconds)
	{
		WorstSeconds = FMath::Max(WorstSeconds, Seconds);
	}

	FIntPoint Window = FIntPoint::ZeroValue;
	FIntPoint View = FIntPoint::ZeroValue;
	bool bFullscreen = false;
	if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
	{
		UGameViewportClient* Client = GEngine->GameViewport;
		Window = Client->Viewport->GetSizeXY();
		bFullscreen = Client->IsFullScreenViewport();
		ULocalPlayer* Local = GetGameInstance()->GetFirstGamePlayer();
		FSceneViewProjectionData Projection;
		if (Local && Local->GetProjectionData(Client->Viewport, Projection))
		{
			View = Projection.GetConstrainedViewRect().Size();
		}
	}
	const float Aspect = View.Y > 0 ? static_cast<float>(View.X) / View.Y : 0.0f;

	UE_LOG(LogUmbrellaElla, Log,
		TEXT("SMOKE_OK map=%s fps=%.1f worst_ms=%.1f commit=%s input=%s input_vz=%.1f gamepad=%s gp_vx=%.1f gp_attack_vz=%.1f res=%dx%d win=%s textpx=%d load_ms=%.0f workbench=%d view=%dx%d aspect=%.3f debugdraw=0"),
		*UGameplayStatics::GetCurrentLevelName(this), ComputeLowFps(FrameSeconds, Tuning.SmokeLowShare), WorstSeconds * MillisecondsPerSecond,
		ANSI_TO_TCHAR(UMBRELLAELLA_BUILD_COMMIT), bInputOk ? TEXT("ok") : TEXT("none"), InputVz, bGamepadOk ? TEXT("ok") : TEXT("none"), PadPeakVx, PadAttackVz, Window.X, Window.Y, bFullscreen ? TEXT("fullscreen") : TEXT("windowed"),
		Tuning.MenuFontSize, LoadMs, UMBRELLAELLA_WORKBENCH, View.X, View.Y, Aspect);

	if (QuitAfterSeconds > 0.0f)
	{
		FPlatformMisc::RequestExit(false);
	}
}

FString USmokeHookSubsystem::BuildEffectiveLine(const TCHAR* At, const TCHAR* Outcome) const
{
	FString Line = FString::Printf(TEXT("SMOKE_EFFECTIVE at=%s"), At);
	if (Outcome)
	{
		Line += FString::Printf(TEXT(" outcome=%s"), Outcome);
	}
	Line += FString::Printf(TEXT(" commit=%s workbench=%d platform=%s manifest=%s"), ANSI_TO_TCHAR(UMBRELLAELLA_BUILD_COMMIT),
		UMBRELLAELLA_WORKBENCH, *UGameplayStatics::GetPlatformName(), GetFeatureManifestVersion());

	// Every reflected field of every struct member of UUmbrellaTuning, never a key list.
	const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
	for (TFieldIterator<FStructProperty> Member(UUmbrellaTuning::StaticClass()); Member; ++Member)
	{
		const void* StructValue = Member->ContainerPtrToValuePtr<void>(Tuning);
		for (TFieldIterator<FProperty> Field(Member->Struct); Field; ++Field)
		{
			FString Value;
			Field->ExportTextItem_Direct(Value, Field->ContainerPtrToValuePtr<void>(StructValue), nullptr, nullptr, PPF_None);
			Line += FString::Printf(TEXT(" %s.%s=%s"), *Member->Struct->GetName(), *Field->GetName(), *Value);
		}
	}
	for (int32 Index = 0; Index < static_cast<int32>(EFeatureId::Count); ++Index)
	{
		const EFeatureId Id = static_cast<EFeatureId>(Index);
		Line += FString::Printf(TEXT(" %s.enabled=%d"), GetFeatureRuleId(Id), IsFeatureEnabled(Id) ? 1 : 0);
	}
	return Line;
}

bool USmokeHookSubsystem::HasMotor(FVector& OutVelocity) const
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	const AEllaCharacter* Ella = World ? Cast<AEllaCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)) : nullptr;
	if (!Ella || !Ella->GetMotor())
	{
		return false;
	}
	OutVelocity = Ella->GetMotor()->GetVelocity();
	return true;
}

bool USmokeHookSubsystem::CanSendKey(APlayerController* Controller, const FKey& Key, EInputEvent Event, float Amount) const
{
	if (!Controller)
	{
		return false;
	}
	FViewport* Viewport = GEngine && GEngine->GameViewport ? GEngine->GameViewport->Viewport : nullptr;
	const FInputDeviceId Device = FInputDeviceId::CreateFromInternalId(0);
	if (Event == IE_Axis)
	{
		return Controller->InputKey(FInputKeyEventArgs(Viewport, Device, Key, Amount, 0.0f, 1, 0));
	}
	return Controller->InputKey(FInputKeyEventArgs(Viewport, Device, Key, Event, 0));
}

void USmokeHookSubsystem::TickInputCheck(AUmbrellaPlayerController* Flow)
{
	const FFlowTuning& Tuning = GetDefault<UUmbrellaTuning>()->Flow;
	const double Now = FApp::GetCurrentTime();
	const double InStep = Now - InputStepStart;
	FVector Velocity = FVector::ZeroVector;
	const bool bHasMotor = HasMotor(Velocity);
	APlayerController* Controller = Flow;

	const double SinceStart = Now - StartTime;
	const EInputStep Next = NextInputStep(InputStep, InStep, SinceStart, Tuning.SmokeShotDelaySeconds, bHasMotor, Controller != nullptr);
	if (InputStep == EInputStep::PadDash)
	{
		PadPeakVx = FMath::Max(PadPeakVx, static_cast<float>(Velocity.X));
	}
	if (Next == InputStep)
	{
		return;
	}

	switch (InputStep)
	{
	case EInputStep::Idle:
		if (Next == EInputStep::KeyHold)
		{
			CanSendKey(Controller, EKeys::J, IE_Pressed, 1.0f);
		}
		break;
	case EInputStep::KeyHold:
		InputVz = static_cast<float>(Velocity.Z);
		bInputOk = InputVz < 0.0f;
		CanSendKey(Controller, EKeys::J, IE_Released, 0.0f);
		UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_INPUT key=J action=Shoot vz=%.1f"), InputVz);
		break;
	case EInputStep::KeyGap:
		CanSendKey(Controller, EKeys::Gamepad_RightTrigger, IE_Pressed, 1.0f);
		CanSendKey(Controller, EKeys::Gamepad_LeftX, IE_Axis, 1.0f);
		break;
	case EInputStep::PadHold:
		PadAttackVz = static_cast<float>(Velocity.Z);
		// Falling, stick right: Hop is a dash by input direction, so it must move her right.
		CanSendKey(Controller, EKeys::Gamepad_FaceButton_Bottom, IE_Pressed, 1.0f);
		CanSendKey(Controller, EKeys::Gamepad_FaceButton_Bottom, IE_Released, 0.0f);
		break;
	case EInputStep::PadDash:
		CanSendKey(Controller, EKeys::Gamepad_LeftX, IE_Axis, 0.0f);
		CanSendKey(Controller, EKeys::Gamepad_RightTrigger, IE_Released, 0.0f);
		bGamepadOk = PadAttackVz < 0.0f && PadPeakVx > 0.0f;
		UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_GAMEPAD attack_vz=%.1f peak_vx=%.1f"), PadAttackVz, PadPeakVx);
		break;
	case EInputStep::PadGap:
	case EInputStep::Done:
	default:
		break;
	}
	InputStep = Next;
	InputStepStart = Now;
}
