#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaPlayMode.h"
#include "Story/StoryTuning.h"

struct FUmbrellaEvent;

namespace StoryCueColumn
{
	constexpr int32 Id = 0;
	constexpr int32 Trigger = 1;
	constexpr int32 Delay = 2;
	constexpr int32 Duration = 3;
	constexpr int32 Text = 4;
	constexpr int32 Count = 5;
}

/** One line the story can show. Loaded from the cue table (StoryCues.tsv), never written in logic. */
struct UMBRELLAELLA_API FStoryCue
{
	FName Id;
	/** "<EventName>.<Detail>" the cue answers, e.g. ModeSelected.DirectorsCut. */
	FName Trigger;
	/** Seconds after the trigger before it shows. */
	float DelaySeconds = 0.0f;
	/** Seconds on screen; 0 = use the tuning value named by Id. */
	float DurationSeconds = 0.0f;
	FString Text;
};

/** The eight Journey Complete numbers of the current run on the Journey Complete screen. Never lifetime totals. */
struct UMBRELLAELLA_API FStoryRunStats
{
	int32 EnemiesDefeated = 0;
	int32 XpEarned = 0;
	int32 Deaths = 0;
	float DistanceFlownUnits = 0.0f;
	int32 ShotsFired = 0;
	int32 ShotsFiredAtYou = 0;
	float DamageTaken = 0.0f;
	float HealthRestored = 0.0f;
};

/** The eight Journey Complete rows (label, value) in the GDD order. */
UMBRELLAELLA_API TArray<TPair<FString, FString>> StoryStatsRows(const FStoryRunStats& Stats);

/** Saved flags: opening seen and first win seen (ending/credits Skip). Two separate flags. */
struct UMBRELLAELLA_API FStoryProgress
{
	bool bOpeningSeen = false;
	bool bFirstWinSeen = false;

	FString ToText() const;
	static FStoryProgress FromText(const FString& Text);
};

/** Ending stages in timeline order (flow drives them; story only follows, forward only). */
enum class EStoryEndingStage : uint8
{
	None,
	Hold,
	StoryText,
	Credits,
	Statistics
};

/** Plain rule functions for the cue table. */
namespace StoryCueTable
{
	/** Parse tab separated rows: id, trigger, delay, duration, text. Bad rows are skipped. */
	UMBRELLAELLA_API TArray<FStoryCue> Parse(const FString& Text);
	/** The compiled copy of Content/UmbrellaElla/UI/Story/StoryCues.tsv (used when the file is not staged). */
	UMBRELLAELLA_API const FString& DefaultText();
	/** The trigger name for an event: "<Event>.<Detail>". */
	UMBRELLAELLA_API FName TriggerFor(const FUmbrellaEvent& Event);
}

/**
 * The story state machine. No UObject, no clock of its own: feed it events and Advance() (in-play captions). The ending
 * timeline is flow's: flow calls EnterEndingStage() as its screens change. It never decides combat success.
 */
class UMBRELLAELLA_API FStoryModel
{
public:
	void SetCues(const TArray<FStoryCue>& InCues) { Cues = InCues; }
	void SetProgress(const FStoryProgress& InProgress) { Progress = InProgress; }
	const FStoryProgress& GetProgress() const { return Progress; }

	/** Feed one bus event. */
	void OnEvent(const FUmbrellaEvent& Event);
	/** Health at run start when the caller knows it; otherwise the first health event is the baseline. */
	void SetHealthBaseline(float Health, int32 Lives);
	/** Sample the player position (distance flown). */
	void SampleLocation(const FVector& Location);
	void Advance(float DeltaSeconds);

	/** The opening caption is on screen (a skip press then belongs to the story and must not reach play). */
	bool IsOpeningShowing() const;
	/** Skip the opening caption; only works after the opening was seen once. */
	void SkipOpening();
	/** Ending story or credits are showing and a prior first win allows skipping. */
	bool CanSkipEnding() const;
	void SkipEnding();

	/**
	 * Flow's ending clock moved on (StoryText, Credits, Statistics). Forward only, Director's Cut only, and only after
	 * EncounterCompleted started the ending (Hold). Statistics saves the first-win flag.
	 */
	void EnterEndingStage(EStoryEndingStage Next);
	/** The ending story lines (cue trigger Ending.Story) in table order; flow shows them as its story pages. */
	TArray<FString> GetEndingLines() const;
	/** Light and shadow trigger: the light shaft and umbra are on (Director's Cut play and the ending hold). */
	bool IsLightShaftOn() const;

	/** Try Again / a fresh run started by the caller without a ModeSelected event. */
	void BeginNewRun(EUmbrellaPlayMode Mode);

	bool IsDirectorsCut() const { return Mode == EUmbrellaPlayMode::DirectorsCut; }
	const FStoryCue* GetActiveCue() const { return bHasActive ? &Active : nullptr; }
	float GetActiveRemaining() const { return ActiveRemaining; }
	const TArray<FName>& GetShownIds() const { return Shown; }
	int32 CountShown(FName Id) const;
	EStoryEndingStage GetEndingStage() const { return Stage; }
	const FStoryRunStats& GetStats() const { return Stats; }
	bool ShouldShowStatistics() const { return Stage == EStoryEndingStage::Statistics; }
	/** The saved flags changed since MarkProgressSaved(). */
	bool HasProgressToSave() const { return bProgressDirty; }
	void MarkProgressSaved() { bProgressDirty = false; }

private:
	void Queue(const FStoryCue& Cue);
	void StartCue(const FStoryCue& Cue);
	void FinishActive();
	void EnterStage(EStoryEndingStage Next);
	void BeginRunState();
	void HandleHealth(const FUmbrellaEvent& Event);

	TArray<FStoryCue> Cues;
	FStoryProgress Progress;
	FStoryRunStats Stats;
	EUmbrellaPlayMode Mode = EUmbrellaPlayMode::StartGame;
	bool bRunLive = false;

	struct FPending
	{
		FStoryCue Cue;
		float Remaining = 0.0f;
	};
	TArray<FPending> Pending;
	TArray<FName> Shown;
	FStoryCue Active;
	bool bHasActive = false;
	float ActiveRemaining = 0.0f;

	EStoryEndingStage Stage = EStoryEndingStage::None;
	bool bProgressDirty = false;

	bool bHaveLocation = false;
	FVector LastLocation = FVector::ZeroVector;
	bool bHaveHealth = false;
	float LastHealth = 0.0f;
	int32 LastLives = 0;
};
