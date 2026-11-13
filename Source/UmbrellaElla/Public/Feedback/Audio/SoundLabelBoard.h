#pragma once

#include "CoreMinimal.h"

#if UMBRELLAELLA_WORKBENCH

/** Dev-only sound labels (workbench and Development builds): tuning for the on-screen list. */
namespace UmbrellaSoundLabel
{
	/** Seconds a label line stays before it is gone (about 3 s). */
	inline constexpr float LineLifetimeSeconds = 3.0f;
	/** The last part of the lifetime a line spends fading out. */
	inline constexpr float LineFadeSeconds = 1.0f;
	/** Lines the list shows at once; the oldest drops first. */
	inline constexpr int32 MaxLines = 8;
	/** Screen padding in pixels from the top-left of the view. */
	inline constexpr float ScreenPaddingPixels = 12.0f;
	inline constexpr int32 FontSize = 14;
	/** Viewport layer, above the HUD. */
	inline constexpr int32 ViewportZOrder = 900;
	/** Mapping priority; the key is not consumed, so it never blocks gameplay input. */
	inline constexpr int32 ContextPriority = 100;
	/** The play view is 16:9 (ArenaCameraTuning CameraAspectRatio); the list sits inside it, not in the letterbox bars. */
	inline constexpr float ViewAspect = 16.0f / 9.0f;

	/** Top-left corner of the centred 16:9 view inside a viewport of this size (zero when the viewport is not larger). */
	inline FVector2D ViewOrigin(const FVector2D& ViewportSize)
	{
		if (ViewportSize.X <= 0.0 || ViewportSize.Y <= 0.0)
		{
			return FVector2D::ZeroVector;
		}
		const double Wide = ViewportSize.Y * ViewAspect;
		if (Wide <= ViewportSize.X)
		{
			return FVector2D((ViewportSize.X - Wide) * 0.5, 0.0);
		}
		return FVector2D(0.0, (ViewportSize.Y - ViewportSize.X / ViewAspect) * 0.5);
	}
}

/** One played sound: what the label list shows and the game log prints. */
struct FUmbrellaSoundLabel
{
	FName Id;
	FString Event;
	int32 Take = 0;
	/** Seconds since the sound started. */
	float Age = 0.0f;
};

/**
 * The label list: pure rules, no engine objects. The cue subsystem calls Note for every sound it starts; the F9 toggle
 * flips ShowToggle. Off by default. Lane soundlabel.
 */
class UMBRELLAELLA_API FUmbrellaSoundLabelBoard
{
public:
	/** `SOUND_LABEL id=<Id> event=<Event> take=<NN>` */
	static FString FormatLogLine(FName Id, const FString& Event, int32 Take);
	/** `<Id> | <Event> | take <NN>` */
	static FString FormatScreenLine(const FUmbrellaSoundLabel& Label);
	/** The take number from a SW_<Id>_NN asset name; 0 when the name has no such suffix. */
	static int32 TakeFromAssetName(const FString& AssetName);
	/** 1 while fresh, falling to 0 at the end of the lifetime. */
	static float OpacityForAge(float Age);

	/** Adds a line and writes the log line (even while hidden, so a headless run keeps the record). */
	void Note(FName Id, const FString& Event, int32 Take);
	/** Ages every line by DeltaSeconds and drops the expired ones. */
	void Advance(float DeltaSeconds);

	void Toggle() { bShown = !bShown; }
	bool IsShown() const { return bShown; }

	/** The lines to draw now, oldest first; empty while hidden. */
	TArray<FUmbrellaSoundLabel> GetVisibleLabels() const;
	int32 GetLabelCount() const { return Labels.Num(); }
	const FString& GetLastLogLine() const { return LastLogLine; }

private:
	TArray<FUmbrellaSoundLabel> Labels;
	FString LastLogLine;
	bool bShown = false;
};

#endif // UMBRELLAELLA_WORKBENCH
