#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "Core/UmbrellaPlayMode.h"
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
	TutorialPaused,
	Purchase,
	LevelUp,
	/** Director's Cut Journey Complete after the credits; Story's widget, Try Again / Main Menu leave it. */
	Statistics
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
	OpenPurchase,
	EnterRefuge,
	LeaveRefuge,
	OpenLevelUp,
	PlayerDefeated,
	EncounterCompleted,
	Retry,
	NeutralReached,
	TimelineDone,
	/** Director's Cut: credits finished, or a later-win Skip from the ending story or credits. */
	ShowStatistics
};

/** What a key means inside a menu. */
UENUM()
enum class EFlowMenuIntent : uint8
{
	None,
	Up,
	Down,
	Left,
	Right,
	Confirm,
	Back
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

	/** Menu meaning of a key: D-pad, arrows, WASD navigate; Cross, A, Enter, Space select; Circle, B, Escape, F1, Menu back out. */
	static EFlowMenuIntent MenuIntentForKey(const FKey& Key);

	/** True when another tutorial page follows Page (zero based). */
	static bool HasTutorialPageAfter(int32 Page, int32 PageCount);

	/** The Director's Cut start offers the purchase screen when there is something to buy or (from run 2) to refund. */
	static bool ShouldOfferPurchase(bool bFeatureOn, int32 UnspentPoints, bool bCanRefund, bool bAnythingRefundable);

	/** The tutorial runs on first start only (tracking and replay rules stay OPEN). */
	static bool ShouldShowTutorial(bool bFeatureOn, bool bAlreadySeen);

	/** True on the screens that draw the slowly moving character-free background. */
	static bool IsBackgroundShownOn(EFlowScreen Screen);

	/** The index of the story page showing at Elapsed seconds, or INDEX_NONE once the story is over. */
	static int32 StoryPageAt(float Elapsed, float PageSeconds, int32 PageCount);

	/** True once Elapsed has reached Duration. */
	static bool IsTimelineDone(float Elapsed, float Duration);

	/** The looping sound-list row a screen starts (Start and credits share the title track), or NAME_None to leave music as is. */
	static FName MusicFor(EFlowScreen Screen);

	/** Story Skip keys (opening caption, ending): Enter and the gamepad View button; no gameplay action uses them, so a skip press never reaches play. */
	static TArray<FKey> StorySkipKeys();

	/** The level option a Try Again reload carries: the new world starts a Director's Cut run at once. */
	static const TCHAR* TryAgainOption();

	/** True when the game options of a freshly loaded world ask for the Try Again start. */
	static bool IsTryAgainStart(const FString& GameOptions);

	/** True during the ending hold on Ella: the Story screen shows the world, not the ending background. */
	static bool IsEndingHoldAt(float StoryElapsed, float HoldSeconds);

	/** The ending page at StoryElapsed seconds on the Story screen (after the hold), or INDEX_NONE in the hold or after. */
	static int32 EndingPageAt(float StoryElapsed, float HoldSeconds, float PageSeconds, int32 PageCount);

	/** What the end of the credits does: Director's Cut shows Journey Complete, Start Game returns to the title. */
	static EFlowCommand AfterCredits(EUmbrellaPlayMode Mode, bool bStatisticsOn);

	/** Seconds of neutral input so far: resets to 0 when a key is held. */
	/** Start screen: the sound-list row the Start screen plays (looped music). */
	static FName TitleMusicId();

	static float AdvanceNeutral(float NeutralSoFar, float DeltaSeconds, bool bAnyHeld);
};
