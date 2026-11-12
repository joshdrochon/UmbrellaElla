#include "Progression/ProgressionDraft.h"
#include "Progression/ProgressionRules.h"
#include "Progression/ProgressionTuning.h"

FProgressionDraft FProgressionDraft::Begin(const FProgressionProfile& Real)
{
	FProgressionDraft Draft;
	Draft.Ranks = Real.Ranks;
	return Draft;
}

EProgressionCommit FProgressionDraft::Stage(const FProgressionTuning& Tuning, const FProgressionProfile& Real,
	const FPurchaseContext& Context, EProgressionTrack Track, int32 Delta)
{
	TArray<int32> Next = Ranks;
	const int32 Index = static_cast<int32>(Track);
	if (!Next.IsValidIndex(Index))
	{
		return EProgressionCommit::InvalidRanks;
	}
	Next[Index] += Delta;
	FProgressionProfile Trial = Real;
	const EProgressionCommit Result = FProgressionRules::TryCommitRanks(Tuning, Trial, Next, Context);
	if (Result == EProgressionCommit::Ok)
	{
		Ranks = Next;
	}
	return Result;
}

bool FProgressionDraft::IsDirty(const FProgressionProfile& Real) const
{
	return Ranks != Real.Ranks;
}

int32 FProgressionDraft::NetCost(const FProgressionTuning& Tuning, const FProgressionProfile& Real) const
{
	return FProgressionRules::SpentOnRanks(Tuning, Ranks) - FProgressionRules::SpentOnRanks(Tuning, Real.Ranks);
}

void FProgressionDraft::Discard(const FProgressionProfile& Real)
{
	Ranks = Real.Ranks;
}
