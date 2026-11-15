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
	/**
	 * Grid sheet playback rate (frames per second): the approved idle cut's sidecar fps
	 * (pipeline/art/proof/artvideo/ella-idle/Ella_idle_N24_grid.sprite.json, "fps": 6.13). Every multi-cell state picture plays at it.
	 */
	static constexpr float GridFps = 6.13f;
	/**
	 * Share of a picture cell under Ella's feet that is empty, per sheet: the lowest opaque row (alpha >= 128) over all 24
	 * cells is at 81.2% of the cell (idle, Ella_idle_N24_grid.png), 93.6% (hurt, ella-hurt_N24_grid.png) and 97.6% (down,
	 * ella-down_N24_grid.png). The bottom-of-frame check keeps her feet, not the empty cell edge, in view.
	 */
	static constexpr float IdleBottomPad = 0.188f;
	static constexpr float HurtBottomPad = 0.064f;
	static constexpr float DownBottomPad = 0.024f;
	/** Aimed shot sheet (pipeline/art/proof/artella/shoot/ella-aimshot_N24_grid.png): lowest opaque row 527 of 654 over all cells. */
	static constexpr float AimShotBottomPad = 0.194f;
	/** World units under which a change of the ceiling drop is ignored (no per-tick re-placing for float noise). */
	static constexpr float FigureDropTolerance = 0.01f;
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
	Down,
	/** Aimed shot (D-new-aimed-shot): the pose walks with the charge, then holds its last cell (the flash) while the beam shows. */
	AimShot
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

	/**
	 * Stand-in scale for a state (shape stands in for the flipbook of that state). Deliberately NOT times
	 * UmbrellaFigureScale::Ella: the plain box is the hitbox-sized stand-in shown only when no picture loads (a _PH-free
	 * build would still read her true hurtbox size), and ArtSlot's admission draws no picture through it. Drawn pictures
	 * (ArtBoxScaleFor, overlays) carry the 1.5x figure scale (D-new-character-scale).
	 */
	static FVector StandInScaleFor(EEllaVisualState State);

	/**
	 * B7/B11 + D-new-character-scale: the world Z the drawn figure's top may not pass (the frame's clear top: frame top
	 * minus the Director's Cut title band). Set by UFrameCompositionSubsystem::ApplyCameraMargin; the camera never moves for it.
	 */
	void SetDrawTopLimit(float WorldZ);

	/**
	 * Ella 2x (Josh, 14 Nov): the world Z the drawn figure's bottom may not pass (the frame bottom). At the floor the 2x
	 * picture reaches under the frame; the picture is lifted (never the capsule, hurtbox or camera). Set with the top limit.
	 */
	void SetDrawBottomLimit(float WorldZ);

	/** Lift for a drawn picture whose bottom sits at BottomZ over LimitZ: how far it must sit higher (>= 0). Pure. */
	static float FigureLift(float BottomZ, float LimitZ);

	/** Drop for a drawn picture whose half-height is DrawnHalf at ActorZ under LimitZ: how far it must sit lower (>= 0). Pure. */
	static float FigureDrop(float ActorZ, float DrawnHalf, float LimitZ);

	/** Move the drawn pictures (never the capsule or hurtbox) just enough that the figure stays in frame: lowered under the top limit, lifted over the bottom one. Tick calls it. Returns the drop (negative = lifted). */
	float KeepFigureInFrame();

	float GetFigureDrop() const { return CurrentDrop; }

	/** Cell of a Cols x Rows grid sheet shown at Seconds: walks every cell left to right, row by row, and loops. Pure. */
	static int32 GridFrameAt(double Seconds, float Fps, int32 Cols, int32 Rows, bool bLoop = true);

	/** True when Ella has health again (a retry or respawn after defeat): the Down picture gives way to Idle. Pure. */
	static bool IsAliveAgain(float HealthFraction);

	/**
	 * AimShot cell for the charge: cell 0 until ShowSeconds into the hold, then it walks to the last cell as the charge
	 * reaches ChargeSeconds, and holds the last cell (the flash at the tip) once the beam fired. Pure.
	 */
	static int32 AimShotFrameAt(float HeldSeconds, float ShowSeconds, float ChargeSeconds, bool bBeamFired, int32 Cells);

	/** True while the attack emitter is charging past the aim-pose time or its aimed beam is on screen. */
	bool ShouldShowAimPose() const;

	/** True when a state's picture loops (Idle and the states that show the idle art); Hurt and Down play once and hold. Pure. */
	static bool IsLoopingState(EEllaVisualState State);

	/** Empty share under the feet of the picture a state draws (IdleBottomPad, HurtBottomPad, DownBottomPad). Pure. */
	static float BottomPadFor(EEllaVisualState State);

	/** Show the current picture's cell for the world time (a grid sheet animates; a single picture stays on 0). Tick calls it. */
	int32 PlayGrid();

	/** The cell the picture draws now (ArtSlot "Frame"), -1 before any picture. */
	int32 GetDrawnFrame() const { return DrawnFrame; }

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
	/** The grid cell the picture draws now (ArtSlot "Frame"), -1 before any picture or after a texture swap. */
	int32 DrawnFrame = -1;
	/** World time the current visual state began: a Hurt or Down clip plays from its own cell 0. */
	double StateStartSeconds = 0.0;
	float StateTimeLeft = 0.0f;
	float TransitionLeft = 0.0f;
	float RepairLeft = 0.0f;
	float DrawTopLimitZ = 0.0f;
	bool bHasDrawTopLimit = false;
	float DrawBottomLimitZ = 0.0f;
	bool bHasDrawBottomLimit = false;
	float CurrentDrop = 0.0f;
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
