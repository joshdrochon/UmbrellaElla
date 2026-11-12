#include "Enemy/EnemyModel.h"

#include "Owl/KeeperTuning.h"

FEnemyProfile FEnemyModel::ProfileFor(EEnemyType Type, const FKeeperTuning& Tuning)
{
	FEnemyProfile Profile;
	switch (Type)
	{
	case EEnemyType::Floodstrider:
		Profile.Hp = Tuning.FloodstriderHp;
		Profile.PatrolSpan = Tuning.FloodstriderPatrolSpan;
		Profile.PatrolSpeed = Tuning.FloodstriderPatrolSpeed;
		Profile.AimSeconds = Tuning.FloodstriderAimSeconds;
		Profile.ShotSpeed = Tuning.FloodstriderShotSpeed;
		Profile.RecoverySeconds = Tuning.FloodstriderRecoverySeconds;
		Profile.CycleSeconds = Tuning.FloodstriderCycleSeconds;
		break;
	case EEnemyType::SkyCourier:
		Profile.Hp = Tuning.CourierHp;
		Profile.PatrolSpan = Tuning.CourierPatrolSpan;
		Profile.PatrolSpeed = Tuning.CourierPatrolSpeed;
		Profile.AimSeconds = Tuning.CourierAimSeconds;
		Profile.ShotSpeed = Tuning.CourierShotSpeed;
		Profile.RecoverySeconds = Tuning.CourierRecoverySeconds;
		Profile.CycleSeconds = Tuning.CourierCycleSeconds;
		Profile.MaxEmissions = Tuning.CourierMaxEmissions;
		Profile.bAirborne = true;
		break;
	default:
		Profile.Hp = Tuning.RoadwardenHp;
		Profile.PatrolSpan = Tuning.RoadwardenPatrolSpan;
		Profile.PatrolSpeed = Tuning.RoadwardenPatrolSpeed;
		Profile.AimSeconds = Tuning.RoadwardenAimSeconds;
		Profile.ShotSpeed = Tuning.RoadwardenShotSpeed;
		Profile.RecoverySeconds = Tuning.RoadwardenRecoverySeconds;
		Profile.CycleSeconds = Tuning.RoadwardenCycleSeconds;
		break;
	}
	return Profile;
}

TArray<EUmbrellaShotKind> FEnemyModel::AssignShotColors(int32 Count, const TArray<int32>& ReservedYellow, int32 RedPerYellow)
{
	TArray<EUmbrellaShotKind> Colors;
	Colors.Init(EUmbrellaShotKind::EnemyRed, FMath::Max(0, Count));
	// The level-wide target: one yellow for every (RedPerYellow + 1) enemies, rounded to the nearest whole enemy.
	const int32 Group = FMath::Max(1, RedPerYellow) + 1;
	const int32 Target = FMath::RoundToInt(static_cast<float>(Count) / static_cast<float>(Group));
	int32 Yellow = 0;
	// Reserved authored catch lanes come first.
	for (int32 Index : ReservedYellow)
	{
		if (Colors.IsValidIndex(Index) && Colors[Index] != EUmbrellaShotKind::EnemyYellow)
		{
			Colors[Index] = EUmbrellaShotKind::EnemyYellow;
			++Yellow;
		}
	}
	// Then spread the remaining yellows evenly over the unreserved enemies.
	for (int32 Index = 0; Index < Colors.Num() && Yellow < Target; ++Index)
	{
		const bool bSlot = (Index % Group) == (Group - 1);
		if (bSlot && Colors[Index] == EUmbrellaShotKind::EnemyRed)
		{
			Colors[Index] = EUmbrellaShotKind::EnemyYellow;
			++Yellow;
		}
	}
	return Colors;
}

void FEnemyModel::Init(EEnemyType InType, const FEnemyProfile& InProfile, EUmbrellaShotKind InColor, const FVector2D& InHome, float SupportMinX, float SupportMaxX)
{
	Type = InType;
	Profile = InProfile;
	Color = InColor;
	Home = InHome;
	const float Half = Profile.PatrolSpan * 0.5f;
	PatrolMinX = FMath::Max(SupportMinX, Home.X - Half);
	PatrolMaxX = FMath::Min(SupportMaxX, Home.X + Half);
	if (PatrolMaxX < PatrolMinX)
	{
		PatrolMinX = Home.X;
		PatrolMaxX = Home.X;
	}
	Reset();
}

void FEnemyModel::Reset()
{
	Position = Home;
	Position.X = FMath::Clamp(Position.X, PatrolMinX, PatrolMaxX);
	State = EEnemyState::Patrol;
	Hp = Profile.Hp;
	StateTime = 0.0f;
	PatrolDirection = -1.0f;
	bAimLocked = false;
	EmissionsUsed = 0;
}

int32 FEnemyModel::GetEmissionsLeft() const
{
	return Profile.MaxEmissions > 0 ? FMath::Max(0, Profile.MaxEmissions - EmissionsUsed) : INT32_MAX;
}

void FEnemyModel::Enter(EEnemyState NewState, TArray<FEnemyCommand>& Out)
{
	State = NewState;
	StateTime = 0.0f;
	FEnemyCommand Cmd;
	Cmd.Type = EEnemyCommandType::StateChanged;
	Cmd.State = NewState;
	Cmd.A = Position;
	Out.Add(Cmd);
}

void FEnemyModel::ApplyHit(float Damage, TArray<FEnemyCommand>& Out)
{
	if (!IsAlive() || Damage <= 0.0f)
	{
		return;
	}
	Hp = FMath::Max(0.0f, Hp - Damage);
	if (Hp <= 0.0f)
	{
		// Zero HP: no new and no delayed fire, no contact damage; the shot already launched keeps flying.
		Enter(EEnemyState::Defeated, Out);
		FEnemyCommand Cmd;
		Cmd.Type = EEnemyCommandType::Defeated;
		Cmd.A = Position;
		Out.Add(Cmd);
	}
}

void FEnemyModel::Step(float DeltaSeconds, const FVector2D& PlayerPos, const FKeeperTuning& Tuning, TArray<FEnemyCommand>& Out)
{
	if (!IsAlive() || DeltaSeconds <= 0.0f)
	{
		return;
	}
	StateTime += DeltaSeconds;
	switch (State)
	{
	case EEnemyState::Patrol:
	{
		const float Next = Position.X + PatrolDirection * Profile.PatrolSpeed * DeltaSeconds;
		Position.X = FMath::Clamp(Next, PatrolMinX, PatrolMaxX);
		if (Next <= PatrolMinX)
		{
			PatrolDirection = 1.0f;
		}
		else if (Next >= PatrolMaxX)
		{
			PatrolDirection = -1.0f;
		}
		// The cycle is patrol + aim + recovery; patrol lasts what is left of the cycle.
		const float PatrolTime = FMath::Max(0.0f, Profile.CycleSeconds - Profile.AimSeconds - Profile.RecoverySeconds);
		const bool bTargetAhead = PlayerPos.X < Position.X;
		if (StateTime >= PatrolTime && bTargetAhead)
		{
			// The shot direction is committed when the aim starts and never tracks afterwards.
			LockedAim = (PlayerPos - Position).GetSafeNormal();
			bAimLocked = true;
			Enter(EEnemyState::Aim, Out);
		}
		break;
	}
	case EEnemyState::Aim:
		if (StateTime >= Profile.AimSeconds)
		{
			FEnemyCommand Cmd;
			Cmd.Type = EEnemyCommandType::FireShot;
			Cmd.ShotKind = Color;
			Cmd.A = Position + FVector2D(0.0f, Tuning.EnemyMuzzleLift);
			Cmd.B = LockedAim * Profile.ShotSpeed;
			Cmd.Slot = EmissionsUsed;
			Out.Add(Cmd);
			++EmissionsUsed;
			bAimLocked = false;
			Enter(EEnemyState::Recovery, Out);
		}
		break;
	case EEnemyState::Recovery:
		if (StateTime >= Profile.RecoverySeconds)
		{
			if (Profile.MaxEmissions > 0 && EmissionsUsed >= Profile.MaxEmissions)
			{
				Enter(EEnemyState::Withdrawn, Out);
				FEnemyCommand Cmd;
				Cmd.Type = EEnemyCommandType::Withdrawn;
				Cmd.A = Position;
				Out.Add(Cmd);
			}
			else
			{
				Enter(EEnemyState::Patrol, Out);
			}
		}
		break;
	default:
		break;
	}
}
