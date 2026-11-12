#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaPlayMode.h"
#include "Settings/SettingsResult.h"
#include "Input/UmbrellaInputBindings.h"

/** The settings pages. GameOptions is the developer menu and exists only in Director's Cut. */
enum class ESettingsPage : uint8
{
	Sound,
	Controller,
	Credits,
	GameOptions
};

/** What Back does: close at once, or ask Save / Discard / Keep Editing because the page has unsaved changes. */
enum class ESettingsBackResult : uint8
{
	Close,
	AskSaveDiscardKeep
};

/** After a Back answer: close the menu or keep it open. */
enum class ESettingsBackOutcome : uint8
{
	CloseMenu,
	StayOpen
};

/** The player's answer to the dirty Back prompt. */
enum class ESettingsBackChoice : uint8
{
	Save,
	Discard,
	KeepEditing
};

/** Everything a player can change and Save persists. Earned progression is never in here (earned progression is independent). */
struct UMBRELLAELLA_API FUmbrellaSettingsData
{
	int32 MasterVolume = 0;
	int32 SfxVolume = 0;
	int32 MusicVolume = 0;
	int32 TextScalePercent = 0;
	bool bReducedMotion = false;
	/** Accessibility: shrink flashing effects . */
	bool bReducedFlash = false;
	TArray<FUmbrellaDefaultBinding> Bindings;

	bool operator==(const FUmbrellaSettingsData& Other) const;
};

/** One credits line: a name and a role (empty role = OPEN in the GDD). */
struct UMBRELLAELLA_API FSettingsCreditLine
{
	FString Name;
	FString Role;
};

/** Plain rule functions: no world, no widgets. Tests call these directly. */
namespace SettingsRules
{
	/** The shipped defaults: full volume, 100% text, the default bindings. */
	UMBRELLAELLA_API FUmbrellaSettingsData MakeDefaults();

	/** Clamp a slider value to 0..slider max. */
	UMBRELLAELLA_API int32 ClampVolume(int32 Value);

	/** Clamp text scale to the accessibility range. */
	UMBRELLAELLA_API int32 ClampTextScale(int32 Percent);

	/** Slider value (0..max) to the 0..1 sound class volume. */
	UMBRELLAELLA_API float VolumeToClassScale(int32 Value);

	/** Player settings (Sound, Controller, Credits) are in both modes; Game Options only in Director's Cut. */
	UMBRELLAELLA_API bool IsPageAvailable(ESettingsPage Page, EUmbrellaPlayMode Mode);

	/** The pages shown in the settings menu for a mode, in display order. */
	UMBRELLAELLA_API TArray<ESettingsPage> GetPages(EUmbrellaPlayMode Mode);

	/** Developer Game Options candidates (names only); empty in Start Game. */
	UMBRELLAELLA_API TArray<FName> GetDeveloperOptionNames(EUmbrellaPlayMode Mode);

	/** The credits shown on the Credits page. */
	UMBRELLAELLA_API TArray<FSettingsCreditLine> GetCredits();

	/** The Nth binding entry (in list order) of an action, or INDEX_NONE. */
	UMBRELLAELLA_API int32 FindBindingIndex(const TArray<FUmbrellaDefaultBinding>& Bindings, EUmbrellaInputAction Action, int32 Slot);

	/** How many binding entries an action has. */
	UMBRELLAELLA_API int32 CountBindings(const TArray<FUmbrellaDefaultBinding>& Bindings, EUmbrellaInputAction Action);

	/** Shoot and Absorb share a key: the four flight modes become impossible (accessibility recovery path). */
	UMBRELLAELLA_API bool HasShootAbsorbConflict(const TArray<FUmbrellaDefaultBinding>& Bindings);

	/** Short key label for instructions, e.g. "J" or "Left Mouse Button". */
	UMBRELLAELLA_API FString KeyLabel(const FKey& Key);

	/** First key bound to an action (keyboard and mouse before gamepad), as a label; empty when unbound. */
	UMBRELLAELLA_API FString FirstKeyLabel(const TArray<FUmbrellaDefaultBinding>& Bindings, EUmbrellaInputAction Action);

	/** Display name of an action ("Shoot", "Dash back"). */
	UMBRELLAELLA_API FText ActionDisplayName(EUmbrellaInputAction Action);
}

/**
 * A draft of the settings over the last saved copy. Edit the draft, Save commits it, Discard drops it.
 * Reset operations touch settings and bindings only; earned progression is never reachable from here.
 */
class UMBRELLAELLA_API FSettingsSession
{
public:
	FSettingsSession();
	explicit FSettingsSession(const FUmbrellaSettingsData& Saved);

	const FUmbrellaSettingsData& GetDraft() const { return Draft; }
	const FUmbrellaSettingsData& GetSaved() const { return Saved; }

	bool IsDirty() const;

	/** Unsaved changes on one page only (Sound page: volumes and accessibility; Controller page: bindings). */
	bool IsPageDirty(ESettingsPage Page) const;

	void SetMasterVolume(int32 Value);
	void SetSfxVolume(int32 Value);
	void SetMusicVolume(int32 Value);
	void SetTextScalePercent(int32 Percent);
	void SetReducedMotion(bool bEnabled);
	void SetReducedFlash(bool bEnabled);

	/** True when the Slot-th binding entry of Action exists and Key is a valid key. */
	bool CanRemap(EUmbrellaInputAction Action, int32 Slot, const FKey& NewKey) const;

	/** Replace the key of the Slot-th binding entry of Action; does nothing when CanRemap is false. */
	void Remap(EUmbrellaInputAction Action, int32 Slot, const FKey& NewKey);

	/** Back to the shipped default bindings and sliders in the draft (not saved until Save). */
	void ResetToDefaults();

	/** Back to the shipped default bindings only. */
	void ResetBindings();

	/** Commit the whole draft. */
	void Save();

	/** Drop all unsaved changes. */
	void Discard();

	/** Save applies the current page only; other pages' drafts stay as they are. */
	void SavePage(ESettingsPage Page);
	void DiscardPage(ESettingsPage Page);

	/** What Back does right now on this page. */
	ESettingsBackResult RequestBack(ESettingsPage Page) const;

	/** Apply the player's answer to the dirty prompt. */
	ESettingsBackOutcome ResolveBack(ESettingsPage Page, ESettingsBackChoice Choice);

private:
	FUmbrellaSettingsData Saved;
	FUmbrellaSettingsData Draft;
};
