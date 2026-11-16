#include "Motor/EllaMotorComponent.h"
#include "Arena/UmbrellaArena.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Components/CapsuleComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Core/UmbrellaSourceIds.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Health/UmbrellaHealthComponent.h"
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
			// One movement path (D-new-move-speeds): possession puts the character movement back in Falling, where it moved
			// Ella a second time with the velocity the motor copies into it. Its tick stays off; the motor sweeps instead.
			Move->SetComponentTickEnabled(false);
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
			if (RefCapsuleRadius < 0.0f)
			{
				RefCapsuleRadius = Capsule->GetUnscaledCapsuleRadius();
				RefCapsuleHalfHeight = Capsule->GetUnscaledCapsuleHalfHeight();
			}
			Capsule->SetCapsuleSize(RefCapsuleRadius * Hitbox, RefCapsuleHalfHeight * Hitbox);
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
		Input.LocalVerticalVelocity += GetDefault<UUmbrellaTuning>()->Motor.WindScale * MotorModel::LocalVerticalTerm(Field.Value.X, Field.Value.Y, Field.Value.Z, static_cast<float>(Owner->GetActorLocation().Z));
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
	// The arena bottom holds even when a harness clears the play bounds: Ella never drops out of the play space.
	const float FloorZ = GetPlayFloorZ();
	bAtPlayFloor = Location.Z <= FloorZ;
	Location.Z = ClampToPlayFloor(static_cast<float>(Location.Z), FloorZ);
	if (bAtPlayFloor && Model.Velocity.Y < 0.0f)
	{
		Model.Velocity.Y = 0.0f;
	}
	// GDD movement ceiling constraint: the arena top holds on the Director's Cut route too, where the arena's ceiling box
	// does not reach (agentplay B7: z 14 962 after 60 s with nothing held). Ella stays in the picture.
	const float CeilingZ = GetPlayCeilingZ();
	bAtPlayCeiling = Location.Z >= CeilingZ;
	Location.Z = ClampToPlayCeiling(static_cast<float>(Location.Z), CeilingZ);
	if (bAtPlayCeiling && Model.Velocity.Y > 0.0f)
	{
		Model.Velocity.Y = 0.0f;
	}
	// Swept move, one axis at a time, so route solids stop her and she slides along their faces (what the character
	// movement's Falling move did before its tick was turned off).
	FVector Swept = Owner->GetActorLocation();
	Swept.X = Location.X;
	Swept.Y = Location.Y;
	Owner->SetActorLocation(Swept, true);
	if (!FMath::IsNearlyEqual(Owner->GetActorLocation().X, Location.X, UE_KINDA_SMALL_NUMBER))
	{
		Model.Velocity.X = 0.0f; // blocked by a solid: no into-wall speed is kept
	}
	Swept = Owner->GetActorLocation();
	Swept.Z = Location.Z;
	Owner->SetActorLocation(Swept, true);
	if (!FMath::IsNearlyEqual(Owner->GetActorLocation().Z, Location.Z, UE_KINDA_SMALL_NUMBER))
	{
		Model.Velocity.Y = 0.0f;
	}
	// Both edges are lethal: the bottom (WIND-03) and the top (D-new-ceiling-lethal, Josh 14 Nov). The clamps above only keep
	// her picture in frame for the death flow; reaching either line defeats her, so the ceiling can never hold her alive.
	UUmbrellaHealthComponent* Health = bBoundaryDeathHeld ? nullptr : Owner->FindComponentByClass<UUmbrellaHealthComponent>();
	if (Health)
	{
		if (bAtPlayFloor && IsFeatureEnabled(EFeatureId::WIND_03))
		{
			Health->DefeatAtBoundary(UmbrellaSourceIds::LethalBottom());
		}
		else if (bAtPlayCeiling)
		{
			Health->DefeatAtBoundary(UmbrellaSourceIds::LethalCeiling());
		}
	}
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

float UEllaMotorComponent::GetPlayFloorZ() const
{
	const AUmbrellaArena* Arena = FindPlayArena();
	return Arena ? static_cast<float>(Arena->LocalPoint(0.0f, 0.0f).Z) + GetCapsuleHalfHeight() : TNumericLimits<float>::Lowest();
}

float UEllaMotorComponent::GetPlayCeilingZ() const
{
	const AUmbrellaArena* Arena = FindPlayArena();
	return Arena ? static_cast<float>(Arena->LocalPoint(0.0f, 1.0f).Z) - GetCapsuleHalfHeight() : TNumericLimits<float>::Max();
}

const AUmbrellaArena* UEllaMotorComponent::FindPlayArena() const
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}
	TActorIterator<AUmbrellaArena> It(const_cast<UWorld*>(World));
	return It ? *It : nullptr;
}

float UEllaMotorComponent::GetCapsuleHalfHeight() const
{
	if (const ACharacter* Character = Cast<ACharacter>(GetOwner()))
	{
		if (const UCapsuleComponent* Capsule = Character->GetCapsuleComponent())
		{
			return Capsule->GetScaledCapsuleHalfHeight();
		}
	}
	return 0.0f;
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
		const FVector2D Velocity = MotorModel::ParseCurrentDirection(Event.Detail) * Event.Value * GetDefault<UUmbrellaTuning>()->Motor.WindScale;
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
