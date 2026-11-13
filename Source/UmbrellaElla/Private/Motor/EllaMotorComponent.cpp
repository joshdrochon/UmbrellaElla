#include "Motor/EllaMotorComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Motor/HeroSizeRules.h"
#include "Motor/MotorTuning.h"
#include "Umbrella/UmbrellaFlightTuning.h"
#include "Umbrella/UmbrellaPlayerIds.h"
#include "Umbrella/UmbrellaStateComponent.h"

UEllaMotorComponent::UEllaMotorComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PrePhysics;
}

void UEllaMotorComponent::BindInput(UEnhancedInputComponent* Input)
{
	// Requests arrive through the Input Adapter; nothing to bind here.
}

void UEllaMotorComponent::BeginPlay()
{
	Super::BeginPlay();
	AActor* Owner = GetOwner();
	UmbrellaState = Owner ? Owner->FindComponentByClass<UUmbrellaStateComponent>() : nullptr;
	if (ACharacter* Character = Cast<ACharacter>(Owner))
	{
		// The motor integrates position itself: no gravity, no engine walking/falling.
		if (UCharacterMovementComponent* Move = Character->GetCharacterMovement())
		{
			Move->GravityScale = 0.0f;
			Move->SetMovementMode(MOVE_None);
		}
	}
	if (Owner)
	{
		FVector Location = Owner->GetActorLocation();
		Location.Y = UmbrellaDrawOrder::EllaY;
		Owner->SetActorLocation(Location);
	}
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		WindEnteredHandle = Bus->On(EUmbrellaEventType::WindEntered).AddUObject(this, &UEllaMotorComponent::OnWindEntered);
		WindExitedHandle = Bus->On(EUmbrellaEventType::WindExited).AddUObject(this, &UEllaMotorComponent::OnWindExited);
		HealthHandle = Bus->On(EUmbrellaEventType::PlayerHealthChanged).AddUObject(this, &UEllaMotorComponent::OnHealthChanged);
	}
	ApplyHeroSize(GetDefault<UUmbrellaTuning>()->Motor);
}

void UEllaMotorComponent::ApplyHeroSize(const FMotorTuning& Size)
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}
	// HAZ-10/13/14: actor scale 0.5 x HeroSize; the hurtbox capsule shrinks by the hitbox scale on top.
	const bool bHeroSize = IsFeatureEnabled(EFeatureId::HAZ_10) && IsFeatureEnabled(EFeatureId::HAZ_13) && IsFeatureEnabled(EFeatureId::HAZ_14);
	if (bHeroSize)
	{
		Owner->SetActorScale3D(FVector(HeroSizeRules::ActorScale(Size)));
	}
	if (const ACharacter* SizedCharacter = bHeroSize ? Cast<ACharacter>(Owner) : nullptr)
	{
		if (UCapsuleComponent* Capsule = SizedCharacter->GetCapsuleComponent())
		{
			const float Hitbox = HeroSizeRules::ClampedHitboxScale(Size);
			if (Hitbox < 1.0f)
			{
				Capsule->SetCapsuleSize(Capsule->GetUnscaledCapsuleRadius() * Hitbox, Capsule->GetUnscaledCapsuleHalfHeight() * Hitbox);
			}
		}
	}
}

void UEllaMotorComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		Bus->On(EUmbrellaEventType::WindEntered).Remove(WindEnteredHandle);
		Bus->On(EUmbrellaEventType::WindExited).Remove(WindExitedHandle);
		Bus->On(EUmbrellaEventType::PlayerHealthChanged).Remove(HealthHandle);
	}
	Super::EndPlay(EndPlayReason);
}

void UEllaMotorComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	StepMotor(DeltaTime);
}

void UEllaMotorComponent::StepMotor(float DeltaSeconds)
{
	AActor* Owner = GetOwner();
	if (!Owner || !IsFeatureEnabled(EFeatureId::MOVE_13))
	{
		return;
	}
	if (!UmbrellaState)
	{
		UmbrellaState = Owner->FindComponentByClass<UUmbrellaStateComponent>();
	}
	if (UmbrellaState && UmbrellaState->IsLocked())
	{
		// Locks resolve before player actions. Ella holds still.
		Model.Velocity = FVector2D::ZeroVector;
		return;
	}
	FMotorInput Input;
	Input.Action = UmbrellaState ? UmbrellaState->GetAction() : EUmbrellaAction::Rise;
	Input.bRideHeld = UmbrellaState && UmbrellaState->IsRideHeld();
	Input.TrimAxis = TrimAxis;
	Input.MoveAxis = MoveAxis;
	Input.bInCurrent = ActiveCurrents.Num() > 0;
	Input.CurrentVelocity = SumCurrents();
	Input.ForcedVelocity = SumForcedPushes();
	for (const TPair<FName, FVector>& Field : ActiveLocalFields)
	{
		Input.LocalVerticalVelocity += MotorModel::LocalVerticalTerm(Field.Value.X, Field.Value.Y, Field.Value.Z, static_cast<float>(Owner->GetActorLocation().Z));
	}
	Input.LiftMultiplier = LiftMultiplier;

	const FMotorTuning& Tuning = GetDefault<UUmbrellaTuning>()->Motor;
	const FVector2D Move = MotorModel::Step(Model, Input, Tuning, DeltaSeconds);

	FVector Location = Owner->GetActorLocation();
	Location.X += Move.X;
	Location.Z += Move.Y;
	if (PlayBounds.bIsValid)
	{
		Location.X = FMath::Clamp(Location.X, PlayBounds.Min.X, PlayBounds.Max.X);
		Location.Z = FMath::Clamp(Location.Z, PlayBounds.Min.Y, PlayBounds.Max.Y);
	}
	Owner->SetActorLocation(Location);
	if (const ACharacter* Character = Cast<ACharacter>(Owner))
	{
		if (UCharacterMovementComponent* CharacterMove = Character->GetCharacterMovement())
		{
			CharacterMove->Velocity = GetVelocity();
		}
	}
}

void UEllaMotorComponent::RequestHop()
{
	MotorModel::Request(Model, EMotorRequest::Hop, GetDefault<UUmbrellaTuning>()->Motor);
}

void UEllaMotorComponent::RequestDash(EUmbrellaDashDirection Direction)
{
	const EMotorRequest Request = Direction == EUmbrellaDashDirection::Back ? EMotorRequest::DashBack : EMotorRequest::DashForward;
	MotorModel::Request(Model, Request, GetDefault<UUmbrellaTuning>()->Motor);
}

void UEllaMotorComponent::SetTrimAxis(float Axis)
{
	TrimAxis = FMath::Clamp(Axis, -1.0f, 1.0f);
}

void UEllaMotorComponent::SetMoveAxis(float Axis)
{
	MoveAxis = FMath::Clamp(Axis, -1.0f, 1.0f);
}

void UEllaMotorComponent::SetPlayBounds(const FBox2D& Bounds)
{
	PlayBounds = Bounds;
}

void UEllaMotorComponent::ClearPlayBounds()
{
	PlayBounds = FBox2D(ForceInit);
}

FVector UEllaMotorComponent::GetVelocity() const
{
	return FVector(Model.Velocity.X, 0.0, Model.Velocity.Y);
}

bool UEllaMotorComponent::IsHopProtected() const
{
	return MotorModel::IsProtected(Model);
}

bool UEllaMotorComponent::IsRiding() const
{
	return Model.bRiding;
}

bool UEllaMotorComponent::IsEventForElla(const FUmbrellaEvent& Event) const
{
	// Senders follow the repo convention TargetId = actor name (AWindCurrent), others use the Ella id or none.
	const AActor* Owner = GetOwner();
	return Event.TargetId.IsNone() || Event.TargetId == UmbrellaPlayerIds::Ella || (Owner && Event.TargetId == Owner->GetFName());
}

FVector2D UEllaMotorComponent::SumCurrents() const
{
	FVector2D Sum = FVector2D::ZeroVector;
	for (const TPair<FName, FVector2D>& Current : ActiveCurrents)
	{
		Sum += Current.Value;
	}
	return Sum;
}

FVector2D UEllaMotorComponent::SumForcedPushes() const
{
	FVector2D Sum = FVector2D::ZeroVector;
	for (const TPair<FName, FVector2D>& Push : ForcedPushes)
	{
		Sum += Push.Value;
	}
	return Sum;
}

void UEllaMotorComponent::OnWindEntered(const FUmbrellaEvent& Event)
{
	if (IsEventForElla(Event))
	{
		// Current contract: force (speed, units/s) in Value, direction word or "x,z" in Detail.
		const FVector2D Velocity = MotorModel::ParseCurrentDirection(Event.Detail) * Event.Value;
		if (MotorModel::IsForcedSource(Event.SourceId))
		{
			ForcedPushes.Add(Event.SourceId, Velocity);
		}
		else
		{
			ActiveCurrents.Add(Event.SourceId, Velocity);
			float Gain = 0.0f;
			float CentreZ = 0.0f;
			float Compensation = 0.0f;
			if (MotorModel::HasLocalField(Event.Detail, Gain, CentreZ, Compensation))
			{
				ActiveLocalFields.Add(Event.SourceId, FVector(Gain, CentreZ, Compensation));
			}
		}
	}
}

void UEllaMotorComponent::OnWindExited(const FUmbrellaEvent& Event)
{
	if (IsEventForElla(Event))
	{
		ActiveCurrents.Remove(Event.SourceId);
		ActiveLocalFields.Remove(Event.SourceId);
		ForcedPushes.Remove(Event.SourceId);
	}
}

void UEllaMotorComponent::OnHealthChanged(const FUmbrellaEvent& Event)
{
	// Lift contract: Value = active health in hits, Amount = per-life capacity in hits (0 = tuning default).
	const FUmbrellaFlightTuning& Flight = GetDefault<UUmbrellaTuning>()->UmbrellaFlight;
	const float Capacity = Event.Amount > 0 ? static_cast<float>(Event.Amount) : Flight.DefaultLifeCapacityHits;
	const float NewLift = UmbrellaActionRules::LiftMultiplier(Event.Value, Capacity, GetDefault<UUmbrellaTuning>()->Health.MinLift);
	if (FMath::IsNearlyEqual(NewLift, LiftMultiplier))
	{
		return;
	}
	LiftMultiplier = NewLift;
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Out;
		Out.Type = EUmbrellaEventType::LiftAvailabilityChanged;
		Out.SourceId = UmbrellaPlayerIds::Ella;
		Out.Value = LiftMultiplier;
		Bus->Broadcast(Out);
	}
}
