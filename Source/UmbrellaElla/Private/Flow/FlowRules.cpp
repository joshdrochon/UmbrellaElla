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
		return Command == EFlowCommand::StartMode ? EFlowScreen::Playing : From;
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
		return Command == EFlowCommand::TimelineDone ? EFlowScreen::Credits : From;
	case EFlowScreen::Credits:
		return Command == EFlowCommand::TimelineDone ? EFlowScreen::Title : From;
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
		|| Screen == EFlowScreen::Defeat;
}

bool FFlowRules::HasTutorialPageAfter(int32 Page, int32 PageCount)
{
	return Page + 1 < PageCount;
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

bool FFlowRules::IsTimelineDone(float Elapsed, float Duration)
{
	return Elapsed >= Duration;
}

float FFlowRules::AdvanceNeutral(float NeutralSoFar, float DeltaSeconds, bool bAnyHeld)
{
	return bAnyHeld ? 0.0f : NeutralSoFar + DeltaSeconds;
}
