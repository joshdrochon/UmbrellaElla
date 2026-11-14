#pragma once

#include "CoreMinimal.h"
#include "Feedback/Art/FigureScale.h"
#include "Components/ActorComponent.h"
#include "EllaAnimPresenterComponent.generated.h"

struct FUmbrellaEvent;
enum class EUmbrellaEventType : uint8;
class UEnhancedInputComponent;
class UPaperFlipbook;
class UPaperFlipbookComponent;
class UStaticMeshComponent;
enum class EArtSlotDraw : uint8;
class UTexture2D;

namespace UmbrellaPresenterConst
{
	/** Stand-in box scale: a slim figure. */
	static const FVector StandInScale(0.5, 0.1, 1.0);
	/** Per-state stand-in shape multipliers (X, Y, Z). */
	static const FVector ShootMul(1.4, 1.0, 1.0);
	static const FVector AbsorbMul(1.8, 1.0, 0.8);
	static const FVector HurtMul(1.0, 1.0, 0.8);
	/**
	 * Box height (relative units) of one Ella picture cell: 2.7 x 100 x actor scale 0.5 = 135 world units, so the idle
	 * figure (79% of its 481x654 cell) stands about 100 px at 1080p in Start Game (about 91 px in Director's Cut, whose
	 * camera margin is wider): the top of the art bible Asset spec "Ella + open umbrella 80-100 px" and about 0.93x the
	 * Other Realm study's figure (10% of the frame height). At 2.28 she read at about 0.6x the study (artella #5).
	 */
	static constexpr double FramedCellHeight = 2.7;
	/** The drawn cell height: FramedCellHeight times the figure scale (D-new-character-scale). The camera frames FramedCellHeight. */
	static constexpr double ArtCellHeight = FramedCellHeight * UmbrellaFigureScale::Ella;
}

namespace UmbrellaEllaOverlayConst
{
	/** Seconds the mode-transition and umbrella-repair pictures stay up after their event. */
	static constexpr float TransitionHoldSeconds = 0.6f;
	static constexpr float RepairHoldSeconds = 0.5f;
	/** Health fraction at or below which the living-critical picture shows (one hit of the default three). */
	static constexpr float CriticalFraction = 1.0f / 3.0f;
	/** Overlay layers over the body: slot id and depth offset (Y units; negative = behind Ella). */
	struct FOverlay
	{
		const TCHAR* Visual;
		float DepthOffset;
	};
	static constexpr float OverlayDepthStep = 1.0f;
	static const FOverlay Overlays[] = {
		{ TEXT("umbrella:prop"), -1.0f * OverlayDepthStep },
		{ TEXT("ella:condition-100-to-0"), 1.0f * OverlayDepthStep },
		{ TEXT("ella:free-fall"), 2.0f * OverlayDepthStep },
		{ TEXT("ella:hop-cartwheel-dash"), 3.0f * OverlayDepthStep },
		{ TEXT("ella:mode-transition"), 4.0f * OverlayDepthStep },
		{ TEXT("ella:living-critical"), 5.0f * OverlayDepthStep },
		{ TEXT("umbrella:repair"), 6.0f * OverlayDepthStep },
	};
}

/** What the overlay rules read: facts about Ella this frame. */
struct FEllaOverlayInput
{
	bool bFreeFall = false;
	bool bMoving = false;
	float HealthFraction = 1.0f;
	float TransitionLeft = 0.0f;
	float RepairLeft = 0.0f;
};

/** What Ella is shown doing. Presentation only. */
UENUM()
enum class EEllaVisualState : uint8
{
	Idle,
	Shoot,
	Absorb,
	Hurt,
	Down
};

/** Animation Presenter: state to Paper2D flipbook, placeholder fallback. Never gameplay authority. Lane e. */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UEllaAnimPresenterComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UEllaAnimPresenterComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);

	/** True while a neutral stand-in shape is shown because no flipbook art is set. */
	bool IsShowingStandIn() const;

	/** Create the visual (flipbook if art is set, otherwise the stand-in). Safe to call twice. */
	void BuildVisual();

	UStaticMeshComponent* GetStandIn() const { return StandIn; }

	/** The visual state an event maps to for this owner; Idle means "no change". Only shots fired by the owner show Shoot. Pure, tests call it. */
	static EEllaVisualState StateForEvent(const FUmbrellaEvent& Event, FName OwnerId);

	/** Stand-in scale for a state (shape stands in for the flipbook of that state). */
	static FVector StandInScaleFor(EEllaVisualState State);

	/** Box scale for a drawn picture: ArtCellHeight tall, as wide as one cell of the row's sheet. Pure. */
	static FVector ArtBoxScaleFor(const UTexture2D* Texture, const struct FArtSlotRow& Row);

	/** True while the stand-in quad shows a state picture from the art slots (T_Ella_<State>[_PH]). */
	bool IsShowingArt() const;

	/** Slot name of a state's flipbook (Open, Attack, Shield, Closed); empty when the state has none. Pure. */
	static FString FlipbookSlotName(EEllaVisualState State);

	/** Object paths tried for a state's flipbook: FB_Ella_<Name> first (passed art), then FB_Ella_<Name>_PH. Pure. */
	static TArray<FString> FlipbookSlotPaths(EEllaVisualState State);

	/** Set the picture for a state (what the slot load does; tests pass a transient texture). Idle also draws the stand-in as art. */
	void SetStateTexture(EEllaVisualState State, UTexture2D* Texture);

	/** True when an overlay slot shows for these facts. Pure. */
	static bool ShouldShowOverlay(const FString& Visual, const FEllaOverlayInput& Input);

	/** Draw one overlay slot (an Overlays visual) as a layer over Ella (null = load its asset). Refuses one already drawn. */
	EArtSlotDraw ShowOverlayArt(const FString& Visual, UTexture2D* Texture);

	/** The overlay component for a slot id, or null. */
	UStaticMeshComponent* FindOverlay(const FString& Visual) const;

	/** Facts the overlays read, from Ella's motor, umbrella state and health. */
	FEllaOverlayInput ReadOverlayInput() const;

	/** Show or hide each overlay for the input (what Tick does). */
	void UpdateOverlays(const FEllaOverlayInput& Input);

	/** Show a state; transient states return to Idle after the hold time. */
	void SetVisualState(EEllaVisualState State);
	EEllaVisualState GetVisualState() const { return VisualState; }

	/** Per-state flipbooks (set by art later); a state without one keeps the stand-in shape. */
	void SetStateFlipbook(EEllaVisualState State, UPaperFlipbook* Flipbook);

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

private:
	void HandleEvent(const FUmbrellaEvent& Event);
	void LoadOverlays();
	void ApplyState();
	void LoadSlotArt();
	void LoadSlotFlipbooks();
	void DrawArt();
	UTexture2D* TextureForState(EEllaVisualState State) const;
	/** The slot row a loaded state picture came from (its sheet layout); the idle row when unknown. */
	const struct FArtSlotRow* RowForTexture(const UTexture2D* Texture) const;

	EEllaVisualState VisualState = EEllaVisualState::Idle;
	float StateTimeLeft = 0.0f;
	float TransitionLeft = 0.0f;
	float RepairLeft = 0.0f;
	TMap<EEllaVisualState, TObjectPtr<UPaperFlipbook>> StateFlipbooks;
	TArray<TPair<EUmbrellaEventType, FDelegateHandle>> Handles;

	/** Art set on a Blueprint subclass or by Flow later; empty = stand-in. */
	UPROPERTY(EditDefaultsOnly, Category = "Art")
	TObjectPtr<UPaperFlipbook> IdleFlipbook;

	UPROPERTY()
	TObjectPtr<UPaperFlipbookComponent> Flipbook;

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> StandIn;

	UPROPERTY()
	TMap<FName, TObjectPtr<UStaticMeshComponent>> OverlayParts;

	/** Slot art per state; a state without a picture shows the Idle one. */
	UPROPERTY()
	TMap<EEllaVisualState, TObjectPtr<UTexture2D>> StateTextures;
};
