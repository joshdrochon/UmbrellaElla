#pragma once

#include "CoreMinimal.h"
#include "EditorValidatorBase.h"
#include "UmbrellaValidator.generated.h"

class UUmbrellaComponent;

UCLASS()
class UUmbrellaValidator : public UEditorValidatorBase
{
	GENERATED_BODY()

private:
	UPROPERTY()
	TObjectPtr<UUmbrellaComponent> Probe;
};
