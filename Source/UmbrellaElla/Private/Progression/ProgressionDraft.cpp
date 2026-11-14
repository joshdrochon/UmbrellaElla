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

TArray<FProgressionReviewLine> FProgressionDraft::Review(const FProgressionTuning& Tuning, const FProgressionProfile& Real) const
{
	TArray<FProgressionReviewLine> Lines;
	for (int32 Index = 0; Index < static_cast<int32>(EProgressionTrack::Count); ++Index)
	{
		const EProgressionTrack Track = static_cast<EProgressionTrack>(Index);
		const int32 From = FProgressionRules::RankOf(Real.Ranks, Track);
		const int32 To = FProgressionRules::RankOf(Ranks, Track);
		if (From == To)
		{
			continue;
		}
		// The cost of one track's move is the spend difference with only that track changed.
		TArray<int32> OnlyThis = Real.Ranks;
		OnlyThis[Index] = To;
		FProgressionReviewLine Line;
		Line.Track = Track;
		Line.FromRank = From;
		Line.ToRank = To;
		Line.Cost = FProgressionRules::SpentOnRanks(Tuning, OnlyThis) - FProgressionRules::SpentOnRanks(Tuning, Real.Ranks);
		Line.ValueBefore = FProgressionRules::TrackValue(Tuning, Real.Ranks, Track);
		Line.ValueAfter = FProgressionRules::TrackValue(Tuning, OnlyThis, Track);
		Lines.Add(Line);
	}
	return Lines;
}
