#include "Attack/SpellPresentation.h"
#include "Attack/AttackTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"

EUmbrellaBodyPose SpellPresentationRules::BodyPoseFor(EUmbrellaSpell Spell)
{
	// COM-07 / COM-11: the Streamed Blast is shoulder-braced; every other spell uses the regular fall.
	if (IsFeatureEnabled(EFeatureId::COM_11) && Spell == EUmbrellaSpell::StreamedBlast)
	{
		return EUmbrellaBodyPose::ShoulderFall;
	}
	return EUmbrellaBodyPose::RegularFall;
}

bool SpellPresentationRules::HasCanopyCycle(EUmbrellaSpell Spell)
{
	return IsFeatureEnabled(EFeatureId::COM_06) && Spell == EUmbrellaSpell::SmallBlasts;
}

FCanopyCycleState SpellPresentationRules::RestingCycle(EUmbrellaSpell Spell)
{
	FCanopyCycleState Cycle;
	Cycle.Phase = HasCanopyCycle(Spell) ? EUmbrellaCanopyPhase::FoldedReady : EUmbrellaCanopyPhase::Steady;
	return Cycle;
}

void SpellPresentationRules::OnEmission(FCanopyCycleState& Cycle, EUmbrellaSpell Spell, const FAttackTuning& Tuning)
{
	if (!HasCanopyCycle(Spell))
	{
		Cycle.Phase = EUmbrellaCanopyPhase::Steady;
		Cycle.PhaseLeft = 0.0f;
		return;
	}
	Cycle.Phase = EUmbrellaCanopyPhase::SnapOpen;
	Cycle.PhaseLeft = Tuning.SmallCanopyOpenSeconds;
	++Cycle.Pulses;
}

void SpellPresentationRules::Step(FCanopyCycleState& Cycle, float DeltaSeconds, const FAttackTuning& Tuning)
{
	float Left = DeltaSeconds;
	while (Left > 0.0f && (Cycle.Phase == EUmbrellaCanopyPhase::SnapOpen || Cycle.Phase == EUmbrellaCanopyPhase::Cock))
	{
		if (Cycle.PhaseLeft > Left)
		{
			Cycle.PhaseLeft -= Left;
			return;
		}
		Left -= Cycle.PhaseLeft;
		if (Cycle.Phase == EUmbrellaCanopyPhase::SnapOpen)
		{
			Cycle.Phase = EUmbrellaCanopyPhase::Cock;
			Cycle.PhaseLeft = Tuning.SmallCanopyCockSeconds;
		}
		else
		{
			Cycle.Phase = EUmbrellaCanopyPhase::FoldedReady;
			Cycle.PhaseLeft = 0.0f;
		}
	}
}

FString SpellPresentationRules::DisplayName(EUmbrellaSpell Spell)
{
	switch (Spell)
	{
	case EUmbrellaSpell::StreamedBlast:
		return TEXT("Streamed Blast");
	case EUmbrellaSpell::TwinStars:
		return TEXT("Twin Stars");
	case EUmbrellaSpell::Needle:
		return TEXT("Needle");
	default:
		return TEXT("Small Blasts");
	}
}

TArray<FSpellWheelEntry> SpellPresentationRules::WheelEntries(EUmbrellaPlayMode Mode, int32 DirectorLevel, const FAttackTuning& Tuning)
{
	TArray<FSpellWheelEntry> Entries;
	for (int32 Index = 0; Index < SpellRules::SpellCount; ++Index)
	{
		FSpellWheelEntry& Entry = Entries.AddDefaulted_GetRef();
		Entry.Spell = static_cast<EUmbrellaSpell>(Index);
		Entry.UnlockLevel = SpellRules::UnlockLevel(Entry.Spell, Tuning);
		Entry.bLocked = !SpellRules::IsAvailable(Entry.Spell, Mode, DirectorLevel, Tuning);
		if (Entry.bLocked && IsFeatureEnabled(EFeatureId::COM_11))
		{
			// COM-11: a locked weapon shows its Director's Cut unlock level.
			Entry.LockLabel = FString::Printf(TEXT("Lv %d"), Entry.UnlockLevel);
		}
	}
	return Entries;
}

TArray<FBeamStrand> SpellPresentationRules::BeamStrands(float Length, float Width, const FAttackTuning& Tuning)
{
	TArray<FBeamStrand> Strands;
	if (!IsFeatureEnabled(EFeatureId::COM_07) || Length <= 0.0f)
	{
		return Strands;
	}
	const int32 Count = FMath::Max(Tuning.StreamStrandCount, 2);
	const float BodyHalf = Width * 0.5f;
	const float Spread = FMath::Max(Tuning.StreamStrandCanopySpread, BodyHalf);
	const float ConvergeX = Length * FMath::Clamp(Tuning.StreamStrandConvergeShare, 0.0f, 1.0f);
	const int32 PerSide = (Count + 1) / 2;
	for (int32 Index = 0; Index < Count; ++Index)
	{
		// Even strands above the body, odd below; each side fans from the body edge to the canopy spread.
		const float Side = (Index % 2 == 0) ? 1.0f : -1.0f;
		const int32 Rank = Index / 2;
		const float Fan = PerSide > 1 ? static_cast<float>(Rank) / static_cast<float>(PerSide - 1) : 1.0f;
		const float StartZ = Side * FMath::Lerp(BodyHalf + (Spread - BodyHalf) * 0.5f, Spread, Fan);
		FBeamStrand& Strand = Strands.AddDefaulted_GetRef();
		Strand.Start = FVector2D(0.0f, StartZ);
		Strand.Converge = FVector2D(ConvergeX, Side * BodyHalf);
		Strand.End = FVector2D(Length, Side * BodyHalf);
	}
	return Strands;
}
