#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaPlayMode.h"

struct FSettingsLiveTuning;

/**
 * The Director's Cut developer Game Options (the GDD candidates, in GDD order). Contents are OPEN in the GDD; this set is
 * the agent default in docs/decisions.md D-new-flow44-dev-options. No ammunition or energy controls.
 */
enum class EDeveloperOption : uint8
{
	EntryRetries,
	Movement,
	Hop,
	Dash,
	VoluntaryCurrents,
	HostileGusts,
	Missiles,
	Absorption,
	HealthGround,
	FourWeapons,
	ProgressionScarf,
	OwlParts,
	Clock,
	Stun,
	Slow,
	EyesBlackout,
	Tutorial,
	Remapping,
	SizeHitbox,
	Background,
	Count
};

/** How a developer option is shown and applied. */
enum class EDeveloperOptionKind : uint8
{
	/** Percent of the tuned value (100 = as tuned). */
	Percent,
	/** Whole-number change added to the tuned count (0 = as tuned). */
	Offset,
	/** On / off. */
	Toggle,
	/** Opens another settings page (no value of its own). */
	Link
};

/** Ranges of the developer options (true constants of the menu, not tuning). */
namespace DeveloperOptionLimits
{
	/** 100 percent = the tuned value. */
	static constexpr int32 PercentUnit = 100;
	static constexpr int32 PercentLow = 25;
	static constexpr int32 PercentHigh = 200;
	/** Percent options that can switch a hazard or effect off go down to 0. */
	static constexpr int32 PercentOffLow = 0;
	static constexpr int32 PercentStep = 5;
	static constexpr int32 OffsetLow = -2;
	static constexpr int32 OffsetHigh = 8;
	static constexpr int32 OffsetStep = 1;
	/** A count option never goes below one (one life, one hit). */
	static constexpr int32 CountFloor = 1;
	static constexpr int32 ToggleOff = 0;
	static constexpr int32 ToggleOn = 1;
	/** Unlock level every weapon gets when Four Weapons is on. */
	static constexpr int32 AllWeaponsUnlockLevel = 1;
}

/**
 * Release exposure of the developer options is OPEN in the GDD (D-new-flow44-release). Default: the controls change
 * values only in workbench builds (editor and the tester target, UMBRELLAELLA_WORKBENCH=1), as D-new-workbench-debug
 * decided for sliders; the submission build shows the page read-only. Flip this to true to ship them editable.
 */
namespace DeveloperOptionRelease
{
	static constexpr bool bEditableInSubmissionBuild = false;
}

/** One option: id, saved name, label, kind and range. */
struct UMBRELLAELLA_API FDeveloperOptionSpec
{
	EDeveloperOption Id = EDeveloperOption::Count;
	FName Name;
	FText Label;
	EDeveloperOptionKind Kind = EDeveloperOptionKind::Percent;
	int32 Low = 0;
	int32 High = 0;
	int32 Step = 1;
	int32 Default = 0;
};

/** Plain rule functions for the developer options. Tests call these directly. */
namespace DeveloperOptionRules
{
	/** Every option in GDD order (empty when the developer-options flag is off). */
	UMBRELLAELLA_API TArray<FDeveloperOptionSpec> AllSpecs();

	/** The spec of one option (Count id when unknown). */
	UMBRELLAELLA_API FDeveloperOptionSpec SpecFor(EDeveloperOption Option);

	/** One value per option, every one at its default ("as tuned"). */
	UMBRELLAELLA_API TArray<int32> MakeDefaultValues();

	/** Clamp to the option's range and snap to its step. */
	UMBRELLAELLA_API int32 ClampValue(EDeveloperOption Option, int32 Value);

	/** True when every value is its default (nothing to apply). Missing values count as defaults. */
	UMBRELLAELLA_API bool IsAllDefault(const TArray<int32>& Values);

	/** The value of one option in a value list, or its default when the list is short. */
	UMBRELLAELLA_API int32 ValueOf(const TArray<int32>& Values, EDeveloperOption Option);

	/** True in builds compiled with the tester workbench (editor and the tester target). */
	UMBRELLAELLA_API bool IsWorkbenchBuild();

	/** The options change values only in Director's Cut, and only where the release rule allows it. */
	UMBRELLAELLA_API bool CanEdit(EUmbrellaPlayMode Mode, bool bWorkbenchBuild);

	/** Write the options onto a tuning copy taken from the baseline. Defaults leave it unchanged. */
	UMBRELLAELLA_API void Apply(const TArray<int32>& Values, FSettingsLiveTuning& Tuning);

	/** What the option makes of the baseline, for the page ("290 cm/s", "4 lives", "On"). */
	UMBRELLAELLA_API FText ValueText(EDeveloperOption Option, int32 Value, const FSettingsLiveTuning& Baseline);
}
