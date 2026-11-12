#include "Enemy/EnemyRules.h"
#include "Enemy/EnemyTuning.h"

float FEnemyProfile::GetPostFireSeconds() const
{
	return FMath::Max(RecoverySeconds, CycleSeconds - AimSeconds);
}

float FEnemyProfile::GetShotLifetime() const
{
	return ShotSpeed > 0.0f ? Range / ShotSpeed : 0.0f;
}

void FEnemyBrain::Reset(const FEnemyProfile& Profile)
{
	State = EEnemyState::Patrol;
	StateTime = 0.0f;
	PatrolOffset = 0.0f;
	PatrolDirection = 1.0f;
	Hp = Profile.Hp;
}

EEnemyBrainEvent FEnemyBrain::Advance(const FEnemyProfile& Profile, float DeltaTime, bool bTargetInWindow, bool bHasEmissionsLeft)
{
	if (State == EEnemyState::Defeated || State == EEnemyState::Withdrawn)
	{
		return EEnemyBrainEvent::None;
	}
	StateTime += DeltaTime;
	switch (State)
	{
	case EEnemyState::Patrol:
		if (!bHasEmissionsLeft)
		{
			State = EEnemyState::Withdrawn;
			StateTime = 0.0f;
			return EEnemyBrainEvent::Withdraw;
		}
		if (bTargetInWindow)
		{
			State = EEnemyState::Aim;
			StateTime = 0.0f;
			break;
		}
		{
			const float Half = Profile.PatrolSpan * 0.5f;
			PatrolOffset += PatrolDirection * Profile.PatrolSpeed * DeltaTime;
			if (PatrolOffset > Half)
			{
				PatrolOffset = Half;
				PatrolDirection = -1.0f;
			}
			else if (PatrolOffset < -Half)
			{
				PatrolOffset = -Half;
				PatrolDirection = 1.0f;
			}
		}
		break;
	case EEnemyState::Aim:
		if (StateTime >= Profile.AimSeconds)
		{
			State = EEnemyState::Recovery;
			StateTime = 0.0f;
			return EEnemyBrainEvent::ReleaseShot;
		}
		break;
	case EEnemyState::Recovery:
		if (StateTime >= Profile.GetPostFireSeconds())
		{
			State = EEnemyState::Patrol;
			StateTime = 0.0f;
		}
		break;
	default:
		break;
	}
	return EEnemyBrainEvent::None;
}

float FEnemyBrain::ApplyDamage(float Damage)
{
	if (State == EEnemyState::Defeated)
	{
		return Hp;
	}
	Hp = FMath::Max(0.0f, Hp - FMath::Max(0.0f, Damage));
	if (Hp <= 0.0f)
	{
		State = EEnemyState::Defeated;
		StateTime = 0.0f;
	}
	return Hp;
}

void FCourierPackets::Reset(int32 SlotCount)
{
	SlotTotal = FMath::Max(0, SlotCount);
	NextSlot = 0;
	SeenCallbacks.Reset();
}

int32 FCourierPackets::TakeNextSlot()
{
	if (NextSlot >= SlotTotal)
	{
		return INDEX_NONE;
	}
	return NextSlot++;
}

int32 FCourierPackets::GetRemaining() const
{
	return SlotTotal - NextSlot;
}

bool FCourierPackets::IsExhausted() const
{
	return NextSlot >= SlotTotal;
}

int32 FCourierPackets::RecordCallback(int32 Serial)
{
	int32& Seen = SeenCallbacks.FindOrAdd(Serial);
	return ++Seen;
}

FEnemyProfile FEnemyRules::MakeProfile(EEnemyType Type, const FEnemyTuning& Tuning)
{
	FEnemyProfile Profile;
	Profile.Damage = Tuning.IncomingDamage;
	Profile.ShotRadius = Tuning.ShotRadius;
	Profile.Range = Tuning.ShotRange;
	switch (Type)
	{
	case EEnemyType::Roadwarden:
		Profile.Hp = Tuning.RoadwardenHp;
		Profile.PatrolSpan = Tuning.RoadwardenPatrolSpan;
		Profile.PatrolSpeed = Tuning.RoadwardenPatrolSpeed;
		Profile.AimSeconds = Tuning.RoadwardenAimSeconds;
		Profile.ShotSpeed = Tuning.RoadwardenShotSpeed;
		Profile.RecoverySeconds = Tuning.RoadwardenRecoverySeconds;
		Profile.CycleSeconds = Tuning.RoadwardenCycleSeconds;
		Profile.Body = Tuning.RoadwardenTorso;
		break;
	case EEnemyType::Floodstrider:
		Profile.Hp = Tuning.FloodstriderHp;
		Profile.PatrolSpan = Tuning.FloodstriderPatrolSpan;
		Profile.PatrolSpeed = Tuning.FloodstriderPatrolSpeed;
		Profile.AimSeconds = Tuning.FloodstriderAimSeconds;
		Profile.ShotSpeed = Tuning.FloodstriderShotSpeed;
		Profile.RecoverySeconds = Tuning.FloodstriderRecoverySeconds;
		Profile.CycleSeconds = Tuning.FloodstriderCycleSeconds;
		Profile.Body = Tuning.FloodstriderTorso;
		break;
	case EEnemyType::SkyCourier:
		Profile.Hp = Tuning.CourierHp;
		Profile.PatrolSpan = Tuning.CourierPatrolSpan;
		Profile.PatrolSpeed = Tuning.CourierPatrolSpeed;
		Profile.AimSeconds = Tuning.CourierAimSeconds;
		Profile.ShotSpeed = Tuning.CourierShotSpeed;
		Profile.RecoverySeconds = Tuning.CourierRecoverySeconds;
		Profile.CycleSeconds = Tuning.CourierCycleSeconds;
		Profile.Body = Tuning.CourierBody;
		break;
	default:
		break;
	}
	return Profile;
}

bool FEnemyRules::IsTargetInFiringWindow(const FVector& Enemy, const FVector& Target, const FEnemyProfile& Profile)
{
	const double Ahead = Enemy.X - Target.X;
	if (Ahead <= 0.0 || Target.Z > Enemy.Z + Profile.Body.Y)
	{
		return false;
	}
	return FVector2D(Enemy.X - Target.X, Enemy.Z - Target.Z).Size() <= Profile.Range;
}

FVector FEnemyRules::AimVelocity(const FVector& Muzzle, const FVector& Target, float Speed)
{
	FVector Direction(Target.X - Muzzle.X, 0.0, Target.Z - Muzzle.Z);
	if (!Direction.Normalize())
	{
		Direction = FVector(-1.0, 0.0, 0.0);
	}
	return Direction * Speed;
}

FUmbrellaShotSpec FEnemyRules::MakeShot(const FEnemyProfile& Profile, EUmbrellaShotKind Kind, const FVector& Muzzle, const FVector& Target, FName SourceId)
{
	FUmbrellaShotSpec Spec;
	Spec.Kind = Kind;
	Spec.Origin = Muzzle;
	Spec.Velocity = AimVelocity(Muzzle, Target, Profile.ShotSpeed);
	Spec.Radius = Profile.ShotRadius;
	Spec.Damage = Profile.Damage;
	Spec.LifetimeSeconds = Profile.GetShotLifetime();
	Spec.SourceId = SourceId;
	return Spec;
}

TArray<EUmbrellaShotKind> FEnemyRules::AssignShotColors(int32 Count, int32 Reserved, int32 RedPerYellow, FRandomStream& Stream)
{
	TArray<EUmbrellaShotKind> Colors;
	const int32 Total = FMath::Max(0, Count);
	const int32 Target = Total / (FMath::Max(0, RedPerYellow) + 1);
	const int32 Yellow = FMath::Clamp(FMath::Max(Target, Reserved), 0, Total);
	const int32 Pinned = FMath::Clamp(Reserved, 0, Total);
	for (int32 Index = 0; Index < Total; ++Index)
	{
		Colors.Add(Index < Yellow ? EUmbrellaShotKind::EnemyYellow : EUmbrellaShotKind::EnemyRed);
	}
	// Shuffle only the unreserved tail so the reserved early yellows stay first.
	for (int32 Index = Total - 1; Index > Pinned; --Index)
	{
		const int32 Pick = Stream.RandRange(Pinned, Index);
		Colors.Swap(Index, Pick);
	}
	return Colors;
}

bool FEnemyRules::IsDamagingShot(const FUmbrellaShotSpec& Shot)
{
	return Shot.Kind == EUmbrellaShotKind::PlayerBlast;
}
