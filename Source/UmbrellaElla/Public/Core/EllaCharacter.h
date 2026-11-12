#pragma once

#include "CoreMinimal.h"
#include "PaperCharacter.h"
#include "EllaCharacter.generated.h"

class UEllaInputAdapterComponent;
class UEllaMotorComponent;
class UUmbrellaStateComponent;
class UAttackEmitterComponent;
class UAbsorbReceiverComponent;
class UUmbrellaHealthComponent;
class UEllaAnimPresenterComponent;

/**
 * Ella shell (Core, TD-owned; module_check rule L). Constructor creates the components and the plane constraint;
 * SetupPlayerInputComponent calls each component's BindInput (the Input Adapter adds IMC_Default). No rule lives here.
 */
UCLASS()
class UMBRELLAELLA_API AEllaCharacter : public APaperCharacter
{
	GENERATED_BODY()

public:
	AEllaCharacter();

	UEllaInputAdapterComponent* GetInputAdapter() const { return InputAdapter; }
	UEllaMotorComponent* GetMotor() const { return Motor; }
	UUmbrellaStateComponent* GetUmbrellaState() const { return UmbrellaState; }
	UAttackEmitterComponent* GetAttack() const { return Attack; }
	UAbsorbReceiverComponent* GetAbsorb() const { return Absorb; }
	UUmbrellaHealthComponent* GetHealth() const { return Health; }
	UEllaAnimPresenterComponent* GetAnimPresenter() const { return AnimPresenter; }

protected:
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

private:
	UPROPERTY(VisibleAnywhere, Category = "Ella")
	TObjectPtr<UEllaInputAdapterComponent> InputAdapter;

	UPROPERTY(VisibleAnywhere, Category = "Ella")
	TObjectPtr<UEllaMotorComponent> Motor;

	UPROPERTY(VisibleAnywhere, Category = "Ella")
	TObjectPtr<UUmbrellaStateComponent> UmbrellaState;

	UPROPERTY(VisibleAnywhere, Category = "Ella")
	TObjectPtr<UAttackEmitterComponent> Attack;

	UPROPERTY(VisibleAnywhere, Category = "Ella")
	TObjectPtr<UAbsorbReceiverComponent> Absorb;

	UPROPERTY(VisibleAnywhere, Category = "Ella")
	TObjectPtr<UUmbrellaHealthComponent> Health;

	UPROPERTY(VisibleAnywhere, Category = "Ella")
	TObjectPtr<UEllaAnimPresenterComponent> AnimPresenter;
};
