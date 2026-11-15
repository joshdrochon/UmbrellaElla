#include "Flow/FlowRules.h"

EFlowScreen FFlowRules::Next(EFlowScreen From, EFlowCommand Command)
{
	switch (From)
	{
	case EFlowScreen::Title:
		if (Command == EFlowCommand::StartTutorial)
		{
			return EFlowScreen::Tutorial;
		}
		if (Command == EFlowCommand::OpenPurchase)
		{
			return EFlowScreen::Purchase;
		}
		return Command == EFlowCommand::StartMode ? EFlowScreen::Playing : From;
	case EFlowScreen::Purchase:
		// Done, Back and Pause (Escape, F1, Menu, B) all return to the title; the Start press that opened it is then repeated.
		if (Command == EFlowCommand::LeaveRefuge)
		{
			return EFlowScreen::Resuming;
		}
		return (Command == EFlowCommand::Continue || Command == EFlowCommand::Back || Command == EFlowCommand::Pause) ? EFlowScreen::Title : From;
	case EFlowScreen::Tutorial:
		// Pause then Skip works on every page; finishing the last page ends the tutorial the same way as Skip.
		switch (Command)
		{
		case EFlowCommand::Pause:
			return EFlowScreen::TutorialPaused;
		case EFlowCommand::SkipTutorial:
		case EFlowCommand::TimelineDone:
			return EFlowScreen::Resuming;
		default:
			return From;
		}
	case EFlowScreen::TutorialPaused:
		switch (Command)
		{
		case EFlowCommand::Pause:
		case EFlowCommand::Back:
		case EFlowCommand::Continue:
			return EFlowScreen::Tutorial;
		case EFlowCommand::SkipTutorial:
			return EFlowScreen::Resuming;
		default:
			return From;
		}
	case EFlowScreen::Playing:
		switch (Command)
		{
		case EFlowCommand::Pause:
			return EFlowScreen::Paused;
		case EFlowCommand::PlayerDefeated:
			return EFlowScreen::Defeat;
		case EFlowCommand::EncounterCompleted:
			return EFlowScreen::Story;
		case EFlowCommand::OpenLevelUp:
			return EFlowScreen::LevelUp;
		case EFlowCommand::EnterRefuge:
			return EFlowScreen::Purchase;
		default:
			return From;
		}
	case EFlowScreen::LevelUp:
		// Back, Confirm and Pause (Escape, F1, Menu, B) close it; control returns once the keys are released.
		switch (Command)
		{
		case EFlowCommand::Back:
		case EFlowCommand::Continue:
		case EFlowCommand::Pause:
			return EFlowScreen::Resuming;
		case EFlowCommand::PlayerDefeated:
			return EFlowScreen::Defeat;
		case EFlowCommand::EncounterCompleted:
			return EFlowScreen::Story;
		default:
			return From;
		}
	case EFlowScreen::Paused:
		switch (Command)
		{
		case EFlowCommand::Pause:
		case EFlowCommand::Back:
		case EFlowCommand::Continue:
			return EFlowScreen::Resuming;
		case EFlowCommand::OpenSettings:
			return EFlowScreen::Settings;
		default:
			return From;
		}
	case EFlowScreen::Settings:
		return (Command == EFlowCommand::Back || Command == EFlowCommand::Pause) ? EFlowScreen::Paused : From;
	case EFlowScreen::Resuming:
		if (Command == EFlowCommand::NeutralReached)
		{
			return EFlowScreen::Playing;
		}
		return Command == EFlowCommand::Pause ? EFlowScreen::Paused : From;
	case EFlowScreen::Defeat:
		return Command == EFlowCommand::Retry ? EFlowScreen::Resuming : From;
	case EFlowScreen::Story:
		if (Command == EFlowCommand::ShowStatistics)
		{
			return EFlowScreen::Statistics;
		}
		return Command == EFlowCommand::TimelineDone ? EFlowScreen::Credits : From;
	case EFlowScreen::Credits:
		if (Command == EFlowCommand::ShowStatistics)
		{
			return EFlowScreen::Statistics;
		}
		return Command == EFlowCommand::TimelineDone ? EFlowScreen::Title : From;
	case EFlowScreen::Statistics:
		// Only its Try Again and Main Menu buttons leave it; both reload the level.
		return From;
	default:
		return From;
	}
}

bool FFlowRules::IsInputBlockedOn(EFlowScreen Screen)
{
	return Screen != EFlowScreen::Playing;
}

bool FFlowRules::IsWorldPausedOn(EFlowScreen Screen)
{
	return Screen == EFlowScreen::Paused || Screen == EFlowScreen::Settings || Screen == EFlowScreen::Resuming
		|| Screen == EFlowScreen::Defeat || Screen == EFlowScreen::LevelUp;
}

bool FFlowRules::HasTutorialPageAfter(int32 Page, int32 PageCount)
{
	return Page + 1 < PageCount;
}

bool FFlowRules::ShouldOfferPurchase(bool bFeatureOn, int32 UnspentPoints, bool bCanRefund, bool bAnythingRefundable)
{
	// Refunds are open from run 2, so a player with spent points and none unspent still gets the screen.
	return bFeatureOn && (UnspentPoints > 0 || (bCanRefund && bAnythingRefundable));
}

bool FFlowRules::ShouldShowTutorial(bool bFeatureOn, bool bAlreadySeen)
{
	return bFeatureOn && !bAlreadySeen;
}

EFlowMenuIntent FFlowRules::MenuIntentForKey(const FKey& Key)
{
	if (Key == EKeys::Up || Key == EKeys::W || Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Gamepad_LeftStick_Up)
	{
		return EFlowMenuIntent::Up;
	}
	if (Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Gamepad_LeftStick_Down)
	{
		return EFlowMenuIntent::Down;
	}
	if (Key == EKeys::Left || Key == EKeys::A || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Gamepad_LeftStick_Left)
	{
		return EFlowMenuIntent::Left;
	}
	if (Key == EKeys::Right || Key == EKeys::D || Key == EKeys::Gamepad_DPad_Right || Key == EKeys::Gamepad_LeftStick_Right)
	{
		return EFlowMenuIntent::Right;
	}
	if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom)
	{
		return EFlowMenuIntent::Confirm;
	}
	if (Key == EKeys::Escape || Key == EKeys::F1 || Key == EKeys::Gamepad_FaceButton_Right || Key == EKeys::Gamepad_Special_Right)
	{
		return EFlowMenuIntent::Back;
	}
	return EFlowMenuIntent::None;
}

bool FFlowRules::IsBackgroundShownOn(EFlowScreen Screen)
{
	return Screen != EFlowScreen::Playing && Screen != EFlowScreen::Resuming;
}

int32 FFlowRules::StoryPageAt(float Elapsed, float PageSeconds, int32 PageCount)
{
	if (PageSeconds <= 0.0f || PageCount <= 0 || Elapsed < 0.0f)
	{
		return INDEX_NONE;
	}
	const int32 Page = FMath::FloorToInt(Elapsed / PageSeconds);
	return Page < PageCount ? Page : INDEX_NONE;
}

FName FFlowRules::MusicFor(EFlowScreen Screen)
{
	// Sound list: MusicTitle is the Start and End music (one track, the same slow background on both screens).
	return Screen == EFlowScreen::Title || Screen == EFlowScreen::Credits ? FName(TEXT("MusicTitle")) : NAME_None;
}

bool FFlowRules::IsTimelineDone(float Elapsed, float Duration)
{
	return Elapsed >= Duration;
}

float FFlowRules::AdvanceNeutral(float NeutralSoFar, float DeltaSeconds, bool bAnyHeld)
{
	return bAnyHeld ? 0.0f : NeutralSoFar + DeltaSeconds;
}

const TCHAR* FFlowRules::TryAgainOption()
{
	return TEXT("UmbrellaTryAgain");
}

bool FFlowRules::IsTryAgainStart(const FString& GameOptions)
{
	// Options look like "?Key=Value?Key2"; match whole keys only.
	TArray<FString> Parts;
	GameOptions.ParseIntoArray(Parts, TEXT("?"), true);
	for (const FString& Part : Parts)
	{
		FString Key = Part;
		FString Value;
		Part.Split(TEXT("="), &Key, &Value);
		if (Key.Equals(TryAgainOption(), ESearchCase::IgnoreCase))
		{
			return true;
		}
	}
	return false;
}

bool FFlowRules::IsEndingHoldAt(float StoryElapsed, float HoldSeconds)
{
	return StoryElapsed < HoldSeconds;
}

int32 FFlowRules::EndingPageAt(float StoryElapsed, float HoldSeconds, float PageSeconds, int32 PageCount)
{
	return IsEndingHoldAt(StoryElapsed, HoldSeconds) ? INDEX_NONE : StoryPageAt(StoryElapsed - HoldSeconds, PageSeconds, PageCount);
}

EFlowCommand FFlowRules::AfterCredits(EUmbrellaPlayMode Mode, bool bStatisticsOn)
{
	return Mode == EUmbrellaPlayMode::DirectorsCut && bStatisticsOn ? EFlowCommand::ShowStatistics : EFlowCommand::TimelineDone;
}

TArray<FKey> FFlowRules::StorySkipKeys()
{
	TArray<FKey> Keys;
	Keys.Add(EKeys::Enter);
	Keys.Add(EKeys::Gamepad_Special_Left);
	return Keys;
}

FName FFlowRules::TitleMusicId()
{
	return FName(TEXT("MusicTitle"));
}

FString FFlowRules::RetryOption(EUmbrellaPlayMode Mode, int32 RetryCount)
{
	return FString::Printf(TEXT("UmbrellaRetry=%s.%d"), Mode == EUmbrellaPlayMode::DirectorsCut ? TEXT("DirectorsCut") : TEXT("StartGame"), RetryCount);
}

bool FFlowRules::HasRetryStart(const FString& GameOptions, EUmbrellaPlayMode& OutMode, int32& OutRetryCount)
{
	TArray<FString> Parts;
	GameOptions.ParseIntoArray(Parts, TEXT("?"), true);
	for (const FString& Part : Parts)
	{
		FString Key;
		FString Value;
		if (!Part.Split(TEXT("="), &Key, &Value) || !Key.Equals(TEXT("UmbrellaRetry"), ESearchCase::IgnoreCase))
		{
			continue;
		}
		FString ModeName;
		FString Count;
		if (!Value.Split(TEXT("."), &ModeName, &Count))
		{
			ModeName = Value;
		}
		if (ModeName.Equals(TEXT("DirectorsCut"), ESearchCase::IgnoreCase))
		{
			OutMode = EUmbrellaPlayMode::DirectorsCut;
		}
		else if (ModeName.Equals(TEXT("StartGame"), ESearchCase::IgnoreCase))
		{
			OutMode = EUmbrellaPlayMode::StartGame;
		}
		else
		{
			return false;
		}
		OutRetryCount = FMath::Max(0, FCString::Atoi(*Count));
		return true;
	}
	return false;
}
