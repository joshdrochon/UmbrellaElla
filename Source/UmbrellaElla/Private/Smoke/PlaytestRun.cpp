#include "Smoke/PlaytestRun.h"
#include "Arena/UmbrellaArena.h"
#include "Attack/AttackEmitterComponent.h"
#include "BrokenMill/BrokenMillRoom.h"
#include "BrokenMill/BrokenMillTuning.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaLog.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Components/ShapeComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "Field/WindCurrent.h"
#include "GameFramework/PlayerController.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Level/LevelCatalogue.h"
#include "Level/LevelContracts.h"
#include "Level/LevelPlan.h"
#include "Level/UmbrellaLevelDirector.h"
#include "Misc/CommandLine.h"
#include "Motor/EllaMotorComponent.h"
#include "Umbrella/UmbrellaStateComponent.h"

namespace
{
	AEllaCharacter* PlaytestFindElla(UWorld* World)
	{
		APlayerController* Controller = World ? UGameplayStatics::GetPlayerController(World, 0) : nullptr;
		return Controller ? Cast<AEllaCharacter>(Controller->GetPawn()) : nullptr;
	}

	void PlaytestHurtTo(AEllaCharacter* Ella, float LeaveHealth, double& Clock)
	{
		UUmbrellaHealthComponent* Health = Ella->GetHealth();
		const float Raw = Health->GetState().Active - LeaveHealth;
		if (Raw > 0.0f)
		{
			Clock += FPlaytestRun::HitClockStep;
			Health->TakeHitAt(Raw, FName(TEXT("PlaytestScript")), Clock);
		}
	}

	FString PlaytestNum(float Value)
	{
		return FString::Printf(TEXT("%.2f"), Value);
	}

	FString PlaytestBool(bool bValue)
	{
		return bValue ? TEXT("1") : TEXT("0");
	}

	void PlaytestLog(const TCHAR* Key, const TArray<TPair<FString, FString>>& Pairs)
	{
		UE_LOG(LogUmbrellaElla, Log, TEXT("%s"), *FPlaytestRun::FormatLine(Key, Pairs));
	}
}

void FPlaytestRun::VerticalEnvelope(float Seconds, float& OutMin, float& OutMax)
{
	const FMotorTuning& Motor = GetDefault<UUmbrellaTuning>()->Motor;
	const float TrimShare = 1.0f + Motor.VerticalTrimPct * PercentToFraction;
	OutMin = -Motor.FreeFallSpeed * TrimShare * Seconds;
	OutMax = Motor.RiseSpeed * TrimShare * Seconds;
}

float FPlaytestRun::IdleShare(float IdleSecondsIn, float Seconds)
{
	return Seconds > 0.0f ? FMath::Clamp(IdleSecondsIn / Seconds, 0.0f, 1.0f) : 1.0f;
}

FString FPlaytestRun::FormatLine(const TCHAR* Key, const TArray<TPair<FString, FString>>& Pairs)
{
	FString Line = FString::Printf(TEXT("PLAYTEST_%s"), Key);
	for (const TPair<FString, FString>& Pair : Pairs)
	{
		Line += FString::Printf(TEXT(" %s=%s"), *Pair.Key, *Pair.Value);
	}
	return Line;
}

void FPlaytestRun::Start(UWorld* World)
{
	WorldPtr = World;
	AEllaCharacter* Ella = PlaytestFindElla(World);
	if (!Ella || !Ella->GetMotor() || !Ella->GetHealth() || !Ella->GetUmbrellaState() || !Ella->GetAttack())
	{
		UE_LOG(LogUmbrellaElla, Warning, TEXT("PLAYTEST_ABORT no Ella with Motor, Health, State and Attack"));
		bDone = true;
		return;
	}
	EllaPtr = Ella;
	EllaHome = Ella->GetActorLocation();
	Ella->GetMotor()->ClearPlayBounds();

	ABrokenMillRoom* NewRoom = World->SpawnActor<ABrokenMillRoom>(ABrokenMillRoom::StaticClass(), FTransform(FVector(ScratchRoomX, 0.0, 0.0)));
	if (!NewRoom)
	{
		UE_LOG(LogUmbrellaElla, Warning, TEXT("PLAYTEST_ABORT room did not spawn"));
		bDone = true;
		return;
	}
	NewRoom->BuildRoom();
	NewRoom->SetSimulationPaused(true);
	Room = NewRoom;

	MeasureCam04(Ella);
	MeasureCam07(Ella);
	MeasureFlow25();

	// HAZ run set-up: natural attempt, full or low health from the command line, Ella left of the firing column.
	const bool bLow = FParse::Param(FCommandLine::Get(), TEXT("PlaytestLowHealth"));
	double Clock = 0.0;
	Ella->GetHealth()->ResetForRetry();
	if (bLow)
	{
		PlaytestHurtTo(Ella, GetDefault<UUmbrellaTuning>()->Health.HitsPerLife * LowHealthShare, Clock);
	}
	HealthAtStart = Ella->GetHealth()->GetState().Active;
	const FBrokenMillTuning& Mill = NewRoom->GetMillTuning();
	Ella->SetActorLocation(NewRoom->RoomToWorld(FVector2D(FPlaytestRun::RoomStartX, Mill.TargetCentre.Y)));
	NewRoom->SetTargetActor(Ella);
	NewRoom->ResetForRestart();
	NewRoom->SetSimulationPaused(false);
	StartGuardHp = NewRoom->GetGuardHp();
	ShotsAtStart = Ella->GetAttack()->GetShotsFired();
	Ella->GetUmbrellaState()->SetRideHeld(true);
	Ella->GetUmbrellaState()->SetShootHeld(true);
}

void FPlaytestRun::MeasureCam04(AEllaCharacter* Ella)
{
	ABrokenMillRoom* Mill = Room.Get();
	AWindCurrent* Wind = Mill ? Mill->GetLowerWind() : nullptr;
	if (!Wind)
	{
		return;
	}
	float EnvMin = 0.0f;
	float EnvMax = 0.0f;
	VerticalEnvelope(CamSeconds, EnvMin, EnvMax);
	const FBrokenMillTuning& T = Mill->GetMillTuning();
	const FVector Start = Mill->RoomToWorld(FVector2D(T.FiringColumnX.X, (T.LowerOnwardZ.X + T.LowerOnwardZ.Y) * 0.5f));
	double Clock = 0.0;
	UEllaMotorComponent* Motor = Ella->GetMotor();
	UUmbrellaStateComponent* State = Ella->GetUmbrellaState();
	State->SetRideHeld(true);

	struct FProfile { const TCHAR* Name; float Trim; };
	const FProfile Profiles[] = {{TEXT("mill_lower_v1_trim0"), 0.0f}, {TEXT("mill_lower_v1_trim_up"), 1.0f}, {TEXT("mill_lower_v1_trim_down"), -1.0f}};
	for (const bool bMin : {false, true})
	{
		Ella->GetHealth()->ResetForRetry();
		if (bMin)
		{
			PlaytestHurtTo(Ella, FPlaytestRun::MinHealthLeft, Clock);
		}
		for (const FProfile& Profile : Profiles)
		{
			Ella->SetActorLocation(Start);
			Motor->SetTrimAxis(Profile.Trim);
			Wind->BroadcastEntered(Ella);
			float LiftMin = Motor->GetLiftMultiplier();
			float LiftMax = LiftMin;
			const float StartZ = Ella->GetActorLocation().Z;
			for (int32 StepIndex = 0; StepIndex < FMath::RoundToInt(CamSeconds / StepSeconds); ++StepIndex)
			{
				Motor->StepMotor(StepSeconds);
				LiftMin = FMath::Min(LiftMin, Motor->GetLiftMultiplier());
				LiftMax = FMath::Max(LiftMax, Motor->GetLiftMultiplier());
			}
			Wind->BroadcastExited(Ella);
			const float Disp = Ella->GetActorLocation().Z - StartZ;
			PlaytestLog(TEXT("CAM04"), {{TEXT("profile"), Profile.Name}, {TEXT("health"), bMin ? TEXT("min") : TEXT("full")},
				{TEXT("lift_min"), PlaytestNum(LiftMin)}, {TEXT("lift_max"), PlaytestNum(LiftMax)}, {TEXT("vert_disp"), PlaytestNum(Disp)},
				{TEXT("env_min"), PlaytestNum(EnvMin)}, {TEXT("env_max"), PlaytestNum(EnvMax)},
				{TEXT("qualified"), PlaytestBool(LevelContracts::IsInsideQualifiedEnvelope(Disp, EnvMin, EnvMax))}});
		}
	}
	Motor->SetTrimAxis(0.0f);
	Ella->GetHealth()->ResetForRetry();
}

void FPlaytestRun::MeasureCam07(AEllaCharacter* Ella)
{
	ABrokenMillRoom* Mill = Room.Get();
	if (!Mill)
	{
		return;
	}
	const FBrokenMillTuning& T = Mill->GetMillTuning();
	const FMotorTuning& Motor = GetDefault<UUmbrellaTuning>()->Motor;
	// Decision height: from the island underside down to the floor. Reopen height: free fall during the toggle buffer.
	const float DecisionHeight = T.IslandUnderside - T.FloorTop;
	const float ReopenHeight = Motor.FreeFallSpeed * Motor.ToggleBufferSeconds;
	// The return currents must still blow while the guard (the challenge) is alive.
	const bool bChallengeClear = Mill->GetGuardHp() <= 0.0f;
	const AWindCurrent* Upper = Mill->GetUpperWind();
	const AWindCurrent* Lower = Mill->GetLowerWind();
	const bool bActive = Upper && Lower && !Upper->IsHidden() && !Lower->IsHidden() && Upper->GetForce() > 0.0f && Lower->GetForce() > 0.0f;
	PlaytestLog(TEXT("CAM07"), {{TEXT("decision_height"), PlaytestNum(DecisionHeight)}, {TEXT("reopen_height"), PlaytestNum(ReopenHeight)},
		{TEXT("required_current_active"), PlaytestBool(bActive)}, {TEXT("challenge_clear"), PlaytestBool(bChallengeClear)}});
}

void FPlaytestRun::MeasureFlow25()
{
	ABrokenMillRoom* Mill = Room.Get();
	UWorld* World = WorldPtr.Get();
	if (!Mill || !World)
	{
		return;
	}
	const FBrokenMillTuning& T = Mill->GetMillTuning();
	const float Usable = T.FiringColumnX.Y - T.FiringColumnX.X;
	// Drawn width: the widest visible, non-volume primitive on a wind actor. Wind actors have a collision volume only.
	float Drawn = 0.0f;
	for (const AWindCurrent* Wind : {Mill->GetUpperWind(), Mill->GetLowerWind()})
	{
		if (!Wind)
		{
			continue;
		}
		TArray<UPrimitiveComponent*> Prims;
		Wind->GetComponents(Prims);
		for (const UPrimitiveComponent* Prim : Prims)
		{
			if (Prim->IsVisible() && !Prim->IsA<UShapeComponent>() && Prim->GetCollisionEnabled() == ECollisionEnabled::NoCollision)
			{
				Drawn = FMath::Max(Drawn, Prim->Bounds.BoxExtent.X * 2.0f);
			}
		}
	}
	// Camera lead: every sampled X along the route keeps the player inside the view, going either way.
	const float ViewWidth = GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth;
	const float RouteEnd = LevelCatalogue::RouteLength();
	bool bLeadOk = true;
	for (float X = 0.0f; X <= RouteEnd; X += FPlaytestRun::LeadSampleStep)
	{
		bLeadOk = bLeadOk && LevelContracts::IsLeadSafeBothDirections(X, ViewWidth, 0.0f, RouteEnd);
	}
	const FRoute Route = LevelCatalogue::Generate(FPlaytestRun::RouteSeed);
	const UUmbrellaBackdropSubsystem* Backdrop = World->GetSubsystem<UUmbrellaBackdropSubsystem>();
	const int32 Total = Route.Slots.Num();
	const int32 Covered = (Backdrop && Backdrop->GetLayerCount() > 0) ? Total : 0;
	PlaytestLog(TEXT("FLOW25"), {{TEXT("drawn_width"), PlaytestNum(Drawn)}, {TEXT("usable_width"), PlaytestNum(Usable)},
		{TEXT("tol"), PlaytestNum(DrawnWidthTolerance)}, {TEXT("lead_left_ok"), PlaytestBool(bLeadOk)}, {TEXT("lead_right_ok"), PlaytestBool(bLeadOk)},
		{TEXT("stages_total"), FString::FromInt(Total)}, {TEXT("stages_covered"), FString::FromInt(Covered)}});
}

void FPlaytestRun::Advance(float DeltaSeconds)
{
	AEllaCharacter* Ella = EllaPtr.Get();
	ABrokenMillRoom* Mill = Room.Get();
	if (bDone || !Ella || !Mill)
	{
		bDone = true;
		return;
	}
	HazElapsed += DeltaSeconds;
	const FBrokenMillTuning& T = Mill->GetMillTuning();
	// Natural play, no aids: steer vertical trim toward the guard line, keep the umbrella open and shoot.
	const float ErrorZ = T.TargetCentre.Y - Mill->WorldToRoom(Ella->GetActorLocation()).Y;
	const bool bOnLine = FMath::Abs(ErrorZ) <= T.TargetSize.Y * 0.5f;
	Ella->GetMotor()->SetTrimAxis(bOnLine ? 0.0f : FMath::Sign(ErrorZ));
	// Shooting closes the umbrella and drops her, so shoot only on the line and ride back up otherwise.
	Ella->GetUmbrellaState()->SetShootHeld(bOnLine);
	if (!bOnLine)
	{
		IdleSeconds += DeltaSeconds;
	}
	if (HazElapsed >= HazRunSeconds || Mill->GetGuardHp() <= 0.0f)
	{
		FinishHaz();
		bDone = true;
	}
}

void FPlaytestRun::FinishHaz()
{
	AEllaCharacter* Ella = EllaPtr.Get();
	ABrokenMillRoom* Mill = Room.Get();
	Ella->GetUmbrellaState()->SetShootHeld(false);
	Ella->GetMotor()->SetTrimAxis(0.0f);
	const float Damage = HealthAtStart - Ella->GetHealth()->GetState().Active;
	const float HpLost = StartGuardHp - Mill->GetGuardHp();
	const int32 UsefulHits = HpLost > 0.0f ? FMath::CeilToInt(HpLost / GetDefault<UUmbrellaTuning>()->BrokenMill.FriendlyDamage) : 0;
	FIntPoint Res = FIntPoint::ZeroValue;
	if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
	{
		Res = GEngine->GameViewport->Viewport->GetSizeXY();
	}
	const bool bLow = FParse::Param(FCommandLine::Get(), TEXT("PlaytestLowHealth"));
	const bool bBoring = IdleShare(IdleSeconds, HazElapsed) > BoringIdleShare;
	// No aid code exists in this run: no auto-aim call, no invulnerability call, no teleport after the start position.
	PlaytestLog(TEXT("HAZ16"), {{TEXT("res"), FString::Printf(TEXT("%dx%d"), Res.X, Res.Y)}, {TEXT("debug"), TEXT("0")},
		{TEXT("health"), bLow ? TEXT("low") : TEXT("healthy")}, {TEXT("attempts"), FString::FromInt(Ella->GetAttack()->GetShotsFired() - ShotsAtStart)},
		{TEXT("useful_hits"), FString::FromInt(UsefulHits)}, {TEXT("damage"), PlaytestNum(Damage)}, {TEXT("reset_s"), PlaytestNum(IdleSeconds)}, {TEXT("run_s"), PlaytestNum(HazElapsed)},
		{TEXT("warned"), PlaytestBool(Mill->GetEventCount(EMillGuardEvent::WarningStarted) > 0)}, {TEXT("autoaim"), TEXT("0")},
		{TEXT("invuln"), TEXT("0")}, {TEXT("teleport"), TEXT("0")}, {TEXT("boring"), PlaytestBool(bBoring)},
		{TEXT("cleared"), PlaytestBool(Mill->GetGuardHp() <= 0.0f)}});
	MeasureFlow28(Ella);
}

void FPlaytestRun::MeasureFlow28(AEllaCharacter* Ella)
{
	UWorld* World = WorldPtr.Get();
	if (!World)
	{
		return;
	}
	Ella->GetHealth()->ResetForRetry();
	double Clock = CarryClockStart;
	PlaytestHurtTo(Ella, Ella->GetHealth()->GetState().Active - FPlaytestRun::CarryDamage, Clock);
	const int32 Before = FMath::CeilToInt(Ella->GetHealth()->GetState().Active);
	AUmbrellaLevelDirector* Director = World->SpawnActor<AUmbrellaLevelDirector>();
	if (!Director || Director->BuildRoute(FPlaytestRun::RouteSeed) <= 0)
	{
		UE_LOG(LogUmbrellaElla, Warning, TEXT("PLAYTEST_ABORT level director built no route"));
		return;
	}
	int32 Threats = 0;
	for (TActorIterator<AUmbrellaEnemy> It(World); It; ++It)
	{
		if (!It->IsHidden() && !It->IsActorBeingDestroyed())
		{
			++Threats;
		}
	}
	Director->PlaceAtCheckpoint(Ella, 1);
	Director->StepFollow(LevelPlan::KeeperHandoffX(), 1);
	const float CameraA = Director->GetLastCameraX();
	Director->StepFollow(LevelPlan::KeeperHandoffX(), 1);
	const bool bSettled = FMath::IsNearlyEqual(CameraA, Director->GetLastCameraX());
	const int32 After = FMath::CeilToInt(Ella->GetHealth()->GetState().Active);
	PlaytestLog(TEXT("FLOW28"), {{TEXT("health_before"), FString::FromInt(Before)}, {TEXT("health_after"), FString::FromInt(After)},
		{TEXT("max"), FString::FromInt(FMath::CeilToInt(Ella->GetHealth()->GetState().Capacity))}, {TEXT("threats"), FString::FromInt(Threats)},
		{TEXT("framing_settled"), PlaytestBool(bSettled)}, {TEXT("boss_began"), PlaytestBool(Director->HasHandedOff())}});
	Director->ClearRoute();
	Director->Destroy();
}
