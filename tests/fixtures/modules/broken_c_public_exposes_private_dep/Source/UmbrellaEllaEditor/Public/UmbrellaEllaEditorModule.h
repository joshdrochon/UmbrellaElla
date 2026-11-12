#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleInterface.h"

class UUmbrellaComponent;

class FUmbrellaEllaEditorModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	static bool IsValidUmbrella(const UUmbrellaComponent* Umbrella);
};
