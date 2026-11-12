#include "Core/EllaCharacter.h"
#include "Attack/AttackEmitterComponent.h"
#include "Defense/AbsorbReceiverComponent.h"
#include "EnhancedInputComponent.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Motor/EllaMotorComponent.h"
#include "Umbrella/UmbrellaStateComponent.h"

AEllaCharacter::AEllaCharacter()
{
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->SetPlaneConstraintEnabled(true);
	Move->SetPlaneConstraintNormal(FVector(0.0, 1.0, 0.0));

	InputAdapter = CreateDefaultSubobject<UEllaInputAdapterComponent>(TEXT("InputAdapter"));
	Motor = CreateDefaultSubobject<UEllaMotorComponent>(TEXT("Motor"));
	UmbrellaState = CreateDefaultSubobject<UUmbrellaStateComponent>(TEXT("UmbrellaState"));
	Attack = CreateDefaultSubobject<UAttackEmitterComponent>(TEXT("Attack"));
	Absorb = CreateDefaultSubobject<UAbsorbReceiverComponent>(TEXT("Absorb"));
	Health = CreateDefaultSubobject<UUmbrellaHealthComponent>(TEXT("Health"));
	AnimPresenter = CreateDefaultSubobject<UEllaAnimPresenterComponent>(TEXT("AnimPresenter"));
}

void AEllaCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	InputAdapter->BindInput(Input);
	Motor->BindInput(Input);
	UmbrellaState->BindInput(Input);
	Attack->BindInput(Input);
	Absorb->BindInput(Input);
	Health->BindInput(Input);
	AnimPresenter->BindInput(Input);
}
