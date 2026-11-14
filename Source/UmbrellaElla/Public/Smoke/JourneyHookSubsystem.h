#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Tickable.h"
#include "Engine/EngineBaseTypes.h"
#include "JourneyHookSubsystem.generated.h"

class AEllaCharacter;
class AUmbrellaPlayerController;
class SWidget;

enum class EJourneyResult : uint8
{
	Pass,
	Fail
};

/** One line of a journey script (JourneyRules::ParseScript). */
struct UMBRELLAELLA_API FJourneyStep
{
	/** wait, trywait, shot, figureshot, hurtshot, key, hold, click, music, idle, hits, assistwin, retrycheck, log, end, route, routeassist, skipunless. */
	FString Command;
	/** Everything after the command word (a label, a key, a screen name). */
	FString Arg;
	/** Numbers after the argument (timeouts, seconds, damage). */
	TArray<float> Numbers;
	int32 Line = 0;
};

/** Plain rule functions of the journey driver (tests call them). */
namespace JourneyRules
{
	/** Parse a script: one command per line, '#' starts a comment. Unknown commands go to OutErrors with their line. */
	UMBRELLAELLA_API TArray<FJourneyStep> ParseScript(const FString& Text, TArray<FString>& OutErrors);

	/** The flow screen named Word (case-insensitive, e.g. "Title", "Defeat"); false when there is none. */
	UMBRELLAELLA_API bool HasScreenNamed(const FString& Word, uint8& OutScreen);

	/** The name of a flow screen value ("Title"...), for the log. */
	UMBRELLAELLA_API FString ScreenName(uint8 Screen);

	/** True when the label shown on a widget matches the wanted label (case-insensitive, outer spaces ignored). */
	UMBRELLAELLA_API bool IsLabelMatch(const FString& Shown, const FString& Wanted);

	/**
	 * A `click` is done only when it took: the screen changed or its button went away. The gate recheck stalled 60 s on
	 * Defeat (gate-a1a5356e/recheck, Nov 13): the one click sent while the game window was not the active app (active=0;
	 * Josh was using the machine) did nothing, and 28 clicks with active=1 all took. So after ClickSettleSeconds with no
	 * effect the mouse click is sent again, up to ClickMouseTries; then the button gets keyboard focus and Enter (Slate's
	 * Accept, which an SButton takes without the mouse); after that the step fails at the click line, not 60 s later.
	 */
	enum class EJourneyClickNext : uint8 { Done, Wait, ClickAgain, PressAccept, Fail };
	static constexpr double ClickSettleSeconds = 1.0;
	static constexpr int32 ClickMouseTries = 3;
	/** Clicks = presses sent so far (mouse and Enter), at least 1. */
	UMBRELLAELLA_API EJourneyClickNext ClickNext(bool bScreenChanged, bool bButtonShown, double SecondsSinceLastPress, int32 Clicks);
}

/**
 * Journey hook (agentplay lane, workbench builds only, only with -SmokeJourney=<script>). Plays the REAL game from the
 * Start screen through a script of key presses and mouse clicks sent through FSlateApplication (the same path a
 * keyboard and mouse take: menus get them through Slate focus, gameplay through the viewport), waits for the flow
 * screens, saves a capture of the window per `shot` and logs one JOURNEY_STEP line per step (PASS/FAIL, screen,
 * measured values). The first failed `wait` ends the journey (JOURNEY_END blocker=...). Captures and journey.log go to
 * -SmokeJourneyOut=<dir> (default Saved/Journey).
 * Assists, named in their log lines: `hits` lands raw damage on Ella through her Health component's own hit path until a
 * screen shows (a stand-in for waiting on the Keeper's attacks); `assistwin` holds Shoot (real key) and delivers Ella's
 * basic shot to every Keeper part through the parts' own shot receiver, healing her to full each second, until the
 * Story screen. Director's Cut route: `route <N> <timeout>` plays it with real keys only (D held, Space hop and E dash
 * tapped) until the level director reports checkpoint N (4 = the Keeper handoff), logging Ella's X; it does not end the
 * journey when it fails, so a script can follow it with `routeassist <N>`, which places Ella at checkpoint N's stand
 * position through the director's own PlaceAtCheckpoint (4: just past the handoff line) and is named in the log.
 * Each `shot` also measures where Ella, the Keeper and the arena centre land on screen and the picture's contrast there.
 * `figureshot <name>` saves the shot, then a plate (<name>_plate.png, the same frame composite with Ella's actor hidden for
 * a few frames) and <name>.json (her shown state and the box her drawn components project to), so tools/build/visual_qa.py
 * can measure exactly what was drawn for her. `hurtshot <name>` first lands one assisted hit of exactly her active points
 * through her Health hit path (a life lost: the presenter's Hurt trigger) and captures as soon as her presenter shows Hurt (the state holds 0.25 s; a shot's 20 settle frames
 * would miss it): the hurt frame Josh saw as a solid black box (lead order Nov 13 23:26).
 * Nothing else is skipped: every screen and transition is the game's own.
 */
UCLASS()
class UMBRELLAELLA_API UJourneyHookSubsystem : public UGameInstanceSubsystem, public FTickableGameObject
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	virtual void Tick(float DeltaTime) override;
	virtual bool IsTickable() const override;
	virtual bool IsTickableWhenPaused() const override { return true; }
	virtual TStatId GetStatId() const override;

	/** Real seconds the run waits after the last step before it quits. */
	static constexpr double JourneyExitDelaySeconds = 2.0;
	/** Frames a `shot` waits before it captures (menus fade in). */
	static constexpr int32 JourneyShotSettleFrames = 20;
	/** Real seconds between assisted Keeper hits and heals in `assistwin`. */
	static constexpr double JourneyAssistIntervalSeconds = 0.25;
	/** Window pixels at or below this value count as empty (the 3D scene shows through). */
	static constexpr uint8 JourneyEmptyPixelMax = 2;
	static constexpr uint8 JourneyOpaqueAlpha = 255;
	/** Defaults when a script line leaves the number out (seconds). */
	static constexpr float JourneyDefaultKeyTimeoutSeconds = 30.0f;
	static constexpr float JourneyDefaultHitsTimeoutSeconds = 60.0f;
	static constexpr float JourneyDefaultHitIntervalSeconds = 1.0f;
	static constexpr float JourneyDefaultWinTimeoutSeconds = 600.0f;
	static constexpr double JourneyOverlayCheckSeconds = 1.0;
	/** A click waits this long for its button to be laid out before it fails. */
	static constexpr double JourneyClickWaitSeconds = 5.0;
	/** The `texts` step logs at most this many characters of each text. */
	static constexpr int32 JourneyTextLogChars = 40;
	/** `route`: real seconds between Space hops, between E dashes, and between JOURNEY_ROUTE progress lines. */
	static constexpr double JourneyRouteHopSeconds = 0.6;
	static constexpr double JourneyRouteDashSeconds = 0.9;
	static constexpr double JourneyRouteLogSeconds = 2.0;
	/** `route`/`routeassist` checkpoint number that means "the Keeper handoff" (one past the last refuge). */
	static constexpr int32 JourneyRouteHandoff = 4;
	/** `route ... 1`: Shoot is held while Ella is this many units above the checkpoint stand height. */
	static constexpr float JourneyRouteTrimAbove = 300.0f;
	/** `shot` view measure: half-size of the sampled box around a projected point, as a fraction of the frame height. */
	static constexpr float JourneyViewBoxFraction = 0.04f;
	/** `hurtshot`: frames after the hit before the capture (the Hurt flipbook is on screen), and how long it may wait for
	 * the presenter to show Hurt before the step fails (real seconds). */
	static constexpr int32 JourneyHurtSettleFrames = 2;
	static constexpr double JourneyHurtWaitSeconds = 1.0;
	/** `figureshot`/`hurtshot`: frames Ella stays hidden before the plate capture (the hide must reach a rendered frame). */
	static constexpr int32 JourneyPlateFrames = 3;
	/** A sampled box counts as "drawn" when its luminance spread or its offset from the frame mean reaches this (0-255). */
	static constexpr float JourneyViewContrastMin = 12.0f;
	/** Rec. 709 luma weights for the view measure. */
	static constexpr double JourneyLumaR = 0.2126;
	static constexpr double JourneyLumaG = 0.7152;
	static constexpr double JourneyLumaB = 0.0722;

private:
	void StartStep();
	void FinishStep(EJourneyResult Result, const FString& Detail);
	void EndJourney(const FString& Blocker);
	void Log(const FString& Line);

	AUmbrellaPlayerController* GetFlow() const;
	AEllaCharacter* GetElla() const;
	uint8 CurrentScreen() const;

	void PressSlateKey(const FKey& Key);
	void ReleaseSlateKey(const FKey& Key);
	void SendSlateKey(const FKey& Key, EInputEvent Event);
	void ClickLabel(const FString& Label, FString& OutDetail, bool& bOutClicked);
	/** The click fallback: keyboard focus on the labelled button, then Enter. bOutSent false when the button is not shown. */
	void PressAcceptOn(const FString& Label, bool& bOutSent);
	bool IsButtonShown(const FString& Label) const;
	TSharedPtr<SWidget> FindButtonWithLabel(const TSharedRef<SWidget>& Root, const FString& Label) const;
	void CollectTexts(const TSharedRef<SWidget>& Root, TArray<FString>& Out) const;
	void MakeOverlayClickThrough(const TSharedRef<SWidget>& Root);
	void SaveShot(const FString& Name, FString& OutDetail, bool& bOutSaved);
	/** The window read-back with the 3D scene where the UI drew nothing (what `shot` saves). False without a window. */
	bool CaptureFrame(TArray<FColor>& OutBitmap, FIntVector& OutSize) const;
	/** `figureshot`/`hurtshot` driver: shot, hide Ella, plate, sidecar. bHurt: wait for the Hurt state first. */
	void StepFigureShot(const FJourneyStep& Step, bool bHurt, double Elapsed);
	FString DescribeState() const;
	/** Where Ella, the Keeper and the arena centre project in the frame, and the picture's contrast there. */
	FString MeasureView(const TArray<FColor>& Bitmap, const FIntVector& Size) const;
	/** The level director's checkpoint progress: 0..3, 4 once the Keeper handoff fired; -1 when there is no route. */
	int32 RouteProgress() const;

	FString OutDir;
	FString LogText;
	TArray<FJourneyStep> Steps;
	int32 StepIndex = -1;
	double StepStart = 0.0;
	double LastAssist = 0.0;
	int32 StepFrames = 0;
	bool bStepBegun = false;
	bool bEnded = false;
	double EndedAt = 0.0;
	int32 Passed = 0;
	int32 Failed = 0;
	int32 AssistHits = 0;
	FKey HeldKey;
	double LastOverlayCheck = 0.0;
	FString LastKeyFocus;
	double LastRouteHop = 0.0;
	double LastRouteDash = 0.0;
	double LastRouteLog = 0.0;
	float RouteStartX = 0.0f;
	float RouteBestX = 0.0f;
	int32 RouteHeals = 0;
	bool bRouteSinking = false;
	/** `click`: presses sent (0 = not yet clicked), when the last went, the screen before the first, the first's detail. */
	int32 ClickPresses = 0;
	double LastClickPress = 0.0;
	uint8 ClickFrom = 0;
	FString ClickDetail;
	/** `figureshot`/`hurtshot`: 0 = before the shot, 1 = Ella hidden, waiting for the plate; the shot's detail and sidecar. */
	int32 FigurePhase = 0;
	int32 FigurePhaseFrame = 0;
	FString FigureDetail;
	FString FigureJson;
	/** Steps a `skipunless` drops after itself (set just before its FinishStep). */
	int32 SkipAfterStep = 0;
};
