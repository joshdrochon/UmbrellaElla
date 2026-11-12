#include "Trap/TrapRules.h"
#include "Enemy/EnemyTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Trap/TrapTuning.h"

float FTrapCycle::GetCycleSeconds() const
{
	return WarningSeconds + ActiveSeconds + RecoverySeconds;
}

ETrapPhase FTrapCycle::PhaseAt(float Time) const
{
	const float Cycle = GetCycleSeconds();
	if (Cycle <= 0.0f)
	{
		return ETrapPhase::Recovery;
	}
	const float Local = FMath::Fmod(FMath::Max(0.0f, Time), Cycle);
	if (Local < WarningSeconds)
	{
		return ETrapPhase::Warning;
	}
	return Local < WarningSeconds + ActiveSeconds ? ETrapPhase::Active : ETrapPhase::Recovery;
}

void FContactGate::Advance(float DeltaTime)
{
	for (TPair<FName, float>& Pair : Remaining)
	{
		Pair.Value = FMath::Max(0.0f, Pair.Value - DeltaTime);
	}
}

float FContactGate::ConsumeHit(FName Victim, float Damage, float ProtectionSeconds)
{
	float& Left = Remaining.FindOrAdd(Victim);
	if (Left > 0.0f)
	{
		return 0.0f;
	}
	Left = ProtectionSeconds;
	return Damage;
}

FTrapCycle FTrapRules::MakeCycle(ETrapKind Kind, const FTrapTuning& Tuning)
{
	FTrapCycle Cycle;
	if (Kind == ETrapKind::TimedShutter && IsFeatureEnabled(EFeatureId::HAZ_20))
	{
		Cycle.WarningSeconds = Tuning.ShutterWarningSeconds;
		Cycle.ActiveSeconds = Tuning.ShutterStrikeSeconds;
		Cycle.RecoverySeconds = Tuning.ShutterRecoverySeconds;
	}
	else if (Kind == ETrapKind::HostileBellows && IsFeatureEnabled(EFeatureId::HAZ_21))
	{
		Cycle.WarningSeconds = Tuning.BellowsWarningSeconds;
		Cycle.ActiveSeconds = Tuning.BellowsGustSeconds;
		Cycle.RecoverySeconds = Tuning.BellowsRecoverySeconds;
	}
	return Cycle;
}

bool FTrapRules::IsPhaseDamaging(ETrapKind Kind, ETrapPhase Phase)
{
	switch (Kind)
	{
	case ETrapKind::AirMill:
		return IsFeatureEnabled(EFeatureId::HAZ_19);
	case ETrapKind::RoofTeeth:
		return IsFeatureEnabled(EFeatureId::HAZ_22);
	case ETrapKind::TimedShutter:
	case ETrapKind::HostileBellows:
		return Phase == ETrapPhase::Active;
	default:
		return false;
	}
}

bool FTrapRules::IsInsideSweptDisk(const FVector& Point, const FVector& Centre, float Radius)
{
	return FVector2D(Point.X - Centre.X, Point.Z - Centre.Z).SizeSquared() <= FMath::Square(Radius);
}

float FTrapRules::BladeAngle(float Time, float DegreesPerSecond)
{
	return FMath::Fmod(Time * DegreesPerSecond, TrapConst::FullTurnDegrees);
}

FVector FTrapRules::BellowsPush(float PushSpeed)
{
	return FVector(-PushSpeed, 0.0, -PushSpeed).GetClampedToMaxSize(PushSpeed);
}

FName FTrapRules::KindName(ETrapKind Kind)
{
	switch (Kind)
	{
	case ETrapKind::AirMill:
		return FName(TEXT("AirMill"));
	case ETrapKind::TimedShutter:
		return FName(TEXT("TimedShutter"));
	case ETrapKind::HostileBellows:
		return FName(TEXT("HostileBellows"));
	case ETrapKind::RoofTeeth:
		return FName(TEXT("RoofTeeth"));
	default:
		return NAME_None;
	}
}

TArray<EPressureViolation> FPressureContract::Evaluate(const FPressureChunk& Chunk, const FEnemyTuning& Tuning)
{
	TArray<EPressureViolation> Out;
	if (!IsFeatureEnabled(EFeatureId::HAZ_23))
	{
		return Out;
	}
	const int32 EnemyCount = Chunk.Enemies.Num();
	if (Chunk.Stage == EPressureStage::Early && EnemyCount + Chunk.TrapCount > 1)
	{
		Out.Add(EPressureViolation::TooManyProblemsEarly);
	}
	if (Chunk.TimingDemandsInCrossing > Tuning.MaxTimingDemandsInCrossing)
	{
		Out.Add(EPressureViolation::TooManyTimingDemands);
	}
	if (Chunk.bIsIntroduction && EnemyCount > 1)
	{
		Out.Add(EPressureViolation::IntroductionNotSingleEnemy);
	}
	TSet<EEnemyType> Kinds;
	bool bUntaught = false;
	bool bSpawnOnPlayer = false;
	bool bOffscreen = false;
	bool bNeighbor = false;
	for (const FPressureEnemy& Enemy : Chunk.Enemies)
	{
		Kinds.Add(Enemy.Type);
		bUntaught |= !Chunk.bIsIntroduction && Chunk.Stage == EPressureStage::Later && !Chunk.TaughtTypes.Contains(Enemy.Type);
		bSpawnOnPlayer |= FVector2D(Enemy.Location.X - Chunk.PlayerLocation.X, Enemy.Location.Z - Chunk.PlayerLocation.Z).Size() < Tuning.MinSpawnDistanceFromPlayer;
		bOffscreen |= !Enemy.bOnscreen;
		bNeighbor |= Enemy.bFromClearedNeighbor;
	}
	if (Kinds.Num() > Tuning.MaxMixedEnemyKinds)
	{
		Out.Add(EPressureViolation::MixedChunkTooManyKinds);
	}
	if (bUntaught)
	{
		Out.Add(EPressureViolation::UntaughtEnemy);
	}
	if (bSpawnOnPlayer)
	{
		Out.Add(EPressureViolation::SpawnOnPlayer);
	}
	if (bOffscreen)
	{
		Out.Add(EPressureViolation::AttackFromOffscreen);
	}
	if (bNeighbor)
	{
		Out.Add(EPressureViolation::AttackFromClearedNeighbor);
	}
	if (Chunk.bFireSealsEscape)
	{
		Out.Add(EPressureViolation::FireSealsEscape);
	}
	return Out;
}
