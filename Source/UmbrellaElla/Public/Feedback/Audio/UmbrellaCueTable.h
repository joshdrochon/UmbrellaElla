#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaEvent.h"

/** How a table row picks its bus event: any event of the type, or one whose Detail / TargetId is Value. */
enum class EUmbrellaCueMatch : uint8
{
	Any,
	Detail,
	Target,
	/** The previous Detail seen for this event type was Value and this one is not (e.g. Absorb released). */
	LeftDetail,
};

enum class EUmbrellaCueClass : uint8
{
	SFX,
	Telegraph,
	Music,
	UI,
};

/** One sound-list row bound to the bus event that plays it. Event == Count: no bus event yet, played by name. */
struct FUmbrellaSoundCue
{
	const TCHAR* Id;
	EUmbrellaEventType Event;
	EUmbrellaCueMatch Match;
	const TCHAR* Value;
	EUmbrellaCueClass SoundClass;
	/** SCON_* asset under /Game/UmbrellaElla/Audio/Core, or empty (audio-rules.json concurrency). */
	const TCHAR* Concurrency;
	bool bLoop;
	int32 Takes;
	float PitchJitter;
	/** Loops of one group replace each other; empty = none. */
	const TCHAR* LoopGroup;
};

struct FUmbrellaLoopGroupStop
{
	const TCHAR* Group;
	EUmbrellaEventType Event;
};

/** Pure rules over the generated table (UmbrellaCueTable.cpp, from pipeline/audio/sound-list.csv). */
namespace UmbrellaCueTable
{
	UMBRELLAELLA_API const TArray<FUmbrellaSoundCue>& All();
	UMBRELLAELLA_API const TArray<FUmbrellaLoopGroupStop>& GroupStops();

	/**
	 * The Detail a row matches on: an enum-class name drops its "EType::" prefix. The projectile service stamps
	 * "EUmbrellaShotKind::EnemyRed" while the sound list says "EnemyRed"; without this every shot missed its row
	 * and fell back to the flat Shot placeholder with no concurrency limit (stacked shots, the in-game crackle).
	 */
	UMBRELLAELLA_API FName CueDetail(FName Detail);
	/** Whether one row fires for this event. PrevDetail is the last Detail seen for the event's type. */
	UMBRELLAELLA_API bool IsMatch(const FUmbrellaSoundCue& Cue, const FUmbrellaEvent& Event, FName PrevDetail);
	/** The rows an event plays. */
	UMBRELLAELLA_API TArray<const FUmbrellaSoundCue*> ForEvent(const FUmbrellaEvent& Event, FName PrevDetail = NAME_None);
	UMBRELLAELLA_API const FUmbrellaSoundCue* Find(FName Id);
	/** Every distinct bus event type some row listens to. */
	UMBRELLAELLA_API TArray<EUmbrellaEventType> ListenedEvents();
	/** Class asset name under Audio/Core (SCL_SFX...). */
	UMBRELLAELLA_API const TCHAR* ClassAssetName(EUmbrellaCueClass Class);
}
