#include "Flow/FlowTutorialText.h"

// Controls are from GDD SH1.0 section 3, Controls at a glance. Placeholder wording; Story owns final text.

namespace
{
	FText FlowTutorialLine(const TCHAR* Line)
	{
		return FText::FromString(Line);
	}
}

FText FFlowTutorialText::GetHeading(EUmbrellaPlayMode Mode)
{
	return FlowTutorialLine(Mode == EUmbrellaPlayMode::StartGame ? TEXT("Learn the Keeper's Hour") : TEXT("Learn the Journey"));
}

TArray<FText> FFlowTutorialText::GetPages(EUmbrellaPlayMode Mode)
{
	TArray<FText> Pages;
	if (Mode == EUmbrellaPlayMode::StartGame)
	{
		Pages.Add(FlowTutorialLine(TEXT("Ella drops under her umbrella. Hop with Space or A to rise. Trim with W, S or the left stick.")));
		Pages.Add(FlowTutorialLine(TEXT("While dropping, shoot with J or the left mouse button. Basic shots never run out.")));
		Pages.Add(FlowTutorialLine(TEXT("Absorb yellow shots with K or the right mouse button to heal. Dash with Q and E or the bumpers.")));
	}
	else
	{
		Pages.Add(FlowTutorialLine(TEXT("A long drop lies ahead. Hop with Space or A to rise. Trim with W, S or the left stick.")));
		Pages.Add(FlowTutorialLine(TEXT("Shoot with J or the left mouse button. Cycle spells with [ and ] or press 1 to 4.")));
		Pages.Add(FlowTutorialLine(TEXT("Absorb yellow shots with K or the right mouse button to heal. Dash with Q and E or the bumpers.")));
	}
	return Pages;
}
