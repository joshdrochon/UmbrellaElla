#include "Core/UmbrellaGameMode.h"

#include "Core/EllaCharacter.h"
#include "Kismet/KismetSystemLibrary.h"

AUmbrellaGameMode::AUmbrellaGameMode()
{
	DefaultPawnClass = AEllaCharacter::StaticClass();
}

// G1 quit-play: from play an in-game quit closes the game (exit 0), never Alt+F4. The title Quit button (card 0.21)
// calls the same function.
void AUmbrellaGameMode::QuitFromPlay()
{
	UKismetSystemLibrary::QuitGame(this, nullptr, EQuitPreference::Quit, false);
}
