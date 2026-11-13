#include "Encounter/KeeperFightModel.h"
#include "Core/UmbrellaSourceIds.h"
#include "Owl/KeeperTuning.h"

namespace
{
	const FName RedFanName = UmbrellaSourceIds::RedFan();
	const FName BeatName = UmbrellaSourceIds::ClockDoubleBeat();
	const FName YellowName = UmbrellaSourceIds::YellowPacket();
	const FName GustName = UmbrellaSourceIds::GustBand();
	const FName TalonName = UmbrellaSourceIds::TalonRake();
	const FName FrontName = UmbrellaSourceIds::MechFrontCast();
	const FName MiddleName = UmbrellaSourceIds::MechMiddleCurve();
	const FName RearName = UmbrellaSourceIds::MechRearTwoStage();

	FName PhysicalName(EKeeperPhysical Kind)
	{
		switch (Kind)
		{
		case EKeeperPhysical::Gust: return GustName;
		case EKeeperPhysical::Talon: return TalonName;
		case EKeeperPhysical::FrontCast: return FrontName;
		case EKeeperPhysical::MiddleCurve: return MiddleName;
		case EKeeperPhysical::RearTwoStage: return RearName;
		default: return NAME_None;
		}
	}

	constexpr EKeeperPhysical CastCycle[] = {EKeeperPhysical::FrontCast, EKeeperPhysical::MiddleCurve, EKeeperPhysical::RearTwoStage};
	constexpr int32 CastCycleNum = UE_ARRAY_COUNT(CastCycle);

	FKeeperCommand MakeCommand(EKeeperCommandType Type)
	{
		FKeeperCommand Cmd;
		Cmd.Type = Type;
		return Cmd;
	}

	FVector2D Direction(float AngleDeg)
	{
		const float Rad = FMath::DegreesToRadians(AngleDeg);
		return FVector2D(FMath::Cos(Rad), FMath::Sin(Rad));
	}
}

// ---------------------------------------------------------------- statics

float FKeeperFightModel::MiddleSignForSerial(int32 Serial)
{
	return (Serial % 2 == 0) ? 1.0f : -1.0f;
}

float FKeeperFightModel::FanAngleDeg(float CenterDeg, float SpreadDeg, int32 Index, int32 Count)
{
	if (Count <= 1)
	{
		return CenterDeg;
	}
	const float Alpha = static_cast<float>(Index) / static_cast<float>(Count - 1);
	return CenterDeg + SpreadDeg * (Alpha - 0.5f);
}

bool FKeeperFightModel::ShouldDefeatWin(bool bPlayerDefeated, bool bFightWon)
{
	return bPlayerDefeated && bFightWon;
}

// ---------------------------------------------------------------- setup

void FKeeperFightModel::Init(const FKeeperTuning& InTuning, const FEncounterTuning& InEncounter, const FKeeperRuleSwitches& InSwitches)
{
	TuningRef = &InTuning;
	EncounterTuning = InEncounter;
	Switches = InSwitches;
	const int32 Count = static_cast<int32>(EKeeperPart::Count);
	PartHp.Init(0.0f, Count);
	CheckpointHp.Init(0.0f, Count);
	bHasCheckpoint = false;
	bEnded = false;
}

float FKeeperFightModel::PartMaxHp(EKeeperPart Part) const
{
	switch (Part)
	{
	case EKeeperPart::Wings: return Tuning().WingsHp;
	case EKeeperPart::Front: return Tuning().FrontHp;
	case EKeeperPart::Middle: return Tuning().MiddleHp;
	case EKeeperPart::Rear: return Tuning().RearHp;
	case EKeeperPart::Clock: return Tuning().ClockHp;
	default: return 0.0f;
	}
}

void FKeeperFightModel::ClearDynamicState()
{
	TransitionRemaining = 0.0f;
	PhaseTime = 0.0f;
	StunRemaining = 0.0f;
	BlackoutRemaining = 0.0f;
	FirePauseRemaining = 0.0f;
	ClockOpenRemaining = 0.0f;
	ClockProtectRemaining = 0.0f;
	FinalCycleTime = 0.0f;
	SlowRemaining = 0.0f;
	SlowCooldownRemaining = 0.0f;
	EyeWindowRemaining = 0.0f;
	EyeCooldownRemaining = 0.0f;
	bSlowUsedThisOpening = false;
	bEyeUsedThisOpening = false;
	RedCountdown = 0.0f;
	YellowCountdown = 0.0f;
	PhysicalCountdown = 0.0f;
	TalonCooldown = 0.0f;
	bTalonArmed = true;
	Pending.Reset();
	NextCastIndex = 0;
	Physical = EKeeperPhysical::None;
	Stage = EKeeperStage::Idle;
	StageRemaining = 0.0f;
	StageDuration = 0.0f;
	bDamagedThisCast = false;
	GustTravelled = 0.0f;
}

void FKeeperFightModel::BeginPhase(EKeeperPhase StartPhase, TArray<FKeeperCommand>& Out)
{
	bEnded = false;
	// A fresh start (or a jump to a later phase): every part at full HP, earlier phases already depleted.
	for (int32 Index = 0; Index < static_cast<int32>(EKeeperPart::Count); ++Index)
	{
		PartHp[Index] = PartMaxHp(static_cast<EKeeperPart>(Index));
	}
	if (StartPhase != EKeeperPhase::Wings)
	{
		PartHp[PartIndex(EKeeperPart::Wings)] = 0.0f;
	}
	if (StartPhase == EKeeperPhase::Clock)
	{
		PartHp[PartIndex(EKeeperPart::Front)] = 0.0f;
		PartHp[PartIndex(EKeeperPart::Middle)] = 0.0f;
		PartHp[PartIndex(EKeeperPart::Rear)] = 0.0f;
	}
	CastSerial = 0;
	StartTransition(StartPhase, Out);
}

void FKeeperFightModel::StartTransition(EKeeperPhase NewPhase, TArray<FKeeperCommand>& Out)
{
	ClearDynamicState();
	Phase = NewPhase;
	TransitionRemaining = EncounterTuning.PhaseTransitionSeconds;
	// Phase-start checkpoint: parts at their HP now (the clock carries earlier damage).
	CheckpointHp = PartHp;
	CheckpointPhase = NewPhase;
	bHasCheckpoint = true;
	HeadPos = GetClaw();
	FKeeperCommand Cmd;
	Cmd.Type = EKeeperCommandType::PhaseStarted;
	Cmd.Phase = NewPhase;
	Cmd.Value = TransitionRemaining;
	Out.Add(Cmd);
}

void FKeeperFightModel::FinishTransition(TArray<FKeeperCommand>& Out)
{
	TransitionRemaining = 0.0f;
	PhaseTime = 0.0f;
	RedCountdown = (Phase == EKeeperPhase::Clock) ? Tuning().BeatFirstAtSeconds : Tuning().RedFirstAtSeconds;
	YellowCountdown = Tuning().YellowFirstAtSeconds;
	PhysicalCountdown = (Phase == EKeeperPhase::Wings) ? Tuning().GustFirstAtSeconds : Tuning().CastFirstAtSeconds;
	FinalCycleTime = 0.0f;
	if (Phase == EKeeperPhase::Clock)
	{
		OpenClock(Out, true);
	}
	FKeeperCommand Cmd;
	Cmd.Type = EKeeperCommandType::TransitionEnded;
	Cmd.Phase = Phase;
	Out.Add(Cmd);
}

void FKeeperFightModel::RetryCheckpoint(TArray<FKeeperCommand>& Out)
{
	if (!bHasCheckpoint)
	{
		BeginPhase(EKeeperPhase::Wings, Out);
		return;
	}
	PartHp = CheckpointHp;
	bEnded = false;
	Out.Add(MakeCommand(EKeeperCommandType::ClearProjectiles));
	Out.Add(MakeCommand(EKeeperCommandType::ClearGusts));
	StartTransition(CheckpointPhase, Out);
}

void FKeeperFightModel::Halt(TArray<FKeeperCommand>& Out)
{
	if (Physical != EKeeperPhysical::None)
	{
		CancelPhysical(Out);
	}
	Pending.Reset();
	EndEffects(Out);
	bEnded = true;
	FKeeperCommand Clear;
	Clear.Type = EKeeperCommandType::ClearProjectiles;
	Out.Add(Clear);
	FKeeperCommand Gusts;
	Gusts.Type = EKeeperCommandType::ClearGusts;
	Out.Add(Gusts);
}

// ---------------------------------------------------------------- readers

float FKeeperFightModel::GetPartHp(EKeeperPart Part) const
{
	return PartHp.IsValidIndex(PartIndex(Part)) ? PartHp[PartIndex(Part)] : 0.0f;
}

bool FKeeperFightModel::IsPartBroken(EKeeperPart Part) const
{
	return Part != EKeeperPart::Eye && Part != EKeeperPart::Clock && GetPartHp(Part) <= 0.0f;
}

float FKeeperFightModel::GetWorldScale() const
{
	return (SlowRemaining > 0.0f && BlackoutRemaining <= 0.0f) ? Tuning().SlowWorldScale : 1.0f;
}

bool FKeeperFightModel::IsPartEligible(EKeeperPart Part) const
{
	if (bEnded || TransitionRemaining > 0.0f || BlackoutRemaining > 0.0f)
	{
		return false;
	}
	switch (Part)
	{
	case EKeeperPart::Wings:
		return Phase == EKeeperPhase::Wings && GetPartHp(Part) > 0.0f;
	case EKeeperPart::Front:
		return Phase == EKeeperPhase::Mechanisms && GetPartHp(Part) > 0.0f;
	case EKeeperPart::Middle:
		return Phase == EKeeperPhase::Mechanisms && GetPartHp(Part) > 0.0f && IsPartBroken(EKeeperPart::Front);
	case EKeeperPart::Rear:
		return Phase == EKeeperPhase::Mechanisms && GetPartHp(Part) > 0.0f && IsPartBroken(EKeeperPart::Middle);
	case EKeeperPart::Clock:
	{
		if (Phase == EKeeperPhase::Wings || ClockOpenRemaining <= 0.0f)
		{
			return false;
		}
		const float Floor = (Phase == EKeeperPhase::Clock) ? 0.0f : Tuning().ClockReserveHp;
		return GetPartHp(Part) > Floor;
	}
	case EKeeperPart::Eye:
		return EyeWindowRemaining > 0.0f;
	default:
		return false;
	}
}

FVector2D FKeeperFightModel::GetMechanismHome(EKeeperPart Part) const
{
	switch (Part)
	{
	case EKeeperPart::Front: return Anchor + FVector2D(Tuning().FrontOffset);
	case EKeeperPart::Middle: return Anchor + FVector2D(Tuning().MiddleOffsetPos);
	case EKeeperPart::Rear: return Anchor + FVector2D(Tuning().RearOffset);
	default: return Anchor;
	}
}

bool FKeeperFightModel::IsPhysicalThreatening() const
{
	return Physical != EKeeperPhysical::None && Stage != EKeeperStage::Idle && Stage != EKeeperStage::Recovery;
}

bool FKeeperFightModel::IsHeadHurting() const
{
	return IsCastPhysical(Physical) && (Stage == EKeeperStage::Stroke || Stage == EKeeperStage::SecondStroke);
}

bool FKeeperFightModel::IsCastPhysical(EKeeperPhysical Kind) const
{
	return Kind == EKeeperPhysical::FrontCast || Kind == EKeeperPhysical::MiddleCurve || Kind == EKeeperPhysical::RearTwoStage;
}

EKeeperPart FKeeperFightModel::CastPart(EKeeperPhysical Kind) const
{
	switch (Kind)
	{
	case EKeeperPhysical::FrontCast: return EKeeperPart::Front;
	case EKeeperPhysical::MiddleCurve: return EKeeperPart::Middle;
	case EKeeperPhysical::RearTwoStage: return EKeeperPart::Rear;
	default: return EKeeperPart::Count;
	}
}

bool FKeeperFightModel::IsKindEnabled(EKeeperPhysical Kind) const
{
	switch (Kind)
	{
	case EKeeperPhysical::Gust: return Switches.bGust;
	case EKeeperPhysical::Talon: return Switches.bTalon;
	case EKeeperPhysical::FrontCast: return Switches.bFrontCast;
	case EKeeperPhysical::MiddleCurve: return Switches.bMiddleCast;
	case EKeeperPhysical::RearTwoStage: return Switches.bRearCast;
	default: return false;
	}
}

float FKeeperFightModel::RedSpeed() const
{
	switch (Phase)
	{
	case EKeeperPhase::Wings: return Tuning().RedSpeedWings;
	case EKeeperPhase::Mechanisms: return Tuning().RedSpeedMechanisms;
	default: return Tuning().RedSpeedClock;
	}
}

float FKeeperFightModel::RedSpread() const
{
	switch (Phase)
	{
	case EKeeperPhase::Wings: return Tuning().RedSpreadWingsDeg;
	case EKeeperPhase::Mechanisms: return Tuning().RedSpreadMechanismsDeg;
	default: return Tuning().RedSpreadClockDeg;
	}
}

float FKeeperFightModel::RedSize() const
{
	switch (Phase)
	{
	case EKeeperPhase::Wings: return Tuning().RedSizeWings;
	case EKeeperPhase::Mechanisms: return Tuning().RedSizeMechanisms;
	default: return Tuning().RedSizeClock;
	}
}

float FKeeperFightModel::YellowSpeed() const
{
	switch (Phase)
	{
	case EKeeperPhase::Wings: return Tuning().YellowSpeedWings;
	case EKeeperPhase::Mechanisms: return Tuning().YellowSpeedMechanisms;
	default: return Tuning().YellowSpeedClock;
	}
}

float FKeeperFightModel::SegmentDistance(const FVector2D& P, const FVector2D& A, const FVector2D& B) const
{
	const FVector2D AB = B - A;
	const float LenSq = AB.SizeSquared();
	if (LenSq <= UE_SMALL_NUMBER)
	{
		return FVector2D::Distance(P, A);
	}
	const float T = FMath::Clamp(FVector2D::DotProduct(P - A, AB) / LenSq, 0.0f, 1.0f);
	return FVector2D::Distance(P, A + AB * T);
}

// ---------------------------------------------------------------- tick

void FKeeperFightModel::Step(float UnscaledDeltaSeconds, const FKeeperTickInput& Input, TArray<FKeeperCommand>& Out)
{
	if (bEnded || UnscaledDeltaSeconds <= 0.0f)
	{
		return;
	}
	TickUnscaled(UnscaledDeltaSeconds, Out);
	if (bEnded)
	{
		return;
	}
	if (TransitionRemaining > 0.0f)
	{
		TransitionRemaining -= UnscaledDeltaSeconds;
		if (TransitionRemaining <= 0.0f)
		{
			FinishTransition(Out);
		}
		TickPending(UnscaledDeltaSeconds * GetWorldScale(), Out);
		return;
	}
	PhaseTime += UnscaledDeltaSeconds;
	const bool bFrozen = FirePauseRemaining > 0.0f || StunRemaining > 0.0f || BlackoutRemaining > 0.0f;
	const float WorldDt = UnscaledDeltaSeconds * GetWorldScale();
	if (FirePauseRemaining <= 0.0f && BlackoutRemaining <= 0.0f)
	{
		TickPending(WorldDt, Out);
	}
	if (!bFrozen)
	{
		TickAttacks(WorldDt, Input, Out);
		TickPhysical(WorldDt, Input, Out);
	}
}

void FKeeperFightModel::TickUnscaled(float Dt, TArray<FKeeperCommand>& Out)
{
	auto Emit = [&Out](EKeeperCommandType Type)
	{
		FKeeperCommand Cmd;
		Cmd.Type = Type;
		Out.Add(Cmd);
	};
	if (StunRemaining > 0.0f)
	{
		StunRemaining -= Dt;
		if (StunRemaining <= 0.0f)
		{
			StunRemaining = 0.0f;
			Emit(EKeeperCommandType::StunEnded);
		}
	}
	if (BlackoutRemaining > 0.0f)
	{
		BlackoutRemaining -= Dt;
		if (BlackoutRemaining <= 0.0f)
		{
			BlackoutRemaining = 0.0f;
			RedCountdown = Tuning().RedIntervalSeconds;
			YellowCountdown = Tuning().YellowIntervalSeconds;
			PhysicalCountdown = Tuning().PhysicalIntervalSeconds;
			Emit(EKeeperCommandType::BlackoutEnded);
		}
	}
	FirePauseRemaining = FMath::Max(0.0f, FirePauseRemaining - Dt);
	if (SlowRemaining > 0.0f)
	{
		SlowRemaining -= Dt;
		if (SlowRemaining <= 0.0f)
		{
			SlowRemaining = 0.0f;
			Emit(EKeeperCommandType::SlowEnded);
		}
	}
	SlowCooldownRemaining = FMath::Max(0.0f, SlowCooldownRemaining - Dt);
	EyeCooldownRemaining = FMath::Max(0.0f, EyeCooldownRemaining - Dt);
	if (EyeWindowRemaining > 0.0f)
	{
		EyeWindowRemaining -= Dt;
		if (EyeWindowRemaining <= 0.0f)
		{
			EyeWindowRemaining = 0.0f;
			Emit(EKeeperCommandType::EyeHidden);
		}
	}
	if (TransitionRemaining > 0.0f)
	{
		return;
	}
	if (ClockOpenRemaining > 0.0f)
	{
		ClockOpenRemaining -= Dt;
		if (ClockOpenRemaining <= 0.0f)
		{
			CloseClock(Out);
		}
	}
	else if (ClockProtectRemaining > 0.0f)
	{
		ClockProtectRemaining = FMath::Max(0.0f, ClockProtectRemaining - Dt);
	}
	if (Phase == EKeeperPhase::Clock)
	{
		FinalCycleTime += Dt;
		if (FinalCycleTime >= Tuning().FinalExposureCycleSeconds)
		{
			FinalCycleTime -= Tuning().FinalExposureCycleSeconds;
			OpenClock(Out, true);
		}
	}
}

void FKeeperFightModel::TickPending(float WorldDt, TArray<FKeeperCommand>& Out)
{
	for (int32 Index = 0; Index < Pending.Num();)
	{
		Pending[Index].DelayRemaining -= WorldDt;
		if (Pending[Index].DelayRemaining <= 0.0f)
		{
			Out.Add(Pending[Index].Command);
			Pending.RemoveAt(Index);
		}
		else
		{
			++Index;
		}
	}
}

void FKeeperFightModel::QueueShot(float Delay, EUmbrellaShotKind Kind, FName Name, const FVector2D& Origin, float AngleDeg, float Speed, float Radius)
{
	FPendingShot Shot;
	Shot.DelayRemaining = Delay;
	Shot.Command.Type = EKeeperCommandType::FireShot;
	Shot.Command.ShotKind = Kind;
	Shot.Command.Name = Name;
	Shot.Command.A = Origin;
	Shot.Command.B = Direction(AngleDeg) * Speed;
	Shot.Command.Value = Radius;
	Shot.Command.Damage = Tuning().ProjectileDamage;
	Shot.Command.Phase = Phase;
	Pending.Add(Shot);
}

void FKeeperFightModel::TickAttacks(float WorldDt, const FKeeperTickInput& Input, TArray<FKeeperCommand>& Out)
{
	RedCountdown -= WorldDt;
	YellowCountdown -= WorldDt;
	if (RedCountdown <= 0.0f)
	{
		if (Phase == EKeeperPhase::Clock)
		{
			if (Switches.bDoubleBeat)
			{
				StartDoubleBeat(Input);
			}
			else
			{
				RedCountdown = Tuning().RedIntervalSeconds;
			}
		}
		else if (Switches.bRed)
		{
			StartRedVolley(Input);
		}
		else
		{
			RedCountdown = Tuning().RedIntervalSeconds;
		}
	}
	if (YellowCountdown <= 0.0f)
	{
		if (Switches.bYellow)
		{
			StartYellow(Input);
		}
		else
		{
			YellowCountdown = Tuning().YellowIntervalSeconds;
		}
	}
}

void FKeeperFightModel::StartRedVolley(const FKeeperTickInput& Input)
{
	const bool bReduced = IsPhysicalThreatening();
	const int32 Count = bReduced ? 1 : Tuning().RedShotCount;
	const FVector2D Origin = GetMuzzle();
	const float Center = (Phase == EKeeperPhase::Wings)
		? FMath::RadiansToDegrees(FMath::Atan2(Input.PlayerPos.Y - Origin.Y, Input.PlayerPos.X - Origin.X))
		: Tuning().FixedLeftAngleDeg;
	for (int32 Index = 0; Index < Count; ++Index)
	{
		QueueShot(static_cast<float>(Index) * Tuning().RedSpacingSeconds, EUmbrellaShotKind::EnemyRed, RedFanName, Origin,
			FanAngleDeg(Center, RedSpread(), Index, Count), RedSpeed(), Tuning().RedBaseRadius * RedSize());
	}
	RedCountdown = bReduced ? Tuning().ReducedIntervalSeconds : Tuning().RedIntervalSeconds;
}

void FKeeperFightModel::StartDoubleBeat(const FKeeperTickInput& Input)
{
	const bool bReduced = IsPhysicalThreatening();
	const int32 Count = bReduced ? 1 : Tuning().RedShotCount;
	const FVector2D Origin = GetMuzzle();
	const float Center = FMath::RadiansToDegrees(FMath::Atan2(Input.PlayerPos.Y - Origin.Y, Input.PlayerPos.X - Origin.X));
	const float GroupSpan = static_cast<float>(Count - 1) * Tuning().RedSpacingSeconds;
	const float RepeatStart = GroupSpan + Tuning().BeatRepeatWaitSeconds;
	for (int32 Repeat = 0; Repeat < 2; ++Repeat)
	{
		for (int32 Index = 0; Index < Count; ++Index)
		{
			// The repeat flies the same captured paths: same origin, same angles, never re-aimed.
			QueueShot(static_cast<float>(Repeat) * RepeatStart + static_cast<float>(Index) * Tuning().RedSpacingSeconds,
				EUmbrellaShotKind::EnemyRed, BeatName, Origin, FanAngleDeg(Center, RedSpread(), Index, Count), RedSpeed(),
				Tuning().RedBaseRadius * RedSize());
		}
	}
	const float Natural = RepeatStart + GroupSpan + Tuning().BeatRecoverySeconds;
	RedCountdown = bReduced ? FMath::Max(Natural, Tuning().ReducedIntervalSeconds) : Natural;
}

void FKeeperFightModel::StartYellow(const FKeeperTickInput& Input)
{
	const FVector2D Origin = GetMuzzle();
	const float Angle = FMath::RadiansToDegrees(FMath::Atan2(Input.PlayerPos.Y - Origin.Y, Input.PlayerPos.X - Origin.X));
	for (int32 Index = 0; Index < Tuning().YellowShotCount; ++Index)
	{
		QueueShot(static_cast<float>(Index) * Tuning().RedSpacingSeconds, EUmbrellaShotKind::EnemyYellow, YellowName, Origin, Angle,
			YellowSpeed(), Tuning().RedBaseRadius * Tuning().YellowSize);
	}
	YellowCountdown = Tuning().YellowIntervalSeconds;
}

// ---------------------------------------------------------------- physical moves

EKeeperPhysical FKeeperFightModel::PickScheduled() const
{
	if (Phase == EKeeperPhase::Wings)
	{
		return (Switches.bGust && !IsPartBroken(EKeeperPart::Wings)) ? EKeeperPhysical::Gust : EKeeperPhysical::None;
	}
	if (Phase != EKeeperPhase::Mechanisms)
	{
		return EKeeperPhysical::None;
	}
	for (int32 Step = 0; Step < CastCycleNum; ++Step)
	{
		const EKeeperPhysical Kind = CastCycle[(NextCastIndex + Step) % CastCycleNum];
		if (IsKindEnabled(Kind) && !IsPartBroken(CastPart(Kind)))
		{
			return Kind;
		}
	}
	return EKeeperPhysical::None;
}

void FKeeperFightModel::TickPhysical(float WorldDt, const FKeeperTickInput& Input, TArray<FKeeperCommand>& Out)
{
	PhysicalCountdown -= WorldDt;
	TalonCooldown = FMath::Max(0.0f, TalonCooldown - WorldDt);
	const float TalonDistance = FVector2D::Distance(GetClaw(), Input.PlayerPos);
	if (TalonDistance > Tuning().TalonRearmExit)
	{
		bTalonArmed = true;
	}
	if (Stage == EKeeperStage::Idle)
	{
		if (Switches.bTalon && bTalonArmed && TalonCooldown <= 0.0f && PhaseTime >= Tuning().TalonFirstAtSeconds
			&& TalonDistance <= Tuning().TalonReach)
		{
			StartPhysical(EKeeperPhysical::Talon, Input, Out);
		}
		else if (PhysicalCountdown <= 0.0f)
		{
			const EKeeperPhysical Kind = PickScheduled();
			if (Kind != EKeeperPhysical::None)
			{
				StartPhysical(Kind, Input, Out);
			}
		}
		return;
	}

	// A broken mechanism cancels its own cast at once.
	if (IsCastPhysical(Physical) && IsPartBroken(CastPart(Physical)))
	{
		CancelPhysical(Out);
		return;
	}

	StageRemaining -= WorldDt;
	const float Duration = FMath::Max(StageDuration, UE_SMALL_NUMBER);
	const float Progress = FMath::Clamp(1.0f - StageRemaining / Duration, 0.0f, 1.0f);
	PrevHeadPos = HeadPos;

	switch (Physical)
	{
	case EKeeperPhysical::Gust:
		if (Stage == EKeeperStage::Stroke)
		{
			GustTravelled += Tuning().GustSpeed * WorldDt;
			GustFront.X = LockStart.X - GustTravelled;
			const bool bInBand = FMath::Abs(Input.PlayerPos.Y - GustBandZ) <= Tuning().GustBandWidth * 0.5f + Input.PlayerRadius;
			const bool bInFront = FMath::Abs(Input.PlayerPos.X - GustFront.X) <= Tuning().GustFrontThickness * 0.5f + Input.PlayerRadius;
			if (bInBand && bInFront)
			{
				if (!bDamagedThisCast)
				{
					bDamagedThisCast = true;
					EmitDamage(GustName, Tuning().GustDamage, Out);
				}
				FKeeperCommand Push;
				Push.Type = EKeeperCommandType::PushPlayer;
				Push.Physical = EKeeperPhysical::Gust;
				Push.Value = (Input.PlayerPos.Y >= GustBandZ) ? Tuning().GustPush : -Tuning().GustPush;
				Push.Serial = CastSerial;
				Out.Add(Push);
			}
		}
		break;
	case EKeeperPhysical::Talon:
		if (Stage == EKeeperStage::Stroke)
		{
			HeadPos = FMath::Lerp(LockStart, LockEnd, Progress);
			if (!bDamagedThisCast
				&& SegmentDistance(Input.PlayerPos, LockStart, HeadPos) <= Tuning().TalonTipWidth * 0.5f + Input.PlayerRadius)
			{
				bDamagedThisCast = true;
				EmitDamage(TalonName, Tuning().TalonDamage, Out);
			}
		}
		break;
	default:
		if (Stage == EKeeperStage::Stroke || Stage == EKeeperStage::SecondStroke)
		{
			// Rear: first stroke covers [0, 0.5] of the path, second [0.5, 1]. Others cover [0, 1] in one stroke.
			float PathT = Progress;
			if (Physical == EKeeperPhysical::RearTwoStage)
			{
				PathT = (Stage == EKeeperStage::Stroke) ? Progress * 0.5f : 0.5f + Progress * 0.5f;
			}
			const FVector2D Line = FMath::Lerp(LockStart, LockEnd, PathT);
			const FVector2D Axis = (LockEnd - LockStart).GetSafeNormal();
			const FVector2D Normal(-Axis.Y, Axis.X);
			const float Curve = (Physical == EKeeperPhysical::MiddleCurve) ? MiddleSign * Tuning().MiddleOffset * FMath::Sin(PI * PathT) : 0.0f;
			HeadPos = Line + Normal * Curve;
			if (!bDamagedThisCast
				&& SegmentDistance(Input.PlayerPos, PrevHeadPos, HeadPos) <= Tuning().ChainHeadWidth * 0.5f + Input.PlayerRadius)
			{
				bDamagedThisCast = true;
				EmitDamage(PhysicalName(Physical), Tuning().ChainDamage, Out);
			}
		}
		else if (Stage == EKeeperStage::Recovery)
		{
			HeadPos = FMath::Lerp(LockEnd, LockStart, Progress);
		}
		break;
	}

	if (StageRemaining > 0.0f)
	{
		return;
	}
	switch (Stage)
	{
	case EKeeperStage::Warning:
		if (Physical == EKeeperPhysical::Gust)
		{
			GustFront = FVector2D(LockStart.X, GustBandZ);
			GustTravelled = 0.0f;
		}
		EnterStage(EKeeperStage::Stroke,
			Physical == EKeeperPhysical::Gust ? Tuning().GustLifetimeSeconds
			: Physical == EKeeperPhysical::Talon ? Tuning().TalonStrikeSeconds
			: (Physical == EKeeperPhysical::RearTwoStage ? 0.5f : 1.0f) * Tuning().ChainReach / Tuning().ChainSpeed,
			Out);
		break;
	case EKeeperStage::Stroke:
		if (Physical == EKeeperPhysical::RearTwoStage)
		{
			EnterStage(EKeeperStage::Pause, Tuning().RearPauseSeconds, Out);
		}
		else if (Physical == EKeeperPhysical::Gust)
		{
			EnterRecovery(Tuning().GustRecoverySeconds, Out);
		}
		else if (Physical == EKeeperPhysical::Talon)
		{
			EnterRecovery(Tuning().TalonRecoverySeconds, Out);
		}
		else
		{
			EnterRecovery(Tuning().ChainReturnSeconds, Out);
		}
		break;
	case EKeeperStage::Pause:
		EnterStage(EKeeperStage::SecondStroke, 0.5f * Tuning().ChainReach / Tuning().ChainSpeed, Out);
		break;
	case EKeeperStage::SecondStroke:
		EnterRecovery(Tuning().ChainReturnSeconds, Out);
		break;
	case EKeeperStage::Recovery:
		Physical = EKeeperPhysical::None;
		Stage = EKeeperStage::Idle;
		HeadPos = GetClaw();
		break;
	default:
		break;
	}
}

void FKeeperFightModel::StartPhysical(EKeeperPhysical Kind, const FKeeperTickInput& Input, TArray<FKeeperCommand>& Out)
{
	Physical = Kind;
	++CastSerial;
	bDamagedThisCast = false;
	PhysicalCountdown = Tuning().PhysicalIntervalSeconds;
	FKeeperCommand Cmd;
	Cmd.Type = EKeeperCommandType::PhysicalWarning;
	Cmd.Physical = Kind;
	Cmd.Name = PhysicalName(Kind);
	Cmd.Serial = CastSerial;
	float Warning = Tuning().CastWarningSeconds;
	if (Kind == EKeeperPhysical::Gust)
	{
		Warning = Tuning().GustWarningSeconds;
		GustBandZ = Input.PlayerPos.Y;
		LockStart = GetMuzzle();
		LockEnd = FVector2D(LockStart.X - Tuning().GustSpeed * Tuning().GustLifetimeSeconds, GustBandZ);
		Cmd.A = FVector2D(LockStart.X, GustBandZ);
	}
	else if (Kind == EKeeperPhysical::Talon)
	{
		Warning = Tuning().TalonWarningSeconds;
		bTalonArmed = false;
		TalonCooldown = Tuning().TalonCooldownSeconds;
		LockStart = GetClaw();
		const FVector2D Dir = (Input.PlayerPos - LockStart).GetSafeNormal();
		LockEnd = LockStart + Dir * Tuning().TalonReach;
		HeadPos = LockStart;
		Cmd.A = LockStart;
		Cmd.B = LockEnd;
	}
	else
	{
		const int32 CycleIndex = static_cast<int32>(Kind) - static_cast<int32>(EKeeperPhysical::FrontCast);
		NextCastIndex = (CycleIndex + 1) % CastCycleNum;
		LockStart = GetMechanismHome(CastPart(Kind));
		const FVector2D Dir = (Input.PlayerPos - LockStart).GetSafeNormal();
		LockEnd = LockStart + (Dir.IsNearlyZero() ? FVector2D(-1.0f, 0.0f) : Dir) * Tuning().ChainReach;
		MiddleSign = MiddleSignForSerial(CastSerial);
		HeadPos = LockStart;
		Cmd.A = LockStart;
		Cmd.B = LockEnd;
	}
	PrevHeadPos = HeadPos;
	Out.Add(Cmd);
	Stage = EKeeperStage::Warning;
	StageDuration = Warning;
	StageRemaining = Warning;
}

void FKeeperFightModel::EnterStage(EKeeperStage NewStage, float Duration, TArray<FKeeperCommand>& Out)
{
	Stage = NewStage;
	StageDuration = Duration;
	StageRemaining = Duration;
	FKeeperCommand Cmd;
	Cmd.Type = EKeeperCommandType::PhysicalStrike;
	Cmd.Physical = Physical;
	Cmd.Name = PhysicalName(Physical);
	Cmd.Serial = CastSerial;
	Cmd.A = LockStart;
	Cmd.B = LockEnd;
	Cmd.Value = Duration;
	Out.Add(Cmd);
}

void FKeeperFightModel::EnterRecovery(float Duration, TArray<FKeeperCommand>& Out)
{
	Stage = EKeeperStage::Recovery;
	StageDuration = Duration;
	StageRemaining = Duration;
	// Recovery shortens the next yellow and keeps red from firing at once; a longer red delay is preserved.
	YellowCountdown = FMath::Min(YellowCountdown, Tuning().YellowRecoveryMaxSeconds);
	RedCountdown = FMath::Max(RedCountdown, Tuning().RedRecoveryMinSeconds);
	FKeeperCommand Cmd;
	Cmd.Type = EKeeperCommandType::PhysicalRecovery;
	Cmd.Physical = Physical;
	Cmd.Name = PhysicalName(Physical);
	Cmd.Serial = CastSerial;
	Cmd.Value = Duration;
	Out.Add(Cmd);
}

void FKeeperFightModel::CancelPhysical(TArray<FKeeperCommand>& Out)
{
	if (Physical == EKeeperPhysical::None)
	{
		return;
	}
	FKeeperCommand Cmd;
	Cmd.Type = EKeeperCommandType::PhysicalCancelled;
	Cmd.Physical = Physical;
	Cmd.Name = PhysicalName(Physical);
	Cmd.Serial = CastSerial;
	Out.Add(Cmd);
	Physical = EKeeperPhysical::None;
	Stage = EKeeperStage::Idle;
	StageRemaining = 0.0f;
	HeadPos = GetClaw();
}

void FKeeperFightModel::EmitDamage(FName Source, float Amount, TArray<FKeeperCommand>& Out)
{
	FKeeperCommand Cmd;
	Cmd.Type = EKeeperCommandType::DamagePlayer;
	Cmd.Name = Source;
	Cmd.Damage = Amount;
	Cmd.Serial = CastSerial;
	Out.Add(Cmd);
}

// ---------------------------------------------------------------- clock

void FKeeperFightModel::OpenClock(TArray<FKeeperCommand>& Out, bool bFinalCycle)
{
	if (!bFinalCycle && (ClockOpenRemaining > 0.0f || ClockProtectRemaining > 0.0f))
	{
		return; // repeated outer hits do not extend an opening, nor open during protection recovery
	}
	if (!Switches.bClockProtection && !bFinalCycle)
	{
		return;
	}
	ClockOpenRemaining = bFinalCycle ? Tuning().FinalExposureSeconds : Tuning().ClockOpenSeconds;
	ClockProtectRemaining = 0.0f;
	// A genuinely new opening resets the per-opening slow and eye flags and clears any earlier eye window.
	bSlowUsedThisOpening = false;
	bEyeUsedThisOpening = false;
	if (EyeWindowRemaining > 0.0f)
	{
		EyeWindowRemaining = 0.0f;
		FKeeperCommand Hide;
		Hide.Type = EKeeperCommandType::EyeHidden;
		Out.Add(Hide);
	}
	FirePauseRemaining = Tuning().FirePauseSeconds; // capped: a new opening never stacks pauses
	FKeeperCommand Cmd;
	Cmd.Type = EKeeperCommandType::ClockOpened;
	Cmd.Value = ClockOpenRemaining;
	Out.Add(Cmd);
}

void FKeeperFightModel::CloseClock(TArray<FKeeperCommand>& Out)
{
	ClockOpenRemaining = 0.0f;
	if (Phase != EKeeperPhase::Clock)
	{
		ClockProtectRemaining = Tuning().ClockProtectRecoverySeconds;
	}
	FKeeperCommand Cmd;
	Cmd.Type = EKeeperCommandType::ClockClosed;
	Out.Add(Cmd);
}

void FKeeperFightModel::StartEyeBlackout(TArray<FKeeperCommand>& Out)
{
	EyeWindowRemaining = 0.0f;
	EyeCooldownRemaining = Tuning().EyeCooldownSeconds;
	if (SlowRemaining > 0.0f)
	{
		SlowRemaining = 0.0f;
		FKeeperCommand End;
		End.Type = EKeeperCommandType::SlowEnded;
		Out.Add(End);
	}
	BlackoutRemaining = Tuning().BlackoutSeconds;
	// Blackout clears missiles, queued repeats, the physical move and gusts.
	Pending.Reset();
	CancelPhysical(Out);
	FKeeperCommand Hide;
	Hide.Type = EKeeperCommandType::EyeHidden;
	Out.Add(Hide);
	FKeeperCommand Black;
	Black.Type = EKeeperCommandType::BlackoutStarted;
	Black.Value = BlackoutRemaining;
	Out.Add(Black);
	FKeeperCommand Clear;
	Clear.Type = EKeeperCommandType::ClearProjectiles;
	Out.Add(Clear);
	FKeeperCommand Gusts;
	Gusts.Type = EKeeperCommandType::ClearGusts;
	Out.Add(Gusts);
}

void FKeeperFightModel::EndEffects(TArray<FKeeperCommand>& Out)
{
	if (SlowRemaining > 0.0f)
	{
		FKeeperCommand Cmd;
		Cmd.Type = EKeeperCommandType::SlowEnded;
		Out.Add(Cmd);
	}
	if (EyeWindowRemaining > 0.0f)
	{
		FKeeperCommand Cmd;
		Cmd.Type = EKeeperCommandType::EyeHidden;
		Out.Add(Cmd);
	}
	if (BlackoutRemaining > 0.0f)
	{
		FKeeperCommand Cmd;
		Cmd.Type = EKeeperCommandType::BlackoutEnded;
		Out.Add(Cmd);
	}
	if (StunRemaining > 0.0f)
	{
		FKeeperCommand Cmd;
		Cmd.Type = EKeeperCommandType::StunEnded;
		Out.Add(Cmd);
	}
	SlowRemaining = 0.0f;
	EyeWindowRemaining = 0.0f;
	BlackoutRemaining = 0.0f;
	StunRemaining = 0.0f;
	FirePauseRemaining = 0.0f;
	ClockOpenRemaining = 0.0f;
}

// ---------------------------------------------------------------- player hits

FKeeperHitResult FKeeperFightModel::ApplyPlayerHit(EKeeperPart Part, float Damage, TArray<FKeeperCommand>& Out)
{
	FKeeperHitResult Result;
	Result.HpAfter = GetPartHp(Part);
	if (bEnded || Part == EKeeperPart::Count || Damage <= 0.0f)
	{
		return Result;
	}
	// A broken part (wings or mechanism) is cover only: shots pass through.
	if (IsPartBroken(Part))
	{
		return Result;
	}
	if (Part == EKeeperPart::Eye)
	{
		if (EyeWindowRemaining <= 0.0f)
		{
			return Result;
		}
		Result.Outcome = EKeeperHitOutcome::Blocked;
		StartEyeBlackout(Out);
		return Result;
	}
	if (!IsPartEligible(Part))
	{
		Result.Outcome = EKeeperHitOutcome::Blocked;
		return Result;
	}

	const float Before = PartHp[PartIndex(Part)];
	if (Part == EKeeperPart::Clock)
	{
		const float Floor = (Phase == EKeeperPhase::Clock) ? 0.0f : Tuning().ClockReserveHp;
		PartHp[PartIndex(Part)] = FMath::Max(Floor, Before - Damage);
		Result.Outcome = EKeeperHitOutcome::Damaged;
		Result.bClockHpReduced = PartHp[PartIndex(Part)] < Before;
		Result.HpAfter = PartHp[PartIndex(Part)];
		if (Result.bClockHpReduced)
		{
			if (Phase == EKeeperPhase::Clock && PartHp[PartIndex(Part)] <= 0.0f)
			{
				Result.bBroke = true;
				Result.bFightWon = true;
				FKeeperCommand Cmd;
				Cmd.Type = EKeeperCommandType::PartBroken;
				Cmd.Part = Part;
				Out.Add(Cmd);
				Halt(Out);
				FKeeperCommand Win;
				Win.Type = EKeeperCommandType::FightWon;
				Win.Value = Tuning().DepartureSeconds;
				Out.Add(Win);
				return Result;
			}
			// The qualifying hit: slow and eye, each at most once per opening.
			const bool bSlowReady = Switches.bSlow && Tuning().bSlowEnabled && !bSlowUsedThisOpening && SlowCooldownRemaining <= 0.0f;
			if (bSlowReady)
			{
				bSlowUsedThisOpening = true;
				SlowRemaining = Tuning().SlowSeconds;
				SlowCooldownRemaining = Tuning().SlowSeconds + Tuning().SlowCooldownSeconds;
				FKeeperCommand Cmd;
				Cmd.Type = EKeeperCommandType::SlowStarted;
				Cmd.Value = Tuning().SlowSeconds;
				Out.Add(Cmd);
			}
			const bool bEyeAllowed = Switches.bEye && ((Switches.bSlow && Tuning().bSlowEnabled) || Tuning().bEyeWhenSlowOff);
			if (bEyeAllowed && !bEyeUsedThisOpening && EyeCooldownRemaining <= 0.0f)
			{
				bEyeUsedThisOpening = true;
				EyeWindowRemaining = Tuning().EyeWindowSeconds;
				FKeeperCommand Cmd;
				Cmd.Type = EKeeperCommandType::EyeShown;
				Cmd.Value = Tuning().EyeWindowSeconds;
				Out.Add(Cmd);
			}
		}
		return Result;
	}

	PartHp[PartIndex(Part)] = FMath::Max(0.0f, Before - Damage);
	Result.Outcome = EKeeperHitOutcome::Damaged;
	Result.HpAfter = PartHp[PartIndex(Part)];
	if (Result.HpAfter <= 0.0f)
	{
		BreakPart(Part, Out, Result);
	}
	else if (Phase == EKeeperPhase::Mechanisms)
	{
		OpenClock(Out, false); // an outer hit opens the clock
	}
	return Result;
}

void FKeeperFightModel::BreakPart(EKeeperPart Part, TArray<FKeeperCommand>& Out, FKeeperHitResult& Result)
{
	Result.bBroke = true;
	FKeeperCommand Cmd;
	Cmd.Type = EKeeperCommandType::PartBroken;
	Cmd.Part = Part;
	Out.Add(Cmd);
	if (Part == EKeeperPart::Wings)
	{
		// Wing depletion stops new gusts and removes active fronts; shots in flight are cleared (phase-change rule).
		if (Physical == EKeeperPhysical::Gust)
		{
			CancelPhysical(Out);
		}
		FKeeperCommand Gusts;
		Gusts.Type = EKeeperCommandType::ClearGusts;
		Out.Add(Gusts);
		FKeeperCommand Clear;
		Clear.Type = EKeeperCommandType::ClearProjectiles;
		Out.Add(Clear);
		Pending.Reset();
		StartTransition(EKeeperPhase::Mechanisms, Out);
		Result.bPhaseAdvanced = true;
		return;
	}
	// A mechanism: cancel its cast, open the clock, stun, and clear gusts.
	if (CastPart(Physical) == Part)
	{
		CancelPhysical(Out);
	}
	OpenClock(Out, false);
	if (Switches.bBreakStun)
	{
		StunRemaining = Tuning().BreakStunSeconds;
		FKeeperCommand Stun;
		Stun.Type = EKeeperCommandType::StunStarted;
		Stun.Value = StunRemaining;
		Out.Add(Stun);
		CancelPhysical(Out);
		FKeeperCommand Gusts;
		Gusts.Type = EKeeperCommandType::ClearGusts;
		Out.Add(Gusts);
	}
	if (IsPartBroken(EKeeperPart::Front) && IsPartBroken(EKeeperPart::Middle) && IsPartBroken(EKeeperPart::Rear))
	{
		StartTransition(EKeeperPhase::Clock, Out);
		Result.bPhaseAdvanced = true;
	}
}

FVector2D FKeeperFightModel::GetMuzzle() const { return Anchor + FVector2D(Tuning().MuzzleOffset); }
FVector2D FKeeperFightModel::GetClaw() const { return Anchor + FVector2D(Tuning().ClawOffset); }
