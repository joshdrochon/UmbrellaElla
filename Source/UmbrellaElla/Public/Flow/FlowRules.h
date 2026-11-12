#pragma once

#include "CoreMinimal.h"
#include "FlowRules.generated.h"

/** Which screen the player is on. */
UENUM()
enum class EFlowScreen : uint8
{
	Title,
	Playing,
	Paused,
	Settings,
	Resuming,
	Defeat,
	Story,
	Credits,
	Tutorial,
	TutorialPaused
};

/** What happens to the flow. */
UENUM()
enum class EFlowCommand : uint8
{
	StartMode,
	StartTutorial,
	SkipTutorial,
	NextPage,
	Pause,
	Back,
	Continue,
	OpenSettings,
	PlayerDefeated,
	EncounterCompleted,
	Retry,
	NeutralReached,
	TimelineDone
};

/** Plain rule functions of the mode flow: no world, no widgets, so tests call them directly. */
struct UMBRELLAELLA_API FFlowRules
{
	/** The screen after a command; the same screen when the command does not apply. */
	static EFlowScreen Next(EFlowScreen From, EFlowCommand Command);

	/** True on every screen but Playing: the gameplay input contexts are off. */
	static bool IsInputBlockedOn(EFlowScreen Screen);

	/** True where the simulation stands still (pause, settings, resume wait, defeat). */
	static bool IsWorldPausedOn(EFlowScreen Screen);

	/** True when another tutorial page follows Page (zero based). */
	static bool HasTutorialPageAfter(int32 Page, int32 PageCount);

	/** The tutorial runs on first start only (tracking and replay rules stay OPEN). */
	static bool ShouldShowTutorial(bool bFeatureOn, bool bAlreadySeen);

	/** True on the screens that draw the slowly moving character-free background. */
	static bool IsBackgroundShownOn(EFlowScreen Screen);

	/** The index of the story page showing at Elapsed seconds, or INDEX_NONE once the story is over. */
	static int32 StoryPageAt(float Elapsed, float PageSeconds, int32 PageCount);

	/** True once Elapsed has reached Duration. */
	static bool IsTimelineDone(float Elapsed, float Duration);

	/** Seconds of neutral input so far: resets to 0 when a key is held. */
	static float AdvanceNeutral(float NeutralSoFar, float DeltaSeconds, bool bAnyHeld);
};
