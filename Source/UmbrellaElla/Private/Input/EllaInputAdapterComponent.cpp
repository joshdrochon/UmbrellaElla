#include "Input/EllaInputAdapterComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Motor/EllaMotorComponent.h"
#include "Umbrella/UmbrellaStateComponent.h"

namespace
{
	/** IMC_Default priority (lowest; menus and the like sit above it). */
	constexpr int32 DefaultContextPriority = 0;
}

UEllaInputAdapterComponent::UEllaInputAdapterComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UEllaInputAdapterComponent::BuildInputAssets()
{
	if (MappingContext)
	{
		return;
	}
	const int32 ActionCount = static_cast<int32>(EUmbrellaInputAction::Count);
	InputActions.Reset();
	InputActions.SetNum(ActionCount);
	for (int32 Index = 0; Index < ActionCount; ++Index)
	{
		const EUmbrellaInputAction Id = static_cast<EUmbrellaInputAction>(Index);
		UInputAction* Action = NewObject<UInputAction>(this, UmbrellaInputBindings::ActionName(Id));
		Action->ValueType = UmbrellaInputBindings::IsAxisAction(Id) ? EInputActionValueType::Axis1D : EInputActionValueType::Boolean;
		InputActions[Index] = Action;
	}
	MappingContext = NewObject<UInputMappingContext>(this, FName(TEXT("IMC_Default")));
	for (const FUmbrellaDefaultBinding& Binding : UmbrellaInputBindings::BuildDefaults())
	{
		FEnhancedActionKeyMapping& Mapping = MappingContext->MapKey(InputActions[static_cast<int32>(Binding.Action)], Binding.Key);
		if (Binding.Scale < 0.0f)
		{
			Mapping.Modifiers.Add(NewObject<UInputModifierNegate>(MappingContext));
		}
	}
}

UInputAction* UEllaInputAdapterComponent::GetInputAction(EUmbrellaInputAction Action) const
{
	const int32 Index = static_cast<int32>(Action);
	return InputActions.IsValidIndex(Index) ? InputActions[Index].Get() : nullptr;
}

void UEllaInputAdapterComponent::BindInput(UEnhancedInputComponent* Input)
{
	if (!Input || !IsFeatureEnabled(EFeatureId::MOVE_04))
	{
		return;
	}
	BuildInputAssets();

	// IMC_Default goes on the local player at priority 0.
	const APawn* Pawn = Cast<APawn>(GetOwner());
	const APlayerController* Controller = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (const ULocalPlayer* LocalPlayer = Controller ? Controller->GetLocalPlayer() : nullptr)
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
		{
			Subsystem->AddMappingContext(MappingContext, DefaultContextPriority);
		}
	}

	for (int32 Index = 0; Index < static_cast<int32>(EUmbrellaInputAction::Count); ++Index)
	{
		const EUmbrellaInputAction Id = static_cast<EUmbrellaInputAction>(Index);
		UInputAction* Action = InputActions[Index];
		if (UmbrellaInputBindings::IsAxisAction(Id))
		{
			Input->BindAction(Action, ETriggerEvent::Triggered, this, &UEllaInputAdapterComponent::HandleAxis, Id);
			Input->BindAction(Action, ETriggerEvent::Completed, this, &UEllaInputAdapterComponent::HandleAxis, Id);
		}
		else
		{
			Input->BindAction(Action, ETriggerEvent::Started, this, &UEllaInputAdapterComponent::HandlePressed, Id);
			Input->BindAction(Action, ETriggerEvent::Completed, this, &UEllaInputAdapterComponent::HandleReleased, Id);
			Input->BindAction(Action, ETriggerEvent::Canceled, this, &UEllaInputAdapterComponent::HandleReleased, Id);
		}
	}
}

void UEllaInputAdapterComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	const APlayerController* Controller = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (const ULocalPlayer* LocalPlayer = Controller ? Controller->GetLocalPlayer() : nullptr)
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
		{
			Subsystem->RemoveMappingContext(MappingContext);
		}
	}
	Super::EndPlay(EndPlayReason);
}

void UEllaInputAdapterComponent::HandlePressed(const FInputActionValue& Value, EUmbrellaInputAction Action)
{
	ApplyPress(Action);
}

void UEllaInputAdapterComponent::HandleReleased(const FInputActionValue& Value, EUmbrellaInputAction Action)
{
	ApplyRelease(Action);
}

void UEllaInputAdapterComponent::HandleAxis(const FInputActionValue& Value, EUmbrellaInputAction Action)
{
	ApplyAxis(Action, Value.Get<float>());
}

void UEllaInputAdapterComponent::ApplyPress(EUmbrellaInputAction Action)
{
	AActor* Owner = GetOwner();
	UUmbrellaStateComponent* State = Owner ? Owner->FindComponentByClass<UUmbrellaStateComponent>() : nullptr;
	UEllaMotorComponent* Motor = Owner ? Owner->FindComponentByClass<UEllaMotorComponent>() : nullptr;
	switch (Action)
	{
	case EUmbrellaInputAction::Shoot:
		if (State)
		{
			State->SetShootHeld(true);
		}
		break;
	case EUmbrellaInputAction::Absorb:
		if (State)
		{
			State->SetAbsorbHeld(true);
		}
		break;
	case EUmbrellaInputAction::Ride:
		if (State)
		{
			State->SetRideHeld(true);
		}
		break;
	case EUmbrellaInputAction::Hop:
		if (Motor)
		{
			Motor->RequestHop();
		}
		break;
	case EUmbrellaInputAction::DashBack:
		if (Motor)
		{
			Motor->RequestDash(EUmbrellaDashDirection::Back);
		}
		break;
	case EUmbrellaInputAction::DashForward:
		if (Motor)
		{
			Motor->RequestDash(EUmbrellaDashDirection::Forward);
		}
		break;
	default:
		break;
	}
}

void UEllaInputAdapterComponent::ApplyRelease(EUmbrellaInputAction Action)
{
	AActor* Owner = GetOwner();
	UUmbrellaStateComponent* State = Owner ? Owner->FindComponentByClass<UUmbrellaStateComponent>() : nullptr;
	if (!State)
	{
		return;
	}
	switch (Action)
	{
	case EUmbrellaInputAction::Shoot:
		State->SetShootHeld(false);
		break;
	case EUmbrellaInputAction::Absorb:
		State->SetAbsorbHeld(false);
		break;
	case EUmbrellaInputAction::Ride:
		State->SetRideHeld(false);
		break;
	default:
		break;
	}
}

void UEllaInputAdapterComponent::ApplyAxis(EUmbrellaInputAction Action, float Value)
{
	AActor* Owner = GetOwner();
	UEllaMotorComponent* Motor = Owner ? Owner->FindComponentByClass<UEllaMotorComponent>() : nullptr;
	if (!Motor)
	{
		return;
	}
	if (Action == EUmbrellaInputAction::Trim)
	{
		Motor->SetTrimAxis(Value);
	}
	else if (Action == EUmbrellaInputAction::MoveX)
	{
		Motor->SetMoveAxis(Value);
	}
}
