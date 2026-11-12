#pragma once

#include "CoreMinimal.h"

/** True constants of the settings menu (not tuning). Slider and text range come from the GDD SH1.0 settings rules. */
namespace SettingsConstants
{
	/** Sound slider top, percent (manifest slider_max). */
	static constexpr int32 SliderMax = 100;
	static constexpr int32 SliderMin = 0;

	/** Default slider value. GDD default sound values are OPEN; full volume until a decision row sets them. */
	static constexpr int32 DefaultVolume = 100;

	/** Text scale range, percent (accessibility candidate: 100 to 200). */
	static constexpr int32 TextScaleMin = 100;
	static constexpr int32 TextScaleMax = 200;

	/** Fields in one saved binding line: action, key, scale. */
	static constexpr int32 BindingFieldCount = 3;
}

/** Look and layout of the settings widgets: dark charcoal and sepia with faint blue and small gold (GDD section 7). */
namespace SettingsLayout
{
	static constexpr float Padding = 16.0f;
	static constexpr float RowPadding = 6.0f;
	static constexpr float PanelWidth = 720.0f;
	static constexpr float LabelWidth = 220.0f;
	static constexpr float SliderWidth = 320.0f;
	static constexpr float ValueWidth = 56.0f;
	static constexpr float KeyButtonWidth = 150.0f;
	static constexpr int32 BodyFontSize = 18;
	static constexpr int32 TitleFontSize = 32;
	static constexpr float PanelDim = 0.04f;
	static constexpr float PanelAlpha = 0.94f;
	static constexpr float TextSepia[] = {0.86f, 0.78f, 0.62f};
	static constexpr float GoldAccent[] = {0.92f, 0.74f, 0.28f};
	static constexpr float WarnRed[] = {0.95f, 0.45f, 0.35f};
	static constexpr float SliderStep = 0.01f;
	static constexpr float TextScaleStep = 5.0f;
}
