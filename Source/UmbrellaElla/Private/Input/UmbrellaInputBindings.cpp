#include "Input/UmbrellaInputBindings.h"
#include "Harness/UmbrellaFeatureFlags.h"

namespace
{
	void Add(TArray<FUmbrellaDefaultBinding>& Out, EUmbrellaInputAction Action, const FKey& Key, float Scale = 1.0f)
	{
		FUmbrellaDefaultBinding Binding;
		Binding.Action = Action;
		Binding.Key = Key;
		Binding.Scale = Scale;
		Out.Add(Binding);
	}
}

TArray<FUmbrellaDefaultBinding> UmbrellaInputBindings::BuildDefaults()
{
	TArray<FUmbrellaDefaultBinding> Out;
	if (!IsFeatureEnabled(EFeatureId::MOVE_05))
	{
		return Out;
	}
	// MOVE-05: Shoot = R2/RT, left mouse, J. Absorb = L2/LT, right mouse, K. Both held = fast free fall.
	Add(Out, EUmbrellaInputAction::Shoot, EKeys::J);
	Add(Out, EUmbrellaInputAction::Shoot, EKeys::LeftMouseButton);
	Add(Out, EUmbrellaInputAction::Shoot, EKeys::Gamepad_RightTrigger);
	Add(Out, EUmbrellaInputAction::Absorb, EKeys::K);
	Add(Out, EUmbrellaInputAction::Absorb, EKeys::RightMouseButton);
	Add(Out, EUmbrellaInputAction::Absorb, EKeys::Gamepad_LeftTrigger);

	if (IsFeatureEnabled(EFeatureId::MOVE_06))
	{
		// MOVE-06: Hop = Cross/A or Space (contextual dash while falling); Dash back = L1/LB or Q; forward = R1/RB or E;
		// Ride = Triangle/Y or Left Shift.
		Add(Out, EUmbrellaInputAction::Hop, EKeys::SpaceBar);
		Add(Out, EUmbrellaInputAction::Hop, EKeys::Gamepad_FaceButton_Bottom);
		Add(Out, EUmbrellaInputAction::DashBack, EKeys::Q);
		Add(Out, EUmbrellaInputAction::DashBack, EKeys::Gamepad_LeftShoulder);
		Add(Out, EUmbrellaInputAction::DashForward, EKeys::E);
		Add(Out, EUmbrellaInputAction::DashForward, EKeys::Gamepad_RightShoulder);
		Add(Out, EUmbrellaInputAction::Ride, EKeys::LeftShift);
		Add(Out, EUmbrellaInputAction::Ride, EKeys::Gamepad_FaceButton_Top);
	}

	if (IsFeatureEnabled(EFeatureId::MOVE_07))
	{
		// MOVE-07: Trim = left stick up/down, W/S, arrow aliases. Horizontal input only picks a hop/dash side.
		Add(Out, EUmbrellaInputAction::Trim, EKeys::W);
		Add(Out, EUmbrellaInputAction::Trim, EKeys::S, -1.0f);
		Add(Out, EUmbrellaInputAction::Trim, EKeys::Up);
		Add(Out, EUmbrellaInputAction::Trim, EKeys::Down, -1.0f);
		Add(Out, EUmbrellaInputAction::Trim, EKeys::Gamepad_LeftY);
		Add(Out, EUmbrellaInputAction::MoveX, EKeys::D);
		Add(Out, EUmbrellaInputAction::MoveX, EKeys::A, -1.0f);
		Add(Out, EUmbrellaInputAction::MoveX, EKeys::Right);
		Add(Out, EUmbrellaInputAction::MoveX, EKeys::Left, -1.0f);
		Add(Out, EUmbrellaInputAction::MoveX, EKeys::Gamepad_LeftX);
	}

	if (IsFeatureEnabled(EFeatureId::MOVE_08))
	{
		// MOVE-08: keys 1-4 and right-stick directions select Small / Stream / Twin / Needle; [ / ] and D-pad cycle.
		Add(Out, EUmbrellaInputAction::Spell1, EKeys::One);
		Add(Out, EUmbrellaInputAction::Spell1, EKeys::Gamepad_RightStick_Up);
		Add(Out, EUmbrellaInputAction::Spell2, EKeys::Two);
		Add(Out, EUmbrellaInputAction::Spell2, EKeys::Gamepad_RightStick_Right);
		Add(Out, EUmbrellaInputAction::Spell3, EKeys::Three);
		Add(Out, EUmbrellaInputAction::Spell3, EKeys::Gamepad_RightStick_Down);
		Add(Out, EUmbrellaInputAction::Spell4, EKeys::Four);
		Add(Out, EUmbrellaInputAction::Spell4, EKeys::Gamepad_RightStick_Left);
		Add(Out, EUmbrellaInputAction::SpellNext, EKeys::RightBracket);
		Add(Out, EUmbrellaInputAction::SpellNext, EKeys::Gamepad_DPad_Right);
		Add(Out, EUmbrellaInputAction::SpellPrevious, EKeys::LeftBracket);
		Add(Out, EUmbrellaInputAction::SpellPrevious, EKeys::Gamepad_DPad_Left);
	}
	return Out;
}

FName UmbrellaInputBindings::ActionName(EUmbrellaInputAction Action)
{
	switch (Action)
	{
	case EUmbrellaInputAction::Shoot:
		return FName(TEXT("IA_Shoot"));
	case EUmbrellaInputAction::Absorb:
		return FName(TEXT("IA_Absorb"));
	case EUmbrellaInputAction::Hop:
		return FName(TEXT("IA_Hop"));
	case EUmbrellaInputAction::DashBack:
		return FName(TEXT("IA_DashBack"));
	case EUmbrellaInputAction::DashForward:
		return FName(TEXT("IA_DashForward"));
	case EUmbrellaInputAction::Ride:
		return FName(TEXT("IA_Ride"));
	case EUmbrellaInputAction::Trim:
		return FName(TEXT("IA_Trim"));
	case EUmbrellaInputAction::MoveX:
		return FName(TEXT("IA_MoveX"));
	case EUmbrellaInputAction::Spell1:
		return FName(TEXT("IA_Spell1"));
	case EUmbrellaInputAction::Spell2:
		return FName(TEXT("IA_Spell2"));
	case EUmbrellaInputAction::Spell3:
		return FName(TEXT("IA_Spell3"));
	case EUmbrellaInputAction::Spell4:
		return FName(TEXT("IA_Spell4"));
	case EUmbrellaInputAction::SpellNext:
		return FName(TEXT("IA_SpellNext"));
	case EUmbrellaInputAction::SpellPrevious:
		return FName(TEXT("IA_SpellPrevious"));
	case EUmbrellaInputAction::Count:
	default:
		return NAME_None;
	}
}

bool UmbrellaInputBindings::IsAxisAction(EUmbrellaInputAction Action)
{
	return Action == EUmbrellaInputAction::Trim || Action == EUmbrellaInputAction::MoveX;
}
