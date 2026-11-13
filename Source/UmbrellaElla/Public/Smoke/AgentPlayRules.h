#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"

/**
 * Plain rule functions of the agent play hook (decision D-new-haz16-agent-playtest). The hook lets an outside player
 * (tools/build/agent_play.py) press the same keys a person would, through the normal input path, one turn at a time.
 * Nothing here can move Ella, aim, heal or skip a wait: a turn script is only key presses and waits.
 */
namespace AgentPlayRules
{
	enum class EVerb : uint8
	{
		Down,
		Up,
		Tap,
		Hold,
		Wait,
		ReleaseAll
	};

	/** One scheduled key event of a turn: Millis after the turn starts, key pressed (true) or released. */
	struct UMBRELLAELLA_API FKeyEvent
	{
		int32 Millis = 0;
		FName KeyName;
		bool bPressed = false;
	};

	/** A parsed turn: the key events in time order and how long the turn runs (game milliseconds). */
	struct UMBRELLAELLA_API FTurn
	{
		TArray<FKeyEvent> Events;
		int32 DurationMillis = 0;
		bool bReleaseAllAtEnd = false;
		TArray<FString> Errors;
		bool IsValid() const { return Errors.IsEmpty(); }
	};

	/** Longest single wait / hold / whole turn in game milliseconds, and the most script lines in a turn. */
	constexpr int32 MaxTurnMillis = 3000;
	constexpr int32 MaxLines = 24;
	/** A tap holds the key this long, game milliseconds. */
	constexpr int32 TapMillis = 80;
	/** A turn lasts at least this long, game milliseconds. */
	constexpr int32 MinTurnMillis = 100;
	/** Word counts of the script lines. */
	constexpr int32 HoldWords = 3;

	/** The key a player may press (the GDD default controls only). Returns the engine key name, or NAME_None if refused. */
	UMBRELLAELLA_API FName ResolveKeyName(const FString& Word);

	/**
	 * Parse a turn script, one command per line (blank lines and # comments ignored):
	 *   down KEY | up KEY | tap KEY | hold KEY MS | wait MS | release_all
	 * `hold` presses now and releases after MS without advancing time; `wait` advances time; the turn lasts until the
	 * last wait, hold or tap ends (at least 100 ms). Keys that are not default controls, unknown verbs, a wait or hold
	 * over MaxTurnMillis, more than MaxLines lines or a turn over MaxTurnMillis are errors (the turn is refused whole).
	 */
	UMBRELLAELLA_API FTurn ParseTurn(const FString& Text);

	/** Share of Seconds the player did nothing (no key held, no tap): 1 when Seconds is not positive. */
	UMBRELLAELLA_API float IdleShare(float IdleSeconds, float Seconds);

	/** Turn file name for a turn number: turn_0007.txt. */
	UMBRELLAELLA_API FString TurnFileName(int32 TurnNumber);

	/** The file the player writes to end the attempt: stop.txt. */
	UMBRELLAELLA_API FString StopFileName();

	/** Frame file name for a frame number: f000012.jpg. */
	UMBRELLAELLA_API FString FrameFileName(int32 FrameNumber);

	/** True when a frame is due: real seconds since the last frame reached the interval. */
	UMBRELLAELLA_API bool IsFrameDue(double SinceLastFrameSeconds, double IntervalSeconds);
}
