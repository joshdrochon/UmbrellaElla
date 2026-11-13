#include "Smoke/SmokeHookSubsystem.h"
#include "Core/UmbrellaLog.h"
#include "Core/UmbrellaTuning.h"
#include "Core/EllaCharacter.h"
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

void USmokeHookSubsystem::Tick(float DeltaTime)
{
	const FFlowTuning& Tuning = GetDefault<UUmbrellaTuning>()->Flow;
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

	if (!bShotTaken && !ShotPath.IsEmpty() && Elapsed >= Tuning.SmokeShotDelaySeconds)
	{
		bShotTaken = true;
		// Whole window (bars and UI): bShowUI=true takes the Slate window, not the bare scene render target.
		FScreenshotRequest::RequestScreenshot(ShotPath, true, false);
		ShotRequestedAt = FApp::GetCurrentTime();
		const FVector2D Size = GEngine && GEngine->GameViewport ? FVector2D(GEngine->GameViewport->Viewport->GetSizeXY()) : FVector2D::ZeroVector;
		UE_LOG(LogUmbrellaElla, Log, TEXT("SMOKE_SHOT at_s=%.1f w=%d h=%d"), Elapsed, static_cast<int32>(Size.X), static_cast<int32>(Size.Y));
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

	TickInputCheck(Flow);

	const bool bInputSettled = InputStep == EInputStep::Done;
	if (Flow && Flow->GetScreen() == EFlowScreen::Defeat && (bInputSettled || Elapsed >= QuitAfterSeconds + InputGraceSeconds))
	{
		LogEnd(TEXT("fail"));
	}
	else if (Flow && (Flow->GetScreen() == EFlowScreen::Story || Flow->GetScreen() == EFlowScreen::Credits) && (bInputSettled || Elapsed >= QuitAfterSeconds + InputGraceSeconds))
	{
		LogEnd(TEXT("survived"));
	}
	else if (Elapsed >= QuitAfterSeconds && (bInputSettled || Elapsed >= QuitAfterSeconds + InputGraceSeconds))
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
			Color.A = 255;
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
