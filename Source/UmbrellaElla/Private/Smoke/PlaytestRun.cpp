#include "Smoke/PlaytestRun.h"
#include "Arena/UmbrellaArena.h"
#include "Attack/AttackEmitterComponent.h"
#include "BrokenMill/BrokenMillRoom.h"
#include "BrokenMill/BrokenMillTuning.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaLog.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Components/CapsuleComponent.h"
#include "Components/ShapeComponent.h"
#include "Components/BoxComponent.h"
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
#include "Umbrella/UmbrellaPlayerIds.h"
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
}

EPlaytestBandExit FPlaytestRun::BandExit(const FVector2D& Root, const FBox2D& Band)
{
	if (Root.X > Band.Max.X)
	{
		return EPlaytestBandExit::Right;
	}
	if (Root.X < Band.Min.X)
	{
		return EPlaytestBandExit::Left;
	}
	if (Root.Y > Band.Max.Y)
	{
		return EPlaytestBandExit::Top;
	}
	if (Root.Y < Band.Min.Y)
	{
		return EPlaytestBandExit::Bottom;
	}
	return EPlaytestBandExit::None;
}

const TCHAR* FPlaytestRun::BandExitName(EPlaytestBandExit Exit)
{
	switch (Exit)
	{
	case EPlaytestBandExit::Right:
		return TEXT("right");
	case EPlaytestBandExit::Left:
		return TEXT("left");
	case EPlaytestBandExit::Top:
		return TEXT("top");
	case EPlaytestBandExit::Bottom:
		return TEXT("bottom");
	default:
		return TEXT("none");
	}
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

bool FPlaytestRun::IsWindRelayRun()
{
	return FParse::Param(FCommandLine::Get(), TEXT("PlaytestWindRelay"));
}

FPlaytestRun::~FPlaytestRun()
{
	StopWindRelay();
}

void FPlaytestRun::StartWindRelay(AEllaCharacter* Ella)
{
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(Ella);
	if (!Bus)
	{
		return;
	}
	RelayBus = Bus;
	const FName ActorName = Ella->GetFName();
	TWeakObjectPtr<UUmbrellaEventBus> WeakBus(Bus);
	auto Relay = [WeakBus, ActorName](const FUmbrellaEvent& Event)
	{
		if (Event.TargetId == ActorName && WeakBus.IsValid())
		{
			FUmbrellaEvent Copy = Event;
			Copy.TargetId = UmbrellaPlayerIds::Ella;
			WeakBus->Broadcast(Copy);
		}
	};
	RelayEnteredHandle = Bus->On(EUmbrellaEventType::WindEntered).AddLambda(Relay);
	RelayExitedHandle = Bus->On(EUmbrellaEventType::WindExited).AddLambda(Relay);
	UE_LOG(LogUmbrellaElla, Warning, TEXT("PLAYTEST_RELAY on actor=%s contract=%s (diagnosis run, not evidence)"), *ActorName.ToString(), *UmbrellaPlayerIds::Ella.ToString());
}

void FPlaytestRun::StopWindRelay()
{
	if (UUmbrellaEventBus* Bus = RelayBus.Get())
	{
		Bus->On(EUmbrellaEventType::WindEntered).Remove(RelayEnteredHandle);
		Bus->On(EUmbrellaEventType::WindExited).Remove(RelayExitedHandle);
	}
	RelayBus.Reset();
}

void FPlaytestRun::Start(UWorld* World, AEllaCharacter* EllaOverride)
{
	WorldPtr = World;
	AEllaCharacter* Ella = EllaOverride ? EllaOverride : PlaytestFindElla(World);
	if (!Ella || !Ella->GetMotor() || !Ella->GetHealth() || !Ella->GetUmbrellaState() || !Ella->GetAttack())
	{
		UE_LOG(LogUmbrellaElla, Warning, TEXT("PLAYTEST_ABORT no Ella with Motor, Health, State and Attack"));
		Phase = EPlaytestPhase::Done;
		return;
	}
	EllaPtr = Ella;
	EllaHome = Ella->GetActorLocation();
	if (IsWindRelayRun())
	{
		StartWindRelay(Ella);
	}
	Ella->GetMotor()->ClearPlayBounds();

	ABrokenMillRoom* NewRoom = World->SpawnActor<ABrokenMillRoom>(ABrokenMillRoom::StaticClass(), FTransform(FVector(ScratchRoomX, 0.0, 0.0)));
	if (!NewRoom)
	{
		UE_LOG(LogUmbrellaElla, Warning, TEXT("PLAYTEST_ABORT room did not spawn"));
		Phase = EPlaytestPhase::Done;
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
	Ella->GetHealth()->ResetForRetry();
	if (bLow)
	{
		PlaytestHurtTo(Ella, GetDefault<UUmbrellaTuning>()->Health.HitsPerLife * LowHealthShare, ScriptClock);
	}
	HealthAtStart = Ella->GetHealth()->GetState().Active;
	const FBrokenMillTuning& Mill = NewRoom->GetMillTuning();
	PlaytestSettle(Ella);
	PlaytestPlace(Ella, FVector2D(FPlaytestRun::RoomStartX, Mill.TargetCentre.Y));
	NewRoom->SetTargetActor(Ella);
	NewRoom->ResetForRestart();
	NewRoom->SetSimulationPaused(false);
	StartGuardHp = NewRoom->GetGuardHp();
	ShotsAtStart = Ella->GetAttack()->GetShotsFired();
	Ella->GetUmbrellaState()->SetRideHeld(true);
	Ella->GetUmbrellaState()->SetShootHeld(true);
	LastEllaLocation = Ella->GetActorLocation();
	LastEllaSpeed = Ella->GetMotor()->GetVelocity().Size();
	Phase = EPlaytestPhase::Haz;
}

void FPlaytestRun::UseDirector(AUmbrellaLevelDirector* Director)
{
	DirectorOverride = Director;
}

bool FPlaytestRun::IsTeleportStep(float StepDistance, float SpeedBefore, float SpeedAfter, float DeltaSeconds)
{
	const float Allowed = FMath::Max(SpeedBefore, SpeedAfter) * DeltaSeconds * PlaytestTeleportSpeedShare + PlaytestTeleportSlack;
	return StepDistance > Allowed;
}

bool FPlaytestRun::IsCurrentLive(const AWindCurrent* Current)
{
	if (!Current || Current->IsHidden() || Current->GetForce() <= 0.0f)
	{
		return false;
	}
	TArray<UBoxComponent*> Boxes;
	Current->GetComponents(Boxes);
	for (const UBoxComponent* Box : Boxes)
	{
		if (Box->GetGenerateOverlapEvents() && Box->GetCollisionEnabled() != ECollisionEnabled::NoCollision)
		{
			return true;
		}
	}
	return false;
}

bool FPlaytestRun::IsFrameCovered(const FBox2D& Frame, const TArray<FBox2D>& Layers)
{
	TArray<FBox2D> Usable;
	for (const FBox2D& Layer : Layers)
	{
		if (Layer.Min.Y <= Frame.Min.Y && Layer.Max.Y >= Frame.Max.Y)
		{
			Usable.Add(Layer);
		}
	}
	Usable.Sort([](const FBox2D& A, const FBox2D& B) { return A.Min.X < B.Min.X; });
	double Reach = Frame.Min.X;
	for (const FBox2D& Layer : Usable)
	{
		if (Layer.Min.X > Reach)
		{
			break;
		}
		Reach = FMath::Max(Reach, static_cast<double>(Layer.Max.X));
	}
	return Reach >= Frame.Max.X;
}

void FPlaytestRun::PlaytestPlace(AEllaCharacter* Ella, const FVector2D& RoomPoint) const
{
	const ABrokenMillRoom* Mill = Room.Get();
	FVector Location = Mill->RoomToWorld(RoomPoint);
	// Keep Ella's own depth (draw order Y); only X and Z come from the room.
	Location.Y = Ella->GetActorLocation().Y;
	Ella->SetActorLocation(Location);
}

void FPlaytestRun::PlaytestSettle(AEllaCharacter* Ella)
{
	// Kill carried wind momentum: free fall (fast decay) far from every current, then back to a neutral open umbrella.
	UUmbrellaStateComponent* State = Ella->GetUmbrellaState();
	PlaytestPlace(Ella, FVector2D(ParkRoomX, ParkRoomZ));
	State->SetShootHeld(true);
	State->SetAbsorbHeld(true);
	for (int32 StepIndex = 0; StepIndex < FMath::RoundToInt(SettleSeconds / StepSeconds); ++StepIndex)
	{
		Ella->GetMotor()->StepMotor(StepSeconds);
	}
	State->SetShootHeld(false);
	State->SetAbsorbHeld(false);
	Ella->GetMotor()->SetTrimAxis(0.0f);
}

void FPlaytestRun::MeasureCam04(AEllaCharacter* Ella)
{
	if (!Room.IsValid() || !Room->GetLowerWind())
	{
		return;
	}
	struct FProfile { const TCHAR* Name; float Trim; };
	const FProfile Profiles[] = {{TEXT("mill_lower_v2_trim0"), 0.0f}, {TEXT("mill_lower_v2_trim_up"), 1.0f}, {TEXT("mill_lower_v2_trim_down"), -1.0f}};
	for (const bool bMin : {false, true})
	{
		for (const FProfile& Profile : Profiles)
		{
			MeasureCam04Path(Ella, Profile.Name, bMin, Profile.Trim);
		}
	}
	MeasureCam04Transients(Ella);
	Ella->GetHealth()->ResetForRetry();
	Ella->GetUmbrellaState()->SetRideHeld(false);
}

void FPlaytestRun::MeasureCam04Path(AEllaCharacter* Ella, const TCHAR* Profile, bool bMinHealth, float Trim)
{
	ABrokenMillRoom* Mill = Room.Get();
	const FBrokenMillTuning& T = Mill->GetMillTuning();
	UEllaMotorComponent* Motor = Ella->GetMotor();
	UUmbrellaStateComponent* State = Ella->GetUmbrellaState();
	const FMotorTuning& MotorTuning = GetDefault<UUmbrellaTuning>()->Motor;
	const float CarrySpeed = FMath::Min(Mill->GetLowerWind()->GetForce(), MotorTuning.HorizontalMaxSpeed);
	const FBox2D Band(FVector2D(T.FiringColumnX.X, T.LowerOnwardZ.X), FVector2D(T.FiringColumnX.Y, T.LowerOnwardZ.Y));
	const float HalfHeight = Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();

	PlaytestSettle(Ella);
	Ella->GetHealth()->ResetForRetry();
	if (bMinHealth)
	{
		PlaytestHurtTo(Ella, FPlaytestRun::MinHealthLeft, ScriptClock);
	}
	Motor->SetTrimAxis(Trim);
	State->SetRideHeld(true);
	const FVector2D Start(Band.Min.X + PathEntryInset, Band.GetCenter().Y);
	PlaytestPlace(Ella, Start);

	bool bEntered = false;
	float AccelT = -1.0f;
	float PeakVx = 0.0f;
	float RideSeconds = 0.0f;
	float RootZMin = Start.Y;
	float RootZMax = Start.Y;
	float ExitT = -1.0f;
	FVector2D ExitRoot = Start;
	float ExitVx = 0.0f;
	EPlaytestBandExit Exit = EPlaytestBandExit::None;
	float RideEndZ = Start.Y;
	const int32 Steps = FMath::RoundToInt(CamSeconds / StepSeconds);
	for (int32 StepIndex = 1; StepIndex <= Steps; ++StepIndex)
	{
		Motor->StepMotor(StepSeconds);
		const float Now = StepIndex * StepSeconds;
		const FVector Velocity = Motor->GetVelocity();
		const FVector2D Root = Mill->WorldToRoom(Ella->GetActorLocation());
		if (Motor->IsRiding())
		{
			bEntered = true;
			RideSeconds += StepSeconds;
			RideEndZ = Root.Y;
		}
		PeakVx = FMath::Max(PeakVx, static_cast<float>(Velocity.X));
		if (AccelT < 0.0f && Velocity.X >= CarryShare * CarrySpeed)
		{
			AccelT = Now;
		}
		if (Exit == EPlaytestBandExit::None)
		{
			RootZMin = FMath::Min(RootZMin, static_cast<float>(Root.Y));
			RootZMax = FMath::Max(RootZMax, static_cast<float>(Root.Y));
			Exit = BandExit(Root, Band);
			if (Exit != EPlaytestBandExit::None)
			{
				ExitT = Now;
				ExitRoot = Root;
				ExitVx = Velocity.X;
			}
		}
		else if (!Motor->IsRiding())
		{
			break;
		}
	}
	// The path qualifies when the real current carried her out of its far (onward) edge without leaving the band's eligible height.
	const bool bQualified = bEntered && Exit == EPlaytestBandExit::Right;
	Emit(TEXT("CAM04"), {{TEXT("profile"), Profile}, {TEXT("health"), bMinHealth ? TEXT("min") : TEXT("full")},
		{TEXT("lift"), PlaytestNum(Motor->GetLiftMultiplier())}, {TEXT("trim"), PlaytestNum(Trim)}, {TEXT("entered"), PlaytestBool(bEntered)},
		{TEXT("carry_speed"), PlaytestNum(CarrySpeed)}, {TEXT("accel_t90"), PlaytestNum(AccelT)}, {TEXT("vx_peak"), PlaytestNum(PeakVx)},
		{TEXT("exit_edge"), BandExitName(Exit)}, {TEXT("exit_t"), PlaytestNum(ExitT)}, {TEXT("exit_x"), PlaytestNum(ExitRoot.X)},
		{TEXT("exit_root_z"), PlaytestNum(ExitRoot.Y)}, {TEXT("exit_vx"), PlaytestNum(ExitVx)},
		{TEXT("vert_disp"), PlaytestNum(ExitRoot.Y - Start.Y)}, {TEXT("root_z_min"), PlaytestNum(RootZMin)}, {TEXT("root_z_max"), PlaytestNum(RootZMax)},
		{TEXT("half_h"), PlaytestNum(HalfHeight)}, {TEXT("ride_s"), PlaytestNum(RideSeconds)}, {TEXT("ride_end_root_z"), PlaytestNum(RideEndZ)},
		{TEXT("band_x"), FString::Printf(TEXT("%.0f-%.0f"), Band.Min.X, Band.Max.X)}, {TEXT("band_z"), FString::Printf(TEXT("%.0f-%.0f"), Band.Min.Y, Band.Max.Y)},
		{TEXT("qualified"), PlaytestBool(bQualified)}});
	Motor->SetTrimAxis(0.0f);
}

void FPlaytestRun::MeasureCam04Transients(AEllaCharacter* Ella)
{
	// Motor response inside the real lower current with Ella's position held at the band centre after every step
	// (pinned=xz): acceleration, braking (Ride released in the current), reacquisition, decay after exit, open and falling.
	ABrokenMillRoom* Mill = Room.Get();
	const FBrokenMillTuning& T = Mill->GetMillTuning();
	UEllaMotorComponent* Motor = Ella->GetMotor();
	UUmbrellaStateComponent* State = Ella->GetUmbrellaState();
	const float CarrySpeed = FMath::Min(Mill->GetLowerWind()->GetForce(), GetDefault<UUmbrellaTuning>()->Motor.HorizontalMaxSpeed);
	const FVector2D Centre((T.FiringColumnX.X + T.FiringColumnX.Y) * 0.5f, (T.LowerOnwardZ.X + T.LowerOnwardZ.Y) * 0.5f);
	const FVector2D Outside(ParkRoomX, Centre.Y);
	const int32 Steps = FMath::RoundToInt(CamSeconds / StepSeconds);

	PlaytestSettle(Ella);
	Ella->GetHealth()->ResetForRetry();
	State->SetRideHeld(true);
	PlaytestPlace(Ella, Centre);

	// Time until the horizontal speed crosses Target (rising when bUp), position re-pinned to At every step. -1 = never.
	float Drift = 0.0f;
	auto Run = [&](const FVector2D& At, float Target, bool bUp) -> float
	{
		Drift = 0.0f;
		for (int32 StepIndex = 1; StepIndex <= Steps; ++StepIndex)
		{
			Motor->StepMotor(StepSeconds);
			const float Vx = Motor->GetVelocity().X;
			Drift += Vx * StepSeconds;
			PlaytestPlace(Ella, At);
			if (bUp ? Vx >= Target : Vx <= Target)
			{
				return StepIndex * StepSeconds;
			}
		}
		return -1.0f;
	};
	const float AccelT = Run(Centre, CarryShare * CarrySpeed, true);
	Run(Centre, CarrySpeed, true);
	const float SteadyVx = Motor->GetVelocity().X;
	const float SteadyVz = Motor->GetVelocity().Z;
	const bool bRodeSteady = Motor->IsRiding();

	State->SetRideHeld(false);
	const float BrakeT = Run(Centre, DecayShare * SteadyVx, false);
	State->SetRideHeld(true);
	const float ReacqT = Run(Centre, CarryShare * CarrySpeed, true);
	Run(Centre, CarrySpeed, true);

	const float BeforeOpen = Motor->GetVelocity().X;
	const float DecayOpenT = Run(Outside, DecayShare * BeforeOpen, false);
	const float DriftOpen = Drift;

	PlaytestPlace(Ella, Centre);
	Run(Centre, CarrySpeed, true);
	const float BeforeFall = Motor->GetVelocity().X;
	State->SetShootHeld(true);
	State->SetAbsorbHeld(true);
	const float DecayFallT = Run(Centre, DecayShare * BeforeFall, false);
	const float DriftFall = Drift;
	State->SetShootHeld(false);
	State->SetAbsorbHeld(false);

	// Diagnosis only (never part of a measurement): is Ella inside the real volume, and does the motor ride when the
	// same current is announced with the contract player id instead of the actor name the volume sends?
	PlaytestSettle(Ella);
	State->SetRideHeld(true);
	PlaytestPlace(Ella, Centre);
	AWindCurrent* Lower = Mill->GetLowerWind();
	const bool bOverlap = Lower->IsOverlappingActor(Ella);
	Motor->StepMotor(StepSeconds);
	const bool bRodeFromVolume = Motor->IsRiding();
	bool bRodeWithContractId = false;
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(Ella))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::WindEntered;
		Event.SourceId = FName(TEXT("PlaytestDiagnosisCurrent"));
		Event.TargetId = UmbrellaPlayerIds::Ella;
		Event.Detail = AWindCurrent::DirectionLabel(Lower->GetDirection());
		Event.Value = Lower->GetForce();
		Bus->Broadcast(Event);
		Motor->StepMotor(StepSeconds);
		bRodeWithContractId = Motor->IsRiding();
		Event.Type = EUmbrellaEventType::WindExited;
		Bus->Broadcast(Event);
	}
	Emit(TEXT("WINDDIAG"), {{TEXT("ella_id"), Ella->GetFName().ToString()}, {TEXT("contract_id"), UmbrellaPlayerIds::Ella.ToString()},
		{TEXT("overlap"), PlaytestBool(bOverlap)}, {TEXT("rode_from_volume"), PlaytestBool(bRodeFromVolume)},
		{TEXT("rode_with_contract_id"), PlaytestBool(bRodeWithContractId)}});
	PlaytestSettle(Ella);

	Emit(TEXT("CAM04T"), {{TEXT("profile"), TEXT("mill_lower_v2_trim0")}, {TEXT("health"), TEXT("full")}, {TEXT("pinned"), TEXT("xz")},
		{TEXT("ella_id"), Ella->GetFName().ToString()}, {TEXT("carry_speed"), PlaytestNum(CarrySpeed)}, {TEXT("rode"), PlaytestBool(bRodeSteady)},
		{TEXT("steady_vx"), PlaytestNum(SteadyVx)}, {TEXT("steady_vz"), PlaytestNum(SteadyVz)}, {TEXT("accel_t90"), PlaytestNum(AccelT)},
		{TEXT("brake_t10"), PlaytestNum(BrakeT)}, {TEXT("reacq_t90"), PlaytestNum(ReacqT)}, {TEXT("decay_open_t10"), PlaytestNum(DecayOpenT)},
		{TEXT("drift_open"), PlaytestNum(DriftOpen)}, {TEXT("decay_fall_t10"), PlaytestNum(DecayFallT)}, {TEXT("drift_fall"), PlaytestNum(DriftFall)}});
}

void FPlaytestRun::MeasureCam07(AEllaCharacter* Ella)
{
	if (!Room.IsValid())
	{
		return;
	}
	const FBrokenMillTuning& T = Room->GetMillTuning();
	// Fold from the upper RESET band and reopen: on time (lower band centre), late (its eligible bottom) and missed
	// (the mill's missed-current assist height, below the band). Only the first two are descent decisions the room must catch.
	MeasureCam07Case(Ella, TEXT("ontime"), (T.LowerOnwardZ.X + T.LowerOnwardZ.Y) * 0.5f);
	MeasureCam07Case(Ella, TEXT("late"), T.LowerOnwardZ.X);
	MeasureCam07Case(Ella, TEXT("missed"), T.MissedCurrentAssistPoint.Y);
	Ella->GetUmbrellaState()->SetRideHeld(false);
}

void FPlaytestRun::MeasureCam07Case(AEllaCharacter* Ella, const TCHAR* Case, float ReopenRootZ)
{
	ABrokenMillRoom* Mill = Room.Get();
	const FBrokenMillTuning& T = Mill->GetMillTuning();
	UEllaMotorComponent* Motor = Ella->GetMotor();
	UUmbrellaStateComponent* State = Ella->GetUmbrellaState();
	const float HalfHeight = Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const int32 Steps = FMath::RoundToInt(CamSeconds / StepSeconds);

	PlaytestSettle(Ella);
	Ella->GetHealth()->ResetForRetry();
	State->SetRideHeld(true);
	const FVector2D Start((T.FiringColumnX.X + T.FiringColumnX.Y) * 0.5f, (T.UpperResetZ.X + T.UpperResetZ.Y) * 0.5f);
	PlaytestPlace(Ella, Start);
	Motor->StepMotor(StepSeconds);
	const bool bRodeUpper = Motor->IsRiding();

	// Fold (Shoot + Absorb = free fall) and drop to the reopen height.
	State->SetShootHeld(true);
	State->SetAbsorbHeld(true);
	FVector2D Root = Mill->WorldToRoom(Ella->GetActorLocation());
	float FallT = 0.0f;
	for (int32 StepIndex = 1; StepIndex <= Steps && Root.Y > ReopenRootZ; ++StepIndex)
	{
		Motor->StepMotor(StepSeconds);
		FallT = StepIndex * StepSeconds;
		Root = Mill->WorldToRoom(Ella->GetActorLocation());
	}
	const FVector2D Reopen = Root;
	State->SetShootHeld(false);
	State->SetAbsorbHeld(false);

	// Reopen with Ride held and watch for a catch by a real current.
	float MinRootZ = Reopen.Y;
	bool bCaught = false;
	float CatchT = -1.0f;
	for (int32 StepIndex = 1; StepIndex <= FMath::RoundToInt(CatchWatchSeconds / StepSeconds); ++StepIndex)
	{
		Motor->StepMotor(StepSeconds);
		Root = Mill->WorldToRoom(Ella->GetActorLocation());
		MinRootZ = FMath::Min(MinRootZ, static_cast<float>(Root.Y));
		if (!bCaught && Motor->IsRiding())
		{
			bCaught = true;
			CatchT = StepIndex * StepSeconds;
		}
	}
	const float MinClear = MinRootZ - HalfHeight - T.FloorTop;
	const bool bChallengeClear = Mill->GetGuardHp() <= 0.0f;
	const AWindCurrent* Upper = Mill->GetUpperWind();
	const AWindCurrent* Lower = Mill->GetLowerWind();
	const bool bActive = Upper && Lower && !Upper->IsHidden() && !Lower->IsHidden() && Upper->GetForce() > 0.0f && Lower->GetForce() > 0.0f;
	Emit(TEXT("CAM07"), {{TEXT("case"), Case}, {TEXT("start_root_z"), PlaytestNum(Start.Y)}, {TEXT("rode_upper"), PlaytestBool(bRodeUpper)},
		{TEXT("fall_s"), PlaytestNum(FallT)}, {TEXT("reopen_root_z"), PlaytestNum(Reopen.Y)}, {TEXT("x_drift"), PlaytestNum(Reopen.X - Start.X)},
		{TEXT("min_root_z"), PlaytestNum(MinRootZ)}, {TEXT("fall_after_reopen"), PlaytestNum(Reopen.Y - MinRootZ)},
		{TEXT("half_h"), PlaytestNum(HalfHeight)}, {TEXT("floor"), PlaytestNum(T.FloorTop)}, {TEXT("min_clear"), PlaytestNum(MinClear)},
		{TEXT("caught"), PlaytestBool(bCaught)}, {TEXT("catch_t"), PlaytestNum(CatchT)},
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
	int32 Covered = 0;
	if (Backdrop)
	{
		const float ViewHeight = GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaHeight * FrameHeightShare;
		const float FrameZ = EllaPtr.IsValid() ? EllaPtr->GetActorLocation().Z : 0.0f;
		const TArray<TObjectPtr<AActor>>& Layers = Backdrop->GetLayers();
		const TArray<FBackdropLayerSpec>& Specs = Backdrop->GetBuiltSpecs();
		for (int32 Slot = 0; Slot < Total; ++Slot)
		{
			const float SlotEnd = Slot + 1 < Total ? LevelCatalogue::SlotStartX(Slot + 1) : RouteEnd;
			const float CameraX = (LevelCatalogue::SlotStartX(Slot) + SlotEnd) * 0.5f;
			const FBox2D Frame(FVector2D(CameraX - ViewWidth * 0.5f, FrameZ - ViewHeight * 0.5f), FVector2D(CameraX + ViewWidth * 0.5f, FrameZ + ViewHeight * 0.5f));
			TArray<FBox2D> Boxes;
			for (int32 Index = 0; Index < Layers.Num() && Index < Specs.Num(); ++Index)
			{
				if (!Layers[Index])
				{
					continue;
				}
				FVector Origin, Extent;
				Layers[Index]->GetActorBounds(true, Origin, Extent);
				const float X = UUmbrellaBackdropSubsystem::LayerXForCamera(CameraX, Specs[Index].Parallax);
				Boxes.Add(FBox2D(FVector2D(X - Extent.X, Origin.Z - Extent.Z), FVector2D(X + Extent.X, Origin.Z + Extent.Z)));
			}
			Covered += IsFrameCovered(Frame, Boxes) ? 1 : 0;
		}
	}
	Emit(TEXT("FLOW25"), {{TEXT("drawn_width"), PlaytestNum(Drawn)}, {TEXT("usable_width"), PlaytestNum(Usable)},
		{TEXT("tol"), PlaytestNum(DrawnWidthTolerance)}, {TEXT("lead_left_ok"), PlaytestBool(bLeadOk)}, {TEXT("lead_right_ok"), PlaytestBool(bLeadOk)},
		{TEXT("stages_total"), FString::FromInt(Total)}, {TEXT("stages_covered"), FString::FromInt(Covered)}});
}

void FPlaytestRun::Advance(float DeltaSeconds)
{
	if (!EllaPtr.IsValid() || !WorldPtr.IsValid())
	{
		Phase = EPlaytestPhase::Done;
		return;
	}
	switch (Phase)
	{
	case EPlaytestPhase::Haz:
		AdvanceHaz(DeltaSeconds);
		break;
	case EPlaytestPhase::Flow28:
		AdvanceFlow28(DeltaSeconds);
		break;
	default:
		break;
	}
}

void FPlaytestRun::AdvanceHaz(float DeltaSeconds)
{
	AEllaCharacter* Ella = EllaPtr.Get();
	ABrokenMillRoom* Mill = Room.Get();
	if (!Mill)
	{
		Phase = EPlaytestPhase::Done;
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

	// Per-tick samples: teleport check against her own speed, and both required currents while the guard lives.
	const FVector Now = Ella->GetActorLocation();
	const float Speed = Ella->GetMotor()->GetVelocity().Size();
	const float StepDistance = static_cast<float>(FVector::Dist(Now, LastEllaLocation));
	if (DeltaSeconds > 0.0f && IsTeleportStep(StepDistance, LastEllaSpeed, Speed, DeltaSeconds))
	{
		++TeleportSteps;
		if (StepDistance > WorstTeleportStep)
		{
			WorstTeleportStep = StepDistance;
			WorstTeleportDt = DeltaSeconds;
			WorstTeleportSpeed = FMath::Max(LastEllaSpeed, Speed);
		}
	}
	LastEllaLocation = Now;
	LastEllaSpeed = Speed;
	if (Mill->GetGuardHp() > 0.0f)
	{
		++CurrentSamples;
		CurrentSamplesLive += (IsCurrentLive(Mill->GetUpperWind()) && IsCurrentLive(Mill->GetLowerWind())) ? 1 : 0;
	}
	else
	{
		bGuardDiedWhileSampling = true;
	}
	if (HazElapsed >= HazRunSeconds || Mill->GetGuardHp() <= 0.0f)
	{
		FinishHaz();
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
	const bool bCleared = Mill->GetGuardHp() <= 0.0f;
	// The only moves Ella makes in this phase are trim and shoot; teleport is measured per tick, the other two aids have no code path here.
	Emit(TEXT("HAZ16"), {{TEXT("res"), FString::Printf(TEXT("%dx%d"), Res.X, Res.Y)}, {TEXT("debug"), TEXT("0")},
		{TEXT("health"), bLow ? TEXT("low") : TEXT("healthy")}, {TEXT("attempts"), FString::FromInt(Ella->GetAttack()->GetShotsFired() - ShotsAtStart)},
		{TEXT("useful_hits"), FString::FromInt(UsefulHits)}, {TEXT("damage"), PlaytestNum(Damage)}, {TEXT("reset_s"), PlaytestNum(IdleSeconds)}, {TEXT("run_s"), PlaytestNum(HazElapsed)},
		{TEXT("warned"), PlaytestBool(Mill->GetEventCount(EMillGuardEvent::WarningStarted) > 0)}, {TEXT("autoaim"), TEXT("0")},
		{TEXT("invuln"), TEXT("0")}, {TEXT("teleport"), PlaytestBool(TeleportSteps > 0)}, {TEXT("teleport_steps"), FString::FromInt(TeleportSteps)}, {TEXT("worst_step"), PlaytestNum(WorstTeleportStep)}, {TEXT("worst_dt"), PlaytestNum(WorstTeleportDt)}, {TEXT("worst_speed"), PlaytestNum(WorstTeleportSpeed)},
		{TEXT("boring"), PlaytestBool(bBoring)}, {TEXT("cleared"), PlaytestBool(bCleared)}});
	// persistence: both required currents were live on every tick while the guard lived.
	Emit(TEXT("CAM07"), {{TEXT("case"), TEXT("persist")}, {TEXT("samples"), FString::FromInt(CurrentSamples)},
		{TEXT("samples_live"), FString::FromInt(CurrentSamplesLive)},
		{TEXT("required_current_active"), PlaytestBool(CurrentSamples > 0 && CurrentSamplesLive == CurrentSamples)},
		{TEXT("challenge_clear"), PlaytestBool(bCleared)}});
	StartFlow28();
}

void FPlaytestRun::StartFlow28()
{
	UWorld* World = WorldPtr.Get();
	AEllaCharacter* Ella = EllaPtr.Get();
	Ella->GetHealth()->ResetForRetry();
	PlaytestHurtTo(Ella, Ella->GetHealth()->GetState().Active - CarryDamage, ScriptClock);
	FlowHealthBefore = FMath::CeilToInt(Ella->GetHealth()->GetState().Active);
	AUmbrellaLevelDirector* Director = DirectorOverride.Get();
	if (!Director)
	{
		Director = World->SpawnActor<AUmbrellaLevelDirector>();
		if (Director)
		{
			Director->BuildRoute(RouteSeed);
		}
	}
	if (!Director || Director->GetSlotsSpawned() <= 0)
	{
		FinishFlow28(TEXT("level_director_built_no_route"));
		return;
	}
	FlowDirector = Director;
	Director->PlaceAtCheckpoint(Ella, 1);
	FlowTravelX = static_cast<float>(Ella->GetActorLocation().X);
	Phase = EPlaytestPhase::Flow28;
}

void FPlaytestRun::AdvanceFlow28(float DeltaSeconds)
{
	AEllaCharacter* Ella = EllaPtr.Get();
	AUmbrellaLevelDirector* Director = FlowDirector.Get();
	if (!Director)
	{
		FinishFlow28(TEXT("director_lost"));
		return;
	}
	FlowElapsed += DeltaSeconds;
	if (FlowHandoffAt < 0.0f)
	{
		// Route driver: Ella is carried along the route at a fixed speed; the director sees her X every tick, as in play.
		FlowTravelX += FlowTravelSpeed * DeltaSeconds;
		FVector Location = Ella->GetActorLocation();
		Location.X = FlowTravelX;
		Ella->SetActorLocation(Location);
		Director->StepFollow(FlowTravelX, 1);
		if (Director->HasHandedOff())
		{
			FlowHandoffAt = FlowElapsed;
			FlowHealthAtHandoff = FMath::CeilToInt(Ella->GetHealth()->GetState().Active);
			FlowCameraAtHandoff = Director->GetLastCameraX();
			int32 Threats = 0;
			for (TActorIterator<AUmbrellaEnemy> It(WorldPtr.Get()); It; ++It)
			{
				if (!It->IsHidden() && !It->IsActorBeingDestroyed())
				{
					++Threats;
				}
			}
			FlowThreatsAtHandoff = Threats;
		}
		else if (FlowElapsed >= FlowTravelMaxSeconds)
		{
			FinishFlow28(TEXT("route_not_finished_in_time"));
		}
		return;
	}
	Director->StepFollow(FlowTravelX, 1);
	if (FlowElapsed - FlowHandoffAt >= FlowSettleSeconds)
	{
		FinishFlow28(TEXT(""));
	}
}

void FPlaytestRun::FinishFlow28(const TCHAR* NotMeasured)
{
	AEllaCharacter* Ella = EllaPtr.Get();
	AUmbrellaLevelDirector* Director = FlowDirector.Get();
	const bool bMeasured = FlowHandoffAt >= 0.0f;
	const bool bSettled = bMeasured && Director && FMath::Abs(Director->GetLastCameraX() - FlowCameraAtHandoff) <= FlowSettleTolerance;
	TArray<TPair<FString, FString>> Pairs = {{TEXT("health_before"), FString::FromInt(FlowHealthBefore)},
		{TEXT("health_after"), FString::FromInt(bMeasured ? FlowHealthAtHandoff : FlowHealthBefore)},
		{TEXT("max"), FString::FromInt(FMath::CeilToInt(Ella->GetHealth()->GetState().Capacity))},
		{TEXT("threats"), FString::FromInt(FlowThreatsAtHandoff)}, {TEXT("framing_settled"), PlaytestBool(bSettled)},
		{TEXT("boss_began"), PlaytestBool(Director && Director->HasHandedOff())}, {TEXT("route_s"), PlaytestNum(FlowElapsed)}};
	if (FCString::Strlen(NotMeasured) > 0)
	{
		Pairs.Add({TEXT("not_measured"), NotMeasured});
	}
	Emit(TEXT("FLOW28"), Pairs);
	if (Director && !DirectorOverride.IsValid())
	{
		Director->ClearRoute();
		Director->Destroy();
	}
	Finish();
}

void FPlaytestRun::Finish()
{
	StopWindRelay();
	if (AEllaCharacter* Ella = EllaPtr.Get())
	{
		Ella->SetActorLocation(EllaHome);
	}
	if (ABrokenMillRoom* Mill = Room.Get())
	{
		Mill->Destroy();
	}
	Phase = EPlaytestPhase::Done;
}

void FPlaytestRun::Emit(const TCHAR* Key, const TArray<TPair<FString, FString>>& Pairs)
{
	TArray<TPair<FString, FString>> Tagged = Pairs;
	Tagged.Add({TEXT("relay"), IsWindRelayRun() ? TEXT("1") : TEXT("0")});
	Lines.Add(FormatLine(Key, Tagged));
	UE_LOG(LogUmbrellaElla, Log, TEXT("%s"), *Lines.Last());
}
