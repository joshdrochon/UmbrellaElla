#include "Core/UmbrellaGameMode.h"
#include "Core/EllaCharacter.h"
#include "Flow/UmbrellaPlayerController.h"
#include "UI/UmbrellaHUD.h"

AUmbrellaGameMode::AUmbrellaGameMode()
{
	DefaultPawnClass = AEllaCharacter::StaticClass();
	PlayerControllerClass = AUmbrellaPlayerController::StaticClass();
	HUDClass = AUmbrellaHUD::StaticClass();
}
