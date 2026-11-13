#pragma once

#include "CoreMinimal.h"
#include "Attack/SpellRules.h"

/** Which requirement family an effect belongs to (each has its own feature flag). */
enum class EVfxFamily : uint8
{
	Weapon,
	Keeper,
	Story
};

/** The render layer an effect draws on. Effects never share a layer with character or scenery sprites. */
enum class EVfxLayer : uint8
{
	Vfx,
	Hazard,
	Foreground,
	Backdrop
};

/** Stages a weapon effect can have. Not every spell has every stage. */
enum class EVfxWeaponStage : uint8
{
	Channel,
	Release,
	Travel,
	Sustain,
	Impact,
	Pierce,
	Fade,
	Count
};

/** One effect: its art sheet, layer, timing and light. Plain data; the sheets are made by Art/Source/VFX. */
struct FVfxArtRow
{
	const TCHAR* Key;
	const TCHAR* Sheet;
	EVfxFamily Family;
	EVfxLayer Layer;
	/** World size of the square quad the sheet is shown on. */
	float Size;
	int32 Frames;
	float Fps;
	/** A looping effect is held until its state ends; a one-shot ends after its last frame. */
	bool bLoop;
	bool bFlashing;
	/** True when the effect lights nearby surfaces (bright magic); false for dust, veils and harmless cues. */
	bool bLit;
	/** sRGB colour of the light the effect throws (0xRRGGBB). */
	uint32 LightHex;
};

namespace UmbrellaVfxLayerConst
{
	/**
	 * Backdrop-layer effects (the light shaft) sit this far behind the arena layer (screenfix B2). At
	 * BackgroundNearY the shaft hid behind the scene pictures (up to BackgroundNearY + 15), leaving only the dark umbra.
	 */
	static constexpr float BackdropBehindArena = 10.0f;
}

namespace VfxCatalogData
{
	/** Colours: GDD SH1.0 shot colours (pipeline/art/references.json vfx_spec). */
	static constexpr uint32 Gold = 0xE9C46A;
	static constexpr uint32 Red = 0xFF3658;
	static constexpr uint32 Yellow = 0xFFD84A;
	static constexpr uint32 Core = 0xFFF5DC;
	static constexpr uint32 AshBlue = 0x8FA3B0;
	static constexpr uint32 None = 0x000000;
	/** Every sheet is one row of this many square cells. */
	static constexpr int32 SheetFrames = 8;
	static constexpr float FastFps = 20.0f;
	static constexpr float LoopFps = 12.0f;
	static constexpr float SmallSize = 48.0f;
	static constexpr float MediumSize = 96.0f;
	static constexpr float LargeSize = 192.0f;
	static constexpr float HugeSize = 640.0f;

	inline constexpr FVfxArtRow Rows[] = {
		// Four weapons.
		{ TEXT("SmallBlastRelease"), TEXT("VFX_GoldRelease"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, FastFps, false, false, true, Gold },
		{ TEXT("SmallBlastTravel"), TEXT("VFX_GoldTravel"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, LoopFps, true, false, true, Gold },
		{ TEXT("SmallBlastImpact"), TEXT("VFX_GoldImpact"), EVfxFamily::Weapon, EVfxLayer::Vfx, MediumSize, SheetFrames, FastFps, false, true, true, Gold },
		{ TEXT("SmallBlastFade"), TEXT("VFX_GoldFade"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, FastFps, false, false, false, None },
		{ TEXT("StreamStartup"), TEXT("VFX_StreamStart"), EVfxFamily::Weapon, EVfxLayer::Vfx, MediumSize, SheetFrames, FastFps, false, false, true, Gold },
		{ TEXT("StreamSustain"), TEXT("VFX_StreamSustain"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, LoopFps, true, false, true, Gold },
		{ TEXT("StreamContact"), TEXT("VFX_GoldImpact"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, FastFps, false, false, true, Gold },
		{ TEXT("StreamStop"), TEXT("VFX_GoldFade"), EVfxFamily::Weapon, EVfxLayer::Vfx, MediumSize, SheetFrames, FastFps, false, false, false, None },
		{ TEXT("TwinStarRelease"), TEXT("VFX_GoldRelease"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, FastFps, false, false, true, Gold },
		{ TEXT("TwinStarHead"), TEXT("VFX_TwinStarHead"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, LoopFps, true, false, true, Gold },
		{ TEXT("TwinStarImpact"), TEXT("VFX_GoldImpact"), EVfxFamily::Weapon, EVfxLayer::Vfx, MediumSize, SheetFrames, FastFps, false, true, true, Gold },
		{ TEXT("TwinStarFade"), TEXT("VFX_GoldFade"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, FastFps, false, false, false, None },
		{ TEXT("NeedleChannel"), TEXT("VFX_NeedleChannel"), EVfxFamily::Weapon, EVfxLayer::Vfx, MediumSize, SheetFrames, LoopFps, true, false, true, Gold },
		{ TEXT("NeedlePulse"), TEXT("VFX_GoldRelease"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, FastFps, false, false, true, Gold },
		{ TEXT("NeedleSliver"), TEXT("VFX_NeedleSliver"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, LoopFps, true, false, true, Gold },
		{ TEXT("NeedlePierce"), TEXT("VFX_NeedlePierce"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, FastFps, false, false, true, Gold },
		{ TEXT("NeedleImpact"), TEXT("VFX_GoldImpact"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, FastFps, false, true, true, Gold },
		{ TEXT("NeedleFade"), TEXT("VFX_GoldFade"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, FastFps, false, false, false, None },
		{ TEXT("ProtectedContact"), TEXT("VFX_Blocked"), EVfxFamily::Weapon, EVfxLayer::Vfx, SmallSize, SheetFrames, FastFps, false, false, false, None },
		// Keeper of Time.
		{ TEXT("TalonWarning"), TEXT("VFX_KeeperWarning"), EVfxFamily::Keeper, EVfxLayer::Hazard, LargeSize, SheetFrames, LoopFps, true, false, true, Red },
		{ TEXT("TalonStrike"), TEXT("VFX_KeeperStrike"), EVfxFamily::Keeper, EVfxLayer::Vfx, LargeSize, SheetFrames, FastFps, false, true, true, Red },
		{ TEXT("TalonRecovery"), TEXT("VFX_KeeperRecovery"), EVfxFamily::Keeper, EVfxLayer::Hazard, MediumSize, SheetFrames, LoopFps, false, false, false, None },
		{ TEXT("MechFrontWarning"), TEXT("VFX_KeeperWarning"), EVfxFamily::Keeper, EVfxLayer::Hazard, LargeSize, SheetFrames, LoopFps, true, false, true, Red },
		{ TEXT("MechFrontStrike"), TEXT("VFX_KeeperStrike"), EVfxFamily::Keeper, EVfxLayer::Vfx, LargeSize, SheetFrames, FastFps, false, true, true, Red },
		{ TEXT("MechFrontRecovery"), TEXT("VFX_KeeperRecovery"), EVfxFamily::Keeper, EVfxLayer::Hazard, MediumSize, SheetFrames, LoopFps, false, false, false, None },
		{ TEXT("MechMiddleWarning"), TEXT("VFX_KeeperWarning"), EVfxFamily::Keeper, EVfxLayer::Hazard, LargeSize, SheetFrames, LoopFps, true, false, true, Red },
		{ TEXT("MechMiddleStrike"), TEXT("VFX_KeeperStrike"), EVfxFamily::Keeper, EVfxLayer::Vfx, LargeSize, SheetFrames, FastFps, false, true, true, Red },
		{ TEXT("MechMiddleRecovery"), TEXT("VFX_KeeperRecovery"), EVfxFamily::Keeper, EVfxLayer::Hazard, MediumSize, SheetFrames, LoopFps, false, false, false, None },
		{ TEXT("MechRearWarning"), TEXT("VFX_KeeperWarning"), EVfxFamily::Keeper, EVfxLayer::Hazard, LargeSize, SheetFrames, LoopFps, true, false, true, Red },
		{ TEXT("MechRearStrike"), TEXT("VFX_KeeperStrike"), EVfxFamily::Keeper, EVfxLayer::Vfx, LargeSize, SheetFrames, FastFps, false, true, true, Red },
		{ TEXT("MechRearRecovery"), TEXT("VFX_KeeperRecovery"), EVfxFamily::Keeper, EVfxLayer::Hazard, MediumSize, SheetFrames, LoopFps, false, false, false, None },
		{ TEXT("GustWarning"), TEXT("VFX_GustPuff"), EVfxFamily::Keeper, EVfxLayer::Hazard, LargeSize, SheetFrames, LoopFps, true, false, false, None },
		{ TEXT("GustRelease"), TEXT("VFX_GustPuff"), EVfxFamily::Keeper, EVfxLayer::Vfx, LargeSize, SheetFrames, FastFps, false, false, false, None },
		{ TEXT("GustTravel"), TEXT("VFX_Gust"), EVfxFamily::Keeper, EVfxLayer::Hazard, LargeSize, SheetFrames, LoopFps, true, false, false, None },
		{ TEXT("GustExpiry"), TEXT("VFX_GustPuff"), EVfxFamily::Keeper, EVfxLayer::Hazard, MediumSize, SheetFrames, FastFps, false, false, false, None },
		{ TEXT("ClockBeat"), TEXT("VFX_ClockBeat"), EVfxFamily::Keeper, EVfxLayer::Vfx, LargeSize, SheetFrames, FastFps, false, true, true, Red },
		{ TEXT("ClockOpening"), TEXT("VFX_ClockOpen"), EVfxFamily::Keeper, EVfxLayer::Vfx, LargeSize, SheetFrames, LoopFps, false, false, true, Yellow },
		{ TEXT("ClockCover"), TEXT("VFX_ClockOpen"), EVfxFamily::Keeper, EVfxLayer::Vfx, LargeSize, SheetFrames, LoopFps, false, false, false, None },
		{ TEXT("KeeperPartHit"), TEXT("VFX_PartHit"), EVfxFamily::Keeper, EVfxLayer::Vfx, MediumSize, SheetFrames, FastFps, false, true, true, Gold },
		{ TEXT("KeeperPartBroken"), TEXT("VFX_PartBreak"), EVfxFamily::Keeper, EVfxLayer::Vfx, LargeSize, SheetFrames, LoopFps, false, true, true, Core },
		{ TEXT("KeeperStun"), TEXT("VFX_Stun"), EVfxFamily::Keeper, EVfxLayer::Vfx, MediumSize, SheetFrames, LoopFps, true, false, false, None },
		{ TEXT("KeeperSlow"), TEXT("VFX_Slow"), EVfxFamily::Keeper, EVfxLayer::Hazard, LargeSize, SheetFrames, LoopFps, true, false, false, None },
		{ TEXT("KeeperEyeExposed"), TEXT("VFX_EyeExposed"), EVfxFamily::Keeper, EVfxLayer::Vfx, MediumSize, SheetFrames, LoopFps, true, false, true, Yellow },
		{ TEXT("KeeperBlackout"), TEXT("VFX_Blackout"), EVfxFamily::Keeper, EVfxLayer::Foreground, HugeSize, SheetFrames, LoopFps, true, false, false, None },
		{ TEXT("KeeperRestoration"), TEXT("VFX_Restoration"), EVfxFamily::Keeper, EVfxLayer::Foreground, HugeSize, SheetFrames, LoopFps, false, false, true, Core },
		{ TEXT("KeeperDeparture"), TEXT("VFX_Departure"), EVfxFamily::Keeper, EVfxLayer::Vfx, LargeSize, SheetFrames, LoopFps, true, false, true, Core },
		// Story: the light that falls into the abyss and the umbrella's shadow.
		{ TEXT("LightShaft"), TEXT("VFX_LightShaft"), EVfxFamily::Story, EVfxLayer::Backdrop, HugeSize, SheetFrames, LoopFps, true, false, false, None },
		{ TEXT("Umbra"), TEXT("VFX_Umbra"), EVfxFamily::Story, EVfxLayer::Hazard, LargeSize, SheetFrames, LoopFps, true, false, false, None },
	};
}

/** Plain lookups over the effect table. No world, no assets. */
namespace VfxCatalog
{
	UMBRELLAELLA_API TConstArrayView<FVfxArtRow> Rows();

	/** The row for an effect key, or nullptr. */
	UMBRELLAELLA_API const FVfxArtRow* Find(FName Key);

	/** Depth (Y) of a render layer, from the draw order. */
	UMBRELLAELLA_API float LayerY(EVfxLayer Layer);

	/** Seconds a one-shot effect lasts (frames / fps). */
	UMBRELLAELLA_API float Duration(const FVfxArtRow& Row);

	/** Frame shown after Elapsed seconds of game time: wraps for a loop, holds the last frame for a one-shot. */
	UMBRELLAELLA_API int32 FrameAt(const FVfxArtRow& Row, float Elapsed);

	/** True when a one-shot has shown its last frame. A loop never finishes by itself. */
	UMBRELLAELLA_API bool IsFinished(const FVfxArtRow& Row, float Elapsed);

	/** Effect key of a spell stage, or NAME_None when the spell has no such stage. */
	UMBRELLAELLA_API FName WeaponKey(EUmbrellaSpell Spell, EVfxWeaponStage Stage);

	/** Shown when a shot touches a protected part: the same for every spell, and never a damage look. */
	UMBRELLAELLA_API FName ProtectedContactKey();

	UMBRELLAELLA_API FLinearColor LightColour(const FVfxArtRow& Row);

	/** Content paths of the sheet texture: the passed art first, then the tracked placeholder. */
	UMBRELLAELLA_API TArray<FString> TexturePaths(const FVfxArtRow& Row);

	/** Distinct sheet names (the art pieces). */
	UMBRELLAELLA_API TArray<FName> Sheets();
}
