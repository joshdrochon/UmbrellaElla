#include "Core/UmbrellaGameMode.h"
#include "Core/EllaCharacter.h"

AUmbrellaGameMode::AUmbrellaGameMode()
{
	DefaultPawnClass = AEllaCharacter::StaticClass();
}
