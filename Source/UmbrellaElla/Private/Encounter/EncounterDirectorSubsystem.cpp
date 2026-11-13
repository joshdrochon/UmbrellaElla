#include "Encounter/EncounterDirectorSubsystem.h"
#include "Core/UmbrellaSourceIds.h"

#include "Arena/UmbrellaArena.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaLog.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Kismet/GameplayStatics.h"
#include "Owl/KeeperOfTime.h"
#include "Owl/KeeperPartComponent.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Projectile/UmbrellaShotReceiver.h"

namespace
{
	const FName KeeperSource(TEXT("KeeperOfTime"));
	const FName PlayerTarget(TEXT("Ella"));
	const FName SuccessDetail(TEXT("success"));
	/** AnimationCue details: the rear second clack and the double-beat reprise. */
	const FName KeeperRearClackCue(TEXT("KeeperRearSecondClack"));
	const FName KeeperBeatRepriseCue(TEXT("KeeperBeatReprise"));

	FName PartName(EKeeperPart Part)
	{
		switch (Part)
		{
		case EKeeperPart::Wings: return FName(TEXT("WINGS"));
		case EKeeperPart::Front: return FName(TEXT("MECH_FRONT"));
		case EKeeperPart::Middle: return FName(TEXT("MECH_MIDDLE"));
		case EKeeperPart::Rear: return FName(TEXT("MECH_REAR"));
		case EKeeperPart::Clock: return FName(TEXT("CLOCK"));
		case EKeeperPart::Eye: return FName(TEXT("EYE"));
		default: return NAME_None;
		}
	}
}

// ---------------------------------------------------------------- lifetime

bool UEncounterDirectorSubsystem::DoesSupportWorldType(EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId UEncounterDirectorSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UEncounterDirectorSubsystem, STATGROUP_Tickables);
}

void UEncounterDirectorSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Collection.InitializeDependency<UUmbrellaEventBus>();
	Super::Initialize(Collection);
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		DefeatedHandle = Bus->On(EUmbrellaEventType::PlayerDefeated).AddUObject(this, &UEncounterDirectorSubsystem::HandleDefeated);
		LifeLostHandle = Bus->On(EUmbrellaEventType::LifeLost).AddUObject(this, &UEncounterDirectorSubsystem::HandleLifeLost);
	}
}

void UEncounterDirectorSubsystem::Deinitialize()
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		Bus->On(EUmbrellaEventType::PlayerDefeated).Remove(DefeatedHandle);
		Bus->On(EUmbrellaEventType::LifeLost).Remove(LifeLostHandle);
	}
	DestroyKeeper();
	Super::Deinitialize();
}

void UEncounterDirectorSubsystem::SetManualStepping(bool bManual)
{
	bManualStepping = bManual;
}

void UEncounterDirectorSubsystem::SetPlayerActor(AActor* Actor)
{
	PlayerOverride = Actor;
}

FName UEncounterDirectorSubsystem::PhaseName(EKeeperPhase Phase)
{
	switch (Phase)
	{
	case EKeeperPhase::Wings: return FName(TEXT("wings"));
	case EKeeperPhase::Mechanisms: return FName(TEXT("mechanisms"));
	default: return FName(TEXT("clock"));
	}
}

EEncounterState UEncounterDirectorSubsystem::ResolveEnding(bool bPlayerDefeated, bool bFightWon)
{
	if (FKeeperFightModel::ShouldDefeatWin(bPlayerDefeated, bFightWon) || (bPlayerDefeated && !bFightWon))
	{
		return EEncounterState::EndingFailure;
	}
	return bFightWon ? EEncounterState::EndingSuccess : EEncounterState::Active;
}

FKeeperRuleSwitches UEncounterDirectorSubsystem::BuildSwitches() const
{
	FKeeperRuleSwitches Switches;
	Switches.bRed = IsFeatureEnabled(EFeatureId::OWL_11);
	Switches.bYellow = IsFeatureEnabled(EFeatureId::OWL_13);
	Switches.bGust = IsFeatureEnabled(EFeatureId::OWL_16);
	Switches.bTalon = IsFeatureEnabled(EFeatureId::OWL_19);
	Switches.bFrontCast = IsFeatureEnabled(EFeatureId::OWL_22);
	Switches.bMiddleCast = IsFeatureEnabled(EFeatureId::OWL_25);
	Switches.bRearCast = IsFeatureEnabled(EFeatureId::OWL_26);
	Switches.bDoubleBeat = IsFeatureEnabled(EFeatureId::OWL_28);
	Switches.bClockProtection = IsFeatureEnabled(EFeatureId::OWL_29);
	Switches.bBreakStun = IsFeatureEnabled(EFeatureId::OWL_30);
	Switches.bSlow = IsFeatureEnabled(EFeatureId::OWL_31);
	Switches.bEye = IsFeatureEnabled(EFeatureId::OWL_32);
	return Switches;
}

// ---------------------------------------------------------------- world helpers

AActor* UEncounterDirectorSubsystem::GetPlayerActor() const
{
	if (PlayerOverride)
	{
		return PlayerOverride;
	}
	return UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
}

FVector2D UEncounterDirectorSubsystem::PlayerPosition() const
{
	const AActor* Player = GetPlayerActor();
	return Player ? FVector2D(Player->GetActorLocation().X, Player->GetActorLocation().Z) : FVector2D::ZeroVector;
}

float UEncounterDirectorSubsystem::PlayerRadius() const
{
	return GetDefault<UUmbrellaTuning>()->Encounter.PlayerRadius;
}

void UEncounterDirectorSubsystem::FillVerticalBounds(FKeeperTickInput& Input) const
{
	if (!Arena)
	{
		return;
	}
	const FMotorTuning& Motor = GetDefault<UUmbrellaTuning>()->Motor;
	// Slowest controllable rise and fall: full trim against the move.
	const float Trim = 1.0f - Motor.VerticalTrimPct / KeeperPercentScale;
	Input.bHasVerticalBounds = true;
	Input.FloorZ = Arena->LocalPoint(0.0f, 0.0f).Z;
	Input.CeilingZ = Arena->LocalPoint(0.0f, 1.0f).Z;
	Input.RiseSpeed = Motor.RiseSpeed * Trim;
	Input.FallSpeed = Motor.FallSpeed * Trim;
}

FVector UEncounterDirectorSubsystem::FindAnchor()
{
	if (!Arena)
	{
		TActorIterator<AUmbrellaArena> It(GetWorld());
		if (It)
		{
			Arena = *It;
		}
	}
	if (!Arena)
	{
		UE_LOG(LogUmbrellaElla, Warning, TEXT("Encounter Director: no arena in the world; the Keeper spawns at the origin."));
		return FVector::ZeroVector;
	}
	return Arena->GetKeeperAnchorLocation();
}

void UEncounterDirectorSubsystem::Broadcast(EUmbrellaEventType Type, FName Detail, FName Target, float Value, int32 Amount) const
{
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this);
	if (!Bus)
	{
		return;
	}
	FUmbrellaEvent Event;
	Event.Type = Type;
	Event.SourceId = KeeperSource;
	Event.TargetId = Target;
	Event.Detail = Detail;
	Event.Value = Value;
	Event.Amount = Amount;
	Bus->Broadcast(Event);
}

void UEncounterDirectorSubsystem::SpawnKeeper()
{
	DestroyKeeper();
	const FVector Anchor = FindAnchor();
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const FVector Location(Anchor.X, UmbrellaDrawOrder::KeeperY, Anchor.Z);
	Keeper = GetWorld()->SpawnActor<AKeeperOfTime>(AKeeperOfTime::StaticClass(), Location, FRotator::ZeroRotator, Params);
}

void UEncounterDirectorSubsystem::DestroyKeeper()
{
	if (Keeper)
	{
		Keeper->Destroy();
		Keeper = nullptr;
	}
}

void UEncounterDirectorSubsystem::ClearEnemyProjectiles() const
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	for (TActorIterator<AUmbrellaProjectile> It(World); It; ++It)
	{
		const EUmbrellaShotKind Kind = It->GetSpec().Kind;
		if (Kind == EUmbrellaShotKind::EnemyRed || Kind == EUmbrellaShotKind::EnemyYellow)
		{
			It->Destroy();
		}
	}
}

void UEncounterDirectorSubsystem::FreezeProjectiles() const
{
	SetProjectileTicks(false);
}

void UEncounterDirectorSubsystem::ThawProjectiles() const
{
	SetProjectileTicks(true);
}

void UEncounterDirectorSubsystem::SetProjectileTicks(bool bEnabled) const
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	for (TActorIterator<AUmbrellaProjectile> It(World); It; ++It)
	{
		It->SetActorTickEnabled(bEnabled);
	}
}

void UEncounterDirectorSubsystem::DeliverDamage(FName Source, float Amount) const
{
	AActor* Player = GetPlayerActor();
	if (!Player)
	{
		return;
	}
	FUmbrellaShotSpec Spec;
	Spec.Kind = EUmbrellaShotKind::EnemyRed;
	Spec.Damage = Amount;
	Spec.SourceId = Source;
	Spec.Origin = Player->GetActorLocation();
	if (IUmbrellaShotReceiver* Receiver = Cast<IUmbrellaShotReceiver>(Player))
	{
		if (Receiver->ReceiveShot(Spec, Player->GetActorLocation()) == EUmbrellaShotResult::Consumed)
		{
			return;
		}
	}
	TArray<UActorComponent*> Components;
	Player->GetComponents(Components);
	for (UActorComponent* Component : Components)
	{
		if (IUmbrellaShotReceiver* Receiver = Cast<IUmbrellaShotReceiver>(Component))
		{
			if (Receiver->ReceiveShot(Spec, Player->GetActorLocation()) == EUmbrellaShotResult::Consumed)
			{
				return;
			}
		}
	}
}

// ---------------------------------------------------------------- fight flow

void UEncounterDirectorSubsystem::BeginKeeperFight()
{
	BeginKeeperFightAtPhase(EKeeperPhase::Wings);
}

void UEncounterDirectorSubsystem::BeginKeeperFightAtPhase(EKeeperPhase Phase)
{
	if (!IsFeatureEnabled(EFeatureId::OWL_06))
	{
		UE_LOG(LogUmbrellaElla, Warning, TEXT("Encounter Director: the Keeper fight is switched off (OWL-06)."));
		return;
	}
	if (State == EEncounterState::Active || State == EEncounterState::Paused)
	{
		return;
	}
	const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
	SpawnKeeper();
	const FVector Anchor = FindAnchor();
	bWinPending = false;
	bDefeatInWinFrame = false;
	LivesLostThisPhase = 0;

	TArray<FKeeperCommand> Commands;
	if (bResumePending && bModelReady)
	{
		Model.SetAnchor(FVector2D(Anchor.X, Anchor.Z));
		Model.RetryCheckpoint(Commands);
	}
	else
	{
		Model.Init(Tuning->Keeper, Tuning->Encounter, BuildSwitches());
		bModelReady = true;
		Model.SetAnchor(FVector2D(Anchor.X, Anchor.Z));
		Model.BeginPhase(Phase, Commands);
	}
	bResumePending = false;
	State = EEncounterState::Active;
	ProcessCommands(Commands);
}

void UEncounterDirectorSubsystem::ResetForRestart()
{
	const EEncounterState Previous = State;
	State = EEncounterState::Restarting;
	ClearEnemyProjectiles();
	ThawProjectiles();
	DestroyKeeper();
	StopGustWind();
	bWinPending = false;
	bDefeatInWinFrame = false;
	const bool bRetry = IsFeatureEnabled(EFeatureId::FLOW_09) && IsFeatureEnabled(EFeatureId::OWL_10)
		&& Previous != EEncounterState::EndingSuccess && bModelReady;
	bResumePending = bRetry;
	State = EEncounterState::Ready;
	if (bRetry)
	{
		const int32 Lives = GetDefault<UUmbrellaTuning>()->Encounter.RetryLives;
		// Health (lane c) restores full health and exactly this many lives when it hears CheckpointRetried.
		Broadcast(EUmbrellaEventType::CheckpointRetried, PhaseName(Model.GetPhase()), PlayerTarget, 1.0f, Lives);
		if (GetDefault<UUmbrellaTuning>()->Encounter.bResumeAfterReset)
		{
			BeginKeeperFight();
		}
	}
}

void UEncounterDirectorSubsystem::SetPaused(bool bPaused)
{
	if (bPaused && State == EEncounterState::Active)
	{
		StateBeforePause = State;
		StopGustWind();
		State = EEncounterState::Paused;
		FreezeProjectiles();
	}
	else if (!bPaused && State == EEncounterState::Paused)
	{
		State = StateBeforePause;
		ThawProjectiles();
	}
}

void UEncounterDirectorSubsystem::Tick(float DeltaTime)
{
	if (bManualStepping)
	{
		return;
	}
	AdvanceFight(DeltaTime);
}

void UEncounterDirectorSubsystem::AdvanceFight(float DeltaSeconds)
{
	FinalizeEnding();
	if (State != EEncounterState::Active)
	{
		return;
	}
	ElapsedSeconds += DeltaSeconds;
	FKeeperTickInput Input;
	Input.PlayerPos = PlayerPosition();
	Input.PlayerRadius = PlayerRadius();
	FillVerticalBounds(Input);
	TArray<FKeeperCommand> Commands;
	bGustPushThisStep = false;
	Model.Step(DeltaSeconds, Input, Commands);
	ProcessCommands(Commands);
	if (bGustPushThisStep)
	{
		StartGustWind(PendingGustSpeed);
	}
	else
	{
		StopGustWind();
	}
	if (Keeper && State == EEncounterState::Active)
	{
		Keeper->Refresh(Model, ElapsedSeconds);
	}
}

EKeeperHitOutcome UEncounterDirectorSubsystem::HandlePlayerShot(EKeeperPart Part, float Damage)
{
	if (State != EEncounterState::Active)
	{
		return EKeeperHitOutcome::PassThrough;
	}
	TArray<FKeeperCommand> Commands;
	const FKeeperHitResult Result = Model.ApplyPlayerHit(Part, Damage, Commands);
	if (Result.Outcome == EKeeperHitOutcome::Damaged)
	{
		Broadcast(EUmbrellaEventType::BossTargetHit, PhaseName(Model.GetPhase()), PartName(Part), Result.HpAfter, 0);
	}
	ProcessCommands(Commands);
	if (Keeper && State == EEncounterState::Active)
	{
		Keeper->Refresh(Model, ElapsedSeconds);
	}
	return Result.Outcome;
}

void UEncounterDirectorSubsystem::ProcessCommands(TArray<FKeeperCommand>& Commands)
{
	UWorld* World = GetWorld();
	for (const FKeeperCommand& Command : Commands)
	{
		switch (Command.Type)
		{
		case EKeeperCommandType::FireShot:
		{
			FUmbrellaShotSpec Spec;
			Spec.Kind = Command.ShotKind;
			Spec.Origin = FVector(Command.A.X, UmbrellaDrawOrder::ProjectileY, Command.A.Y);
			Spec.Velocity = FVector(Command.B.X, 0.0f, Command.B.Y);
			Spec.Radius = Command.Value;
			Spec.Damage = Command.Damage;
			Spec.LifetimeSeconds = GetDefault<UUmbrellaTuning>()->Keeper.ShotLifetimeSeconds;
			Spec.SourceId = Command.Name;
			AUmbrellaProjectile::Fire(World, Spec);
			break;
		}
		case EKeeperCommandType::PhysicalWarning:
			Broadcast(EUmbrellaEventType::BossAttackTelegraphed, Command.Name, KeeperSource, Command.Value, Command.Serial);
			if (Keeper)
			{
				Keeper->ShowTelegraph(Command);
			}
			break;
		case EKeeperCommandType::PhysicalStrike:
			if (Command.Stage == EKeeperStage::Pause)
			{
				// The stopped head and second clack advertise an unfinished stroke, not recovery.
				Broadcast(EUmbrellaEventType::AnimationCue, KeeperRearClackCue, KeeperSource, Command.Value, Command.Serial);
			}
			break;
		case EKeeperCommandType::BeatReprise:
			Broadcast(EUmbrellaEventType::AnimationCue, KeeperBeatRepriseCue, KeeperSource, 0.0f, 0);
			break;
		case EKeeperCommandType::DamagePlayer:
			DeliverDamage(Command.Name, Command.Damage);
			DamageDelivered.Broadcast(Command.Name, Command.Damage);
			break;
		case EKeeperCommandType::PushPlayer:
			// Same world-scaled time as the model: the slow scale multiplies the push speed the Motor integrates.
			PendingGustSpeed = Command.Value * Model.GetWorldScale();
			bGustPushThisStep = true;
			break;
		case EKeeperCommandType::ClearProjectiles:
			ClearEnemyProjectiles();
			break;
		case EKeeperCommandType::ClearGusts:
			if (Keeper)
			{
				Keeper->ClearGusts();
			}
			break;
		case EKeeperCommandType::PartBroken:
			Broadcast(EUmbrellaEventType::BossPartDestroyed, PhaseName(Model.GetPhase()), PartName(Command.Part), 0.0f, 0);
			break;
		case EKeeperCommandType::PhaseStarted:
			// The phase start is the checkpoint (both modes, no mid-mechanism checkpoint).
			Broadcast(EUmbrellaEventType::PhaseStarted, PhaseName(Command.Phase), KeeperSource, Command.Value, 0);
			Broadcast(EUmbrellaEventType::CheckpointReached, PhaseName(Command.Phase), KeeperSource, 0.0f, 0);
			break;
		case EKeeperCommandType::FightWon:
			// Success is final only once the frame is over: a fatal player hit in the same frame wins the tie.
			bWinPending = true;
			WinFrame = static_cast<int64>(GFrameCounter);
			break;
		default:
			break;
		}
	}
}

// ---------------------------------------------------------------- ending

void UEncounterDirectorSubsystem::HandleLifeLost(const FUmbrellaEvent& Event)
{
	// A lost life with lives left does not reset the fight; only the last life ends the attempt.
	++LivesLostThisPhase;
}

void UEncounterDirectorSubsystem::HandleDefeated(const FUmbrellaEvent& Event)
{
	if (State != EEncounterState::Active && State != EEncounterState::Paused)
	{
		return;
	}
	if (bWinPending && Event.Frame != WinFrame)
	{
		return; // the win was authoritative in an earlier frame
	}
	bDefeatInWinFrame = bWinPending;
	bWinPending = false;
	EnterFailure();
}

void UEncounterDirectorSubsystem::StartGustWind(float SignedSpeed)
{
	if (bGustWindActive && FMath::IsNearlyEqual(ActiveGustSpeed, SignedSpeed))
	{
		return;
	}
	// Motor current contract: force (speed, units/s) in Value, direction word in Detail. Up for a positive push.
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::WindEntered;
		Event.SourceId = UmbrellaSourceIds::GustBand();
		Event.TargetId = PlayerTarget;
		Event.Detail = SignedSpeed >= 0.0f ? FName(TEXT("Up")) : FName(TEXT("Down"));
		Event.Value = FMath::Abs(SignedSpeed);
		Bus->Broadcast(Event);
	}
	bGustWindActive = true;
	ActiveGustSpeed = SignedSpeed;
}

void UEncounterDirectorSubsystem::StopGustWind()
{
	if (!bGustWindActive)
	{
		return;
	}
	bGustWindActive = false;
	ActiveGustSpeed = 0.0f;
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::WindExited;
		Event.SourceId = UmbrellaSourceIds::GustBand();
		Event.TargetId = PlayerTarget;
		Bus->Broadcast(Event);
	}
}

void UEncounterDirectorSubsystem::EnterFailure()
{
	TArray<FKeeperCommand> Commands;
	Model.Halt(Commands);
	ProcessCommands(Commands);
	StopGustWind();
	ThawProjectiles();
	State = EEncounterState::EndingFailure;
}

void UEncounterDirectorSubsystem::FinalizeEnding()
{
	if (!bWinPending || State != EEncounterState::Active)
	{
		return;
	}
	const bool bFrameOver = static_cast<int64>(GFrameCounter) > WinFrame || bManualStepping;
	if (!bFrameOver)
	{
		return;
	}
	bWinPending = false;
	State = ResolveEnding(false, true);
	ClearEnemyProjectiles();
	StopGustWind();
	// OWL-35 off: the fight still ends in success, only the departure animation is skipped (never Active with a halted model).
	const bool bDeparture = DepartureOverride.IsSet() ? DepartureOverride.GetValue() : IsFeatureEnabled(EFeatureId::OWL_35);
	const float Departure = bDeparture ? GetDefault<UUmbrellaTuning>()->Keeper.DepartureSeconds : 0.0f;
	if (Keeper)
	{
		Keeper->Refresh(Model, ElapsedSeconds);
		if (bDeparture)
		{
			Keeper->BeginDeparture(Departure);
		}
	}
	Broadcast(EUmbrellaEventType::EncounterCompleted, SuccessDetail, KeeperSource, Departure, 0);
}
