#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Core/UmbrellaLog.h"
#include "Misc/CommandLine.h"
#include "Components/StaticMeshComponent.h"
#include "Core/EllaCharacter.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Motor/EllaMotorComponent.h"
#include "Motor/MotorTuning.h"
#include "Umbrella/UmbrellaStateComponent.h"
#include "Arena/ArenaCameraTuning.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Feedback/Art/ArtSlot.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "PaperFlipbook.h"
#include "PaperFlipbookComponent.h"

UEllaAnimPresenterComponent::UEllaAnimPresenterComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UEllaAnimPresenterComponent::BindInput(UEnhancedInputComponent* Input)
{
}

bool UEllaAnimPresenterComponent::IsShowingStandIn() const
{
	return IsValid(StandIn) && !IsValid(Flipbook) && !ArtSlot::HasArt(StandIn);
}

bool UEllaAnimPresenterComponent::IsShowingArt() const
{
	return ArtSlot::HasArt(StandIn);
}

UTexture2D* UEllaAnimPresenterComponent::TextureForState(EEllaVisualState State) const
{
	if (const TObjectPtr<UTexture2D>* Found = StateTextures.Find(State))
	{
		if (IsValid(*Found))
		{
			return *Found;
		}
	}
	const TObjectPtr<UTexture2D>* Idle = StateTextures.Find(EEllaVisualState::Idle);
	if (Idle && IsValid(*Idle))
	{
		return Idle->Get();
	}
	// Idle has no art: draw any state's own art rather than nothing.
	for (const TPair<EEllaVisualState, TObjectPtr<UTexture2D>>& Pair : StateTextures)
	{
		if (IsValid(Pair.Value))
		{
			return Pair.Value;
		}
	}
	return nullptr;
}

FString UEllaAnimPresenterComponent::FlipbookSlotName(EEllaVisualState State)
{
	switch (State)
	{
	case EEllaVisualState::Idle:
		return TEXT("Open");
	case EEllaVisualState::Shoot:
		return TEXT("Attack");
	case EEllaVisualState::Absorb:
		return TEXT("Shield");
	case EEllaVisualState::Down:
		return TEXT("Closed");
	default:
		return FString();
	}
}

TArray<FString> UEllaAnimPresenterComponent::FlipbookSlotPaths(EEllaVisualState State)
{
	TArray<FString> Paths;
	const FString Name = FlipbookSlotName(State);
	if (!Name.IsEmpty())
	{
		const FString Base = FString::Printf(TEXT("%s/Ella/FB_Ella_%s"), UmbrellaArtSlotConst::GameRoot, *Name);
		const FString Leaf = FString::Printf(TEXT("FB_Ella_%s"), *Name);
		Paths.Add(FString::Printf(TEXT("%s.%s"), *Base, *Leaf));
		Paths.Add(FString::Printf(TEXT("%s%s.%s%s"), *Base, UmbrellaArtSlotConst::PlaceholderSuffix, *Leaf, UmbrellaArtSlotConst::PlaceholderSuffix));
	}
	return Paths;
}

void UEllaAnimPresenterComponent::LoadSlotFlipbooks()
{
	const UEnum* States = StaticEnum<EEllaVisualState>();
	for (int32 Index = 0; Index < States->NumEnums() - 1; ++Index)
	{
		const EEllaVisualState State = static_cast<EEllaVisualState>(States->GetValueByIndex(Index));
		for (const FString& Path : FlipbookSlotPaths(State))
		{
			if (UPaperFlipbook* Found = LoadObject<UPaperFlipbook>(nullptr, *Path, nullptr, LOAD_NoWarn | LOAD_Quiet))
			{
				StateFlipbooks.Add(State, Found);
				break;
			}
		}
	}
	if (!IsValid(IdleFlipbook))
	{
		if (const TObjectPtr<UPaperFlipbook>* Idle = StateFlipbooks.Find(EEllaVisualState::Idle))
		{
			IdleFlipbook = *Idle;
		}
	}
}

void UEllaAnimPresenterComponent::LoadSlotArt()
{
	const UEnum* States = StaticEnum<EEllaVisualState>();
	for (int32 Index = 0; Index < States->NumEnums() - 1; ++Index)
	{
		const FString Visual = TEXT("ella-state:") + States->GetNameStringByIndex(Index);
		const FArtSlotRow* Row = ArtSlot::Find(*Visual);
		if (UTexture2D* Texture = Row ? ArtSlot::LoadTexture(*Row) : nullptr)
		{
			StateTextures.Add(static_cast<EEllaVisualState>(States->GetValueByIndex(Index)), Texture);
		}
	}
	DrawArt();
}

void UEllaAnimPresenterComponent::DrawArt()
{
	UTexture2D* Texture = TextureForState(VisualState);
	const FArtSlotRow* Row = RowForTexture(Texture);
	if (IsValid(StandIn) && !ArtSlot::HasArt(StandIn) && Texture && Row)
	{
		ArtSlot::Apply(StandIn, Texture, *Row, ArtBoxScaleFor(Texture, *Row));
	}
}

void UEllaAnimPresenterComponent::SetStateTexture(EEllaVisualState State, UTexture2D* Texture)
{
	StateTextures.Add(State, Texture);
	DrawArt();
	ApplyState();
}

namespace
{
	const EUmbrellaEventType PresentedEvents[] = {
		EUmbrellaEventType::ProjectileSpawned,
		EUmbrellaEventType::CatchAttempt,
		EUmbrellaEventType::CatchSucceeded,
		EUmbrellaEventType::CatchFailed,
		EUmbrellaEventType::LifeLost,
		EUmbrellaEventType::PlayerDefeated,
	};
}

EEllaVisualState UEllaAnimPresenterComponent::StateForEvent(const FUmbrellaEvent& Event, FName OwnerId)
{
	switch (Event.Type)
	{
	case EUmbrellaEventType::ProjectileSpawned:
		return Event.SourceId == OwnerId ? EEllaVisualState::Shoot : EEllaVisualState::Idle;
	case EUmbrellaEventType::CatchAttempt:
	case EUmbrellaEventType::CatchSucceeded:
		return EEllaVisualState::Absorb;
	case EUmbrellaEventType::CatchFailed:
	case EUmbrellaEventType::LifeLost:
		return EEllaVisualState::Hurt;
	case EUmbrellaEventType::PlayerDefeated:
		return EEllaVisualState::Down;
	default:
		return EEllaVisualState::Idle;
	}
}

FVector UEllaAnimPresenterComponent::ArtBoxScaleFor(const UTexture2D* Texture, const FArtSlotRow& Row)
{
	const double Height = UmbrellaPresenterConst::ArtCellHeight;
	return FVector(Height * ArtSlot::CellAspect(Texture, Row), UmbrellaPresenterConst::StandInScale.Y, Height);
}

const FArtSlotRow* UEllaAnimPresenterComponent::RowForTexture(const UTexture2D* Texture) const
{
	const UEnum* States = StaticEnum<EEllaVisualState>();
	for (const TPair<EEllaVisualState, TObjectPtr<UTexture2D>>& Pair : StateTextures)
	{
		if (Texture && Pair.Value.Get() == Texture)
		{
			const FString Visual = TEXT("ella-state:") + States->GetNameStringByValue(static_cast<int64>(Pair.Key));
			if (const FArtSlotRow* Row = ArtSlot::Find(*Visual))
			{
				return Row;
			}
		}
	}
	return ArtSlot::Find(TEXT("ella-state:Idle"));
}

FVector UEllaAnimPresenterComponent::StandInScaleFor(EEllaVisualState State)
{
	switch (State)
	{
	case EEllaVisualState::Shoot:
		return UmbrellaPresenterConst::StandInScale * UmbrellaPresenterConst::ShootMul;
	case EEllaVisualState::Absorb:
		return UmbrellaPresenterConst::StandInScale * UmbrellaPresenterConst::AbsorbMul;
	case EEllaVisualState::Hurt:
		return UmbrellaPresenterConst::StandInScale * UmbrellaPresenterConst::HurtMul;
	case EEllaVisualState::Down:
		return FVector(UmbrellaPresenterConst::StandInScale.Z, UmbrellaPresenterConst::StandInScale.Y, UmbrellaPresenterConst::StandInScale.X);
	default:
		return UmbrellaPresenterConst::StandInScale;
	}
}

void UEllaAnimPresenterComponent::SetStateFlipbook(EEllaVisualState State, UPaperFlipbook* InFlipbook)
{
	StateFlipbooks.Add(State, InFlipbook);
	ApplyState();
}

void UEllaAnimPresenterComponent::SetVisualState(EEllaVisualState State)
{
	VisualState = State;
	StateTimeLeft = (State == EEllaVisualState::Idle || State == EEllaVisualState::Down) ? 0.0f : GetDefault<UUmbrellaTuning>()->ArenaCamera.EllaStateHoldSeconds;
	const UWorld* World = GetWorld();
	StateStartSeconds = World ? World->GetTimeSeconds() : 0.0;
	DrawnFrame = -1;
	ApplyState();
	PlayGrid();
}

void UEllaAnimPresenterComponent::ApplyState()
{
	if (IsValid(StandIn))
	{
		ArtSlot::SetBoxScale(StandIn, StandInScaleFor(VisualState));
		DrawArt();
		UTexture2D* Picture = TextureForState(VisualState);
		const FArtSlotRow* PictureRow = RowForTexture(Picture);
		if (ArtSlot::HasArt(StandIn) && Picture && PictureRow)
		{
			ArtSlot::SetTexture(StandIn, Picture, *PictureRow);
			DrawnFrame = -1;   // SetTexture puts Frame back to 0: the next PlayGrid shows the right cell again.
			ArtSlot::SetBoxScale(StandIn, ArtBoxScaleFor(Picture, *PictureRow));
		}
	}
	if (IsValid(Flipbook))
	{
		if (const TObjectPtr<UPaperFlipbook>* Found = StateFlipbooks.Find(VisualState))
		{
			if (IsValid(*Found))
			{
				Flipbook->SetFlipbook(*Found);
			}
		}
	}
}

void UEllaAnimPresenterComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	TransitionLeft = FMath::Max(0.0f, TransitionLeft - DeltaTime);
	RepairLeft = FMath::Max(0.0f, RepairLeft - DeltaTime);
	UpdateOverlays(ReadOverlayInput());
	PlayGrid();
	KeepFigureInFrame();
	if (StateTimeLeft > 0.0f)
	{
		StateTimeLeft -= DeltaTime;
		if (StateTimeLeft <= 0.0f)
		{
			SetVisualState(EEllaVisualState::Idle);
		}
	}
}

void UEllaAnimPresenterComponent::HandleEvent(const FUmbrellaEvent& Event)
{
	if (Event.Type == EUmbrellaEventType::CatchSucceeded)
	{
		RepairLeft = UmbrellaEllaOverlayConst::RepairHoldSeconds;
	}
	const AActor* Owner = GetOwner();
	const EEllaVisualState State = StateForEvent(Event, IsValid(Owner) ? Owner->GetFName() : NAME_None);
	if (State != EEllaVisualState::Idle)
	{
		SetVisualState(State);
	}
}

void UEllaAnimPresenterComponent::BeginPlay()
{
	Super::BeginPlay();
	BuildVisual();
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		for (const EUmbrellaEventType Type : PresentedEvents)
		{
			Handles.Emplace(Type, Bus->On(Type).AddUObject(this, &UEllaAnimPresenterComponent::HandleEvent));
		}
	}
}

void UEllaAnimPresenterComponent::EndPlay(const EEndPlayReason::Type Reason)
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		for (const TPair<EUmbrellaEventType, FDelegateHandle>& Pair : Handles)
		{
			Bus->On(Pair.Key).Remove(Pair.Value);
		}
	}
	Handles.Reset();
	Super::EndPlay(Reason);
}

void UEllaAnimPresenterComponent::BuildVisual()
{
	AActor* Owner = GetOwner();
	if (!IsValid(Owner) || IsValid(StandIn) || IsValid(Flipbook) || !IsFeatureEnabled(EFeatureId::ART_03))
	{
		return;
	}
	LoadSlotFlipbooks();
	if (IsValid(IdleFlipbook))
	{
		Flipbook = NewObject<UPaperFlipbookComponent>(Owner, TEXT("EllaFlipbook"));
		Flipbook->SetFlipbook(IdleFlipbook);
		Flipbook->SetupAttachment(Owner->GetRootComponent());
		Flipbook->RegisterComponent();
		return;
	}
	StandIn = NewObject<UStaticMeshComponent>(Owner, TEXT("EllaStandIn"));
	UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (IsValid(Shape))
	{
		StandIn->SetStaticMesh(Shape);
	}
	StandIn->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	StandIn->SetupAttachment(Owner->GetRootComponent());
	StandIn->SetRelativeScale3D(UmbrellaPresenterConst::StandInScale);
	ArtSlot::SetFlatUnlit(StandIn, Owner, UmbrellaArtSlotConst::StandInEllaColor);
	StandIn->RegisterComponent();
	LoadSlotArt();
	LoadOverlays();
}

bool UEllaAnimPresenterComponent::ShouldShowOverlay(const FString& Visual, const FEllaOverlayInput& Input)
{
	if (Visual == TEXT("umbrella:prop"))
	{
		return true;
	}
	if (Visual == TEXT("ella:condition-100-to-0"))
	{
		return Input.HealthFraction < 1.0f;
	}
	if (Visual == TEXT("ella:free-fall"))
	{
		return Input.bFreeFall;
	}
	if (Visual == TEXT("ella:hop-cartwheel-dash"))
	{
		return Input.bMoving;
	}
	if (Visual == TEXT("ella:mode-transition"))
	{
		return Input.TransitionLeft > 0.0f;
	}
	if (Visual == TEXT("ella:living-critical"))
	{
		return Input.HealthFraction <= UmbrellaEllaOverlayConst::CriticalFraction;
	}
	if (Visual == TEXT("umbrella:repair"))
	{
		return Input.RepairLeft > 0.0f;
	}
	return false;
}

UStaticMeshComponent* UEllaAnimPresenterComponent::FindOverlay(const FString& Visual) const
{
	const TObjectPtr<UStaticMeshComponent>* Found = OverlayParts.Find(FName(*Visual));
	return Found ? Found->Get() : nullptr;
}

EArtSlotDraw UEllaAnimPresenterComponent::ShowOverlayArt(const FString& Visual, UTexture2D* Texture)
{
	AActor* Owner = GetOwner();
	const FArtSlotRow* Row = ArtSlot::Find(*Visual);
	const UmbrellaEllaOverlayConst::FOverlay* Layer = nullptr;
	for (const UmbrellaEllaOverlayConst::FOverlay& Candidate : UmbrellaEllaOverlayConst::Overlays)
	{
		Layer = Visual == Candidate.Visual ? &Candidate : Layer;
	}
	if (!IsValid(Owner) || !Owner->GetRootComponent() || !Row || !Layer || !IsFeatureEnabled(EFeatureId::ANIM_04) || FindOverlay(Visual))
	{
		return EArtSlotDraw::NoTexture;
	}
	UTexture2D* Picture = Texture ? Texture : ArtSlot::LoadTexture(*Row);
	if (!Picture)
	{
		return EArtSlotDraw::NoTexture;
	}
	UStaticMeshComponent* Part = NewObject<UStaticMeshComponent>(Owner);
	Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Part->SetGenerateOverlapEvents(false);
	Part->SetupAttachment(Owner->GetRootComponent());
	const EArtSlotDraw Result = ArtSlot::Apply(Part, Picture, *Row, UmbrellaPresenterConst::StandInScale * UmbrellaFigureScale::Ella);
	if (Result != EArtSlotDraw::Drawn)
	{
		Part->DestroyComponent();
		return Result;
	}
	Part->RegisterComponent();
	ArtSlot::SetWorldBoxScale(Part, UmbrellaPresenterConst::StandInScale * UmbrellaFigureScale::Ella);
	Part->SetWorldLocation(Owner->GetActorLocation() + FVector(0.0, Layer->DepthOffset, 0.0));
	Part->SetVisibility(false);
	OverlayParts.Add(FName(*Visual), Part);
	return Result;
}

void UEllaAnimPresenterComponent::LoadOverlays()
{
	for (const UmbrellaEllaOverlayConst::FOverlay& Layer : UmbrellaEllaOverlayConst::Overlays)
	{
		ShowOverlayArt(Layer.Visual, nullptr);
	}
}

FEllaOverlayInput UEllaAnimPresenterComponent::ReadOverlayInput() const
{
	FEllaOverlayInput Input;
	Input.TransitionLeft = TransitionLeft;
	Input.RepairLeft = RepairLeft;
	const AActor* Owner = GetOwner();
	if (const UUmbrellaStateComponent* State = IsValid(Owner) ? Owner->FindComponentByClass<UUmbrellaStateComponent>() : nullptr)
	{
		Input.bFreeFall = State->GetAction() == EUmbrellaAction::FreeFall;
	}
	if (const UEllaMotorComponent* Motor = IsValid(Owner) ? Owner->FindComponentByClass<UEllaMotorComponent>() : nullptr)
	{
		const FMotorTuning& Tuning = GetDefault<UUmbrellaTuning>()->Motor;
		Input.bMoving = Motor->IsHopProtected() || FMath::Abs(Motor->GetVelocity().X) >= Tuning.HopDistance / FMath::Max(Tuning.HopDurationSeconds, KINDA_SMALL_NUMBER);
	}
	if (const UUmbrellaHealthComponent* Health = IsValid(Owner) ? Owner->FindComponentByClass<UUmbrellaHealthComponent>() : nullptr)
	{
		const FHealthState& HealthNow = Health->GetState();
		Input.HealthFraction = HealthNow.Capacity > 0.0f ? FMath::Clamp(HealthNow.Active / HealthNow.Capacity, 0.0f, 1.0f) : 1.0f;
	}
	return Input;
}

void UEllaAnimPresenterComponent::SetDrawTopLimit(float WorldZ)
{
	DrawTopLimitZ = WorldZ;
	bHasDrawTopLimit = true;
	KeepFigureInFrame();
}

int32 UEllaAnimPresenterComponent::GridFrameAt(double Seconds, float Fps, int32 Cols, int32 Rows, bool bLoop)
{
	const int64 Cells = static_cast<int64>(FMath::Max(1, Cols)) * FMath::Max(1, Rows);
	const int64 Step = FMath::Max<int64>(0, FMath::FloorToInt64(FMath::Max(0.0, Seconds) * FMath::Max(0.0f, Fps)));
	return static_cast<int32>(bLoop ? Step % Cells : FMath::Min(Step, Cells - 1));
}

bool UEllaAnimPresenterComponent::LoopsInState(EEllaVisualState State)
{
	return State != EEllaVisualState::Hurt && State != EEllaVisualState::Down;
}

float UEllaAnimPresenterComponent::BottomPadFor(EEllaVisualState State)
{
	switch (State)
	{
	case EEllaVisualState::Hurt: return UmbrellaPresenterConst::HurtBottomPad;
	case EEllaVisualState::Down: return UmbrellaPresenterConst::DownBottomPad;
	default: return UmbrellaPresenterConst::IdleBottomPad;
	}
}

int32 UEllaAnimPresenterComponent::PlayGrid()
{
	// Josh, 14 Nov: Ella drew the approved 24-frame idle as a still (nothing ever set the art-slot Frame). The material
	// walks the grid by Frame (tools/build/assets/art_slot_material.py), so this is the whole flipbook.
	const UWorld* World = GetWorld();
	if (!World || !IsValid(StandIn) || !ArtSlot::HasArt(StandIn))
	{
		return DrawnFrame;
	}
	const FArtSlotRow* Row = RowForTexture(TextureForState(VisualState));
	// Idle loops on the world clock; Hurt and Down play once from their own start (review, ellaanim) and hold the last cell.
	const bool bLoop = LoopsInState(VisualState);
	const double Seconds = bLoop ? World->GetTimeSeconds() : World->GetTimeSeconds() - StateStartSeconds;
	const int32 Frame = Row ? GridFrameAt(Seconds, UmbrellaPresenterConst::GridFps, Row->Cols, Row->Rows, bLoop) : 0;
	if (Frame != DrawnFrame)
	{
		ArtSlot::SetFrame(StandIn, Frame);
		DrawnFrame = Frame;
		// -LogEllaFrame: one line per cell change, for an offscreen check that the idle plays (Josh, 14 Nov).
		static const bool bLogFrames = FParse::Param(FCommandLine::Get(), TEXT("LogEllaFrame"));
		if (bLogFrames)
		{
			const UTexture2D* Picture = TextureForState(VisualState);
			UE_LOG(LogUmbrellaElla, Log, TEXT("ELLA_FRAME t=%.2f frame=%d tex=%s state=%d z=%.0f"), World->GetTimeSeconds(), Frame,
				Picture ? *Picture->GetName() : TEXT("none"), static_cast<int32>(VisualState), GetOwner() ? GetOwner()->GetActorLocation().Z : 0.0);
		}
	}
	return DrawnFrame;
}

void UEllaAnimPresenterComponent::SetDrawBottomLimit(float WorldZ)
{
	DrawBottomLimitZ = WorldZ;
	bHasDrawBottomLimit = true;
	KeepFigureInFrame();
}

float UEllaAnimPresenterComponent::FigureLift(float BottomZ, float LimitZ)
{
	return FMath::Max(0.0f, LimitZ - BottomZ);
}

float UEllaAnimPresenterComponent::FigureDrop(float ActorZ, float DrawnHalf, float LimitZ)
{
	return FMath::Max(0.0f, ActorZ + DrawnHalf - LimitZ);
}

float UEllaAnimPresenterComponent::KeepFigureInFrame()
{
	const AActor* Owner = GetOwner();
	if (!IsValid(Owner) || !IsValid(StandIn))
	{
		return 0.0f;
	}
	// The drawn cell bounds the opaque figure, so keeping the cell under the limit keeps her whole figure in frame. Only
	// the pictures move; the capsule, hurtbox and camera stay where they are. The cell's top is read from its bounds
	// (whatever mesh and turn the art slot uses), taken back to where it would be without the current drop.
	const FBox Cell = StandIn->CalcBounds(StandIn->GetComponentTransform()).GetBox();
	const float UndroppedTop = static_cast<float>(Cell.Max.Z) + CurrentDrop;
	const float UndroppedBottom = static_cast<float>(Cell.Min.Z + BottomPadFor(VisualState) * (Cell.Max.Z - Cell.Min.Z)) + CurrentDrop;
	const float ActorZ = static_cast<float>(Owner->GetActorLocation().Z);
	const float Lowered = bHasDrawTopLimit ? FigureDrop(ActorZ, UndroppedTop - ActorZ, DrawTopLimitZ) : 0.0f;
	// The bottom wins only if the figure were taller than the clear frame (never at 2x): then its feet stay in view.
	const float Lifted = bHasDrawBottomLimit ? FigureLift(UndroppedBottom - Lowered, DrawBottomLimitZ) : 0.0f;
	const float Drop = Lowered - Lifted;
	if (FMath::IsNearlyEqual(Drop, CurrentDrop, UmbrellaPresenterConst::FigureDropTolerance))
	{
		return CurrentDrop;
	}
	const float RelativeZ = -Drop / FMath::Max(KINDA_SMALL_NUMBER, static_cast<float>(Owner->GetActorScale3D().Z));
	auto Lower = [RelativeZ](UStaticMeshComponent* Part)
	{
		if (IsValid(Part))
		{
			FVector At = Part->GetRelativeLocation();
			At.Z = RelativeZ;
			Part->SetRelativeLocation(At);
		}
	};
	Lower(StandIn);
	for (const TPair<FName, TObjectPtr<UStaticMeshComponent>>& Pair : OverlayParts)
	{
		Lower(Pair.Value.Get());
	}
	CurrentDrop = Drop;
	return CurrentDrop;
}

void UEllaAnimPresenterComponent::UpdateOverlays(const FEllaOverlayInput& Input)
{
	for (const TPair<FName, TObjectPtr<UStaticMeshComponent>>& Pair : OverlayParts)
	{
		if (IsValid(Pair.Value))
		{
			Pair.Value->SetVisibility(ShouldShowOverlay(Pair.Key.ToString(), Input));
		}
	}
}
