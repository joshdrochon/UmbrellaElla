#include "Feedback/Vfx/KeeperVfxRules.h"
#include "Core/UmbrellaSourceIds.h"

namespace
{
	bool IsKeeperVfxStroke(EKeeperStage Stage)
	{
		return Stage == EKeeperStage::Stroke || Stage == EKeeperStage::SecondStroke;
	}

	void AddKeeperVfxCue(TArray<FKeeperVfxCue>& Out, FName Key, bool bStart, EKeeperVfxAnchor Anchor)
	{
		if (!Key.IsNone())
		{
			Out.Add({ Key, bStart, Anchor });
		}
	}

	void AddKeeperVfxToggle(TArray<FKeeperVfxCue>& Out, bool bBefore, bool bAfter, FName Key, EKeeperVfxAnchor Anchor)
	{
		if (bBefore != bAfter)
		{
			AddKeeperVfxCue(Out, Key, bAfter, Anchor);
		}
	}
}

FKeeperVfxSnapshot KeeperVfxRules::Read(const FKeeperFightModel& Model, bool bFightActive, bool bDeparting)
{
	FKeeperVfxSnapshot Snapshot;
	Snapshot.bFightActive = bFightActive;
	Snapshot.bDeparting = bDeparting;
	if (bFightActive)
	{
		Snapshot.Physical = Model.GetPhysical();
		Snapshot.Stage = Model.GetStage();
		Snapshot.bClockOpen = Model.IsClockOpen();
		Snapshot.bEyeExposed = Model.IsEyeExposed();
		Snapshot.bSlowed = Model.IsSlowed();
		Snapshot.bStunned = Model.IsStunned();
		Snapshot.bBlackedOut = Model.IsBlackedOut();
	}
	return Snapshot;
}

FName KeeperVfxRules::WarningKey(EKeeperPhysical Physical)
{
	switch (Physical)
	{
	case EKeeperPhysical::Gust: return TEXT("GustWarning");
	case EKeeperPhysical::Talon: return TEXT("TalonWarning");
	case EKeeperPhysical::FrontCast: return TEXT("MechFrontWarning");
	case EKeeperPhysical::MiddleCurve: return TEXT("MechMiddleWarning");
	case EKeeperPhysical::RearTwoStage: return TEXT("MechRearWarning");
	default: return NAME_None;
	}
}

FName KeeperVfxRules::StrikeKey(EKeeperPhysical Physical)
{
	switch (Physical)
	{
	case EKeeperPhysical::Gust: return TEXT("GustRelease");
	case EKeeperPhysical::Talon: return TEXT("TalonStrike");
	case EKeeperPhysical::FrontCast: return TEXT("MechFrontStrike");
	case EKeeperPhysical::MiddleCurve: return TEXT("MechMiddleStrike");
	case EKeeperPhysical::RearTwoStage: return TEXT("MechRearStrike");
	default: return NAME_None;
	}
}

FName KeeperVfxRules::RecoveryKey(EKeeperPhysical Physical)
{
	switch (Physical)
	{
	case EKeeperPhysical::Gust: return TEXT("GustExpiry");
	case EKeeperPhysical::Talon: return TEXT("TalonRecovery");
	case EKeeperPhysical::FrontCast: return TEXT("MechFrontRecovery");
	case EKeeperPhysical::MiddleCurve: return TEXT("MechMiddleRecovery");
	case EKeeperPhysical::RearTwoStage: return TEXT("MechRearRecovery");
	default: return NAME_None;
	}
}

EKeeperPhysical KeeperVfxRules::PhysicalForAttack(FName AttackName)
{
	if (AttackName == UmbrellaSourceIds::GustBand())
	{
		return EKeeperPhysical::Gust;
	}
	if (AttackName == UmbrellaSourceIds::TalonRake())
	{
		return EKeeperPhysical::Talon;
	}
	if (AttackName == UmbrellaSourceIds::MechFrontCast())
	{
		return EKeeperPhysical::FrontCast;
	}
	if (AttackName == UmbrellaSourceIds::MechMiddleCurve())
	{
		return EKeeperPhysical::MiddleCurve;
	}
	if (AttackName == UmbrellaSourceIds::MechRearTwoStage())
	{
		return EKeeperPhysical::RearTwoStage;
	}
	return EKeeperPhysical::None;
}

EKeeperVfxAnchor KeeperVfxRules::AnchorFor(EKeeperPhysical Physical)
{
	switch (Physical)
	{
	case EKeeperPhysical::Gust: return EKeeperVfxAnchor::GustFront;
	case EKeeperPhysical::Talon: return EKeeperVfxAnchor::Claw;
	case EKeeperPhysical::FrontCast:
	case EKeeperPhysical::MiddleCurve:
	case EKeeperPhysical::RearTwoStage:
		return EKeeperVfxAnchor::Head;
	default: return EKeeperVfxAnchor::Body;
	}
}

void KeeperVfxRules::Diff(const FKeeperVfxSnapshot& Before, const FKeeperVfxSnapshot& After, TArray<FKeeperVfxCue>& Out)
{
	if (Before.bFightActive && !After.bFightActive && !After.bDeparting)
	{
		// Retry, reset or defeat: every held effect stops. Nothing new starts.
		for (const FName Key : HeldKeys())
		{
			AddKeeperVfxCue(Out, Key, false, EKeeperVfxAnchor::Body);
		}
		return;
	}
	const bool bAttackChanged = Before.Physical != After.Physical || Before.Stage != After.Stage;
	if (bAttackChanged)
	{
		const EKeeperVfxAnchor Anchor = AnchorFor(After.Physical);
		// The warning loop is started by the telegraph event; it ends the moment the stage leaves Warning.
		if (Before.Stage == EKeeperStage::Warning)
		{
			AddKeeperVfxCue(Out, WarningKey(Before.Physical), false, AnchorFor(Before.Physical));
		}
		if (IsKeeperVfxStroke(After.Stage))
		{
			AddKeeperVfxCue(Out, StrikeKey(After.Physical), true, Anchor);
			if (After.Physical == EKeeperPhysical::Gust)
			{
				AddKeeperVfxCue(Out, TEXT("GustTravel"), true, EKeeperVfxAnchor::GustFront);
			}
		}
		const bool bGustWasTravelling = Before.Physical == EKeeperPhysical::Gust && IsKeeperVfxStroke(Before.Stage);
		const bool bGustTravels = After.Physical == EKeeperPhysical::Gust && IsKeeperVfxStroke(After.Stage);
		if (bGustWasTravelling && !bGustTravels)
		{
			AddKeeperVfxCue(Out, TEXT("GustTravel"), false, EKeeperVfxAnchor::GustFront);
			AddKeeperVfxCue(Out, TEXT("GustExpiry"), true, EKeeperVfxAnchor::GustFront);
		}
		// Recovery is a harmless cue. The gust already showed its expiry above.
		if (After.Stage == EKeeperStage::Recovery && After.Physical != EKeeperPhysical::Gust)
		{
			AddKeeperVfxCue(Out, RecoveryKey(After.Physical), true, Anchor);
		}
	}
	if (Before.bClockOpen != After.bClockOpen)
	{
		AddKeeperVfxCue(Out, After.bClockOpen ? FName(TEXT("ClockOpening")) : FName(TEXT("ClockCover")), true, EKeeperVfxAnchor::Clock);
	}
	AddKeeperVfxToggle(Out, Before.bEyeExposed, After.bEyeExposed, TEXT("KeeperEyeExposed"), EKeeperVfxAnchor::Clock);
	AddKeeperVfxToggle(Out, Before.bSlowed, After.bSlowed, TEXT("KeeperSlow"), EKeeperVfxAnchor::Screen);
	AddKeeperVfxToggle(Out, Before.bStunned, After.bStunned, TEXT("KeeperStun"), EKeeperVfxAnchor::Body);
	AddKeeperVfxToggle(Out, Before.bBlackedOut, After.bBlackedOut, TEXT("KeeperBlackout"), EKeeperVfxAnchor::Screen);
	if (Before.bBlackedOut && !After.bBlackedOut)
	{
		AddKeeperVfxCue(Out, TEXT("KeeperRestoration"), true, EKeeperVfxAnchor::Screen);
	}
	AddKeeperVfxToggle(Out, Before.bDeparting, After.bDeparting, TEXT("KeeperDeparture"), EKeeperVfxAnchor::Body);
}

TArray<FName> KeeperVfxRules::HeldKeys()
{
	return { TEXT("GustWarning"), TEXT("TalonWarning"), TEXT("MechFrontWarning"), TEXT("MechMiddleWarning"), TEXT("MechRearWarning"),
		TEXT("GustTravel"), TEXT("KeeperEyeExposed"), TEXT("KeeperSlow"), TEXT("KeeperStun"), TEXT("KeeperBlackout"), TEXT("KeeperDeparture") };
}

bool KeeperVfxRules::IsNewBeat(float SecondsSinceLastBeatShot, float ShotSpacingSeconds, float RepeatWaitSeconds)
{
	return SecondsSinceLastBeatShot >= (ShotSpacingSeconds + RepeatWaitSeconds) * 0.5f;
}
