#include "Settings/UmbrellaAccessibility.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Settings/SettingsConstants.h"
#include "Settings/SettingsLiveTuning.h"
#include "Settings/SettingsMenuSubsystem.h"

namespace
{
	const USettingsMenuSubsystem* FindAccessibilitySettings(const UObject* WorldContext)
	{
		const UWorld* World = (WorldContext && GEngine) ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
		const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
		return GameInstance ? GameInstance->GetSubsystem<USettingsMenuSubsystem>() : nullptr;
	}
}

namespace
{
	int32 PublishedPercent = SettingsConstants::TextScaleMin;
	bool bPublishedMotion = false;
}

void UmbrellaAccessibility::PublishSaved(int32 TextPercent, bool bReducedMotion, bool bReducedFlash)
{
	PublishedPercent = FMath::Clamp(TextPercent, SettingsConstants::TextScaleMin, SettingsConstants::TextScaleMax);
	bPublishedMotion = bReducedMotion;
}

void UmbrellaAccessibility::ResetPublished()
{
	PublishedPercent = SettingsConstants::TextScaleMin;
	bPublishedMotion = false;
}

int32 UmbrellaAccessibility::PublishedTextScalePercent()
{
	return IsFeatureEnabled(EFeatureId::FLOW_45) ? PublishedPercent : SettingsConstants::TextScaleMin;
}

float UmbrellaAccessibility::PublishedTextScale()
{
	return TextScaleFromPercent(PublishedTextScalePercent());
}

bool UmbrellaAccessibility::PublishedReducedMotion()
{
	return IsFeatureEnabled(EFeatureId::FLOW_45) && bPublishedMotion;
}

int32 UmbrellaAccessibility::PublishedFontSize(int32 BaseSize)
{
	return ScaledFontSize(BaseSize, PublishedTextScalePercent());
}

int32 UmbrellaAccessibility::GetTextScalePercent(const UObject* WorldContext)
{
	const USettingsMenuSubsystem* Settings = FindAccessibilitySettings(WorldContext);
	if (!Settings || !IsFeatureEnabled(EFeatureId::FLOW_45))
	{
		return SettingsConstants::TextScaleMin;
	}
	return Settings->GetSavedTextScalePercent();
}

float UmbrellaAccessibility::GetTextScale(const UObject* WorldContext)
{
	return TextScaleFromPercent(GetTextScalePercent(WorldContext));
}

bool UmbrellaAccessibility::IsReducedMotion(const UObject* WorldContext)
{
	const USettingsMenuSubsystem* Settings = FindAccessibilitySettings(WorldContext);
	return Settings && IsFeatureEnabled(EFeatureId::FLOW_45) && Settings->IsReducedMotionSaved();
}

bool UmbrellaAccessibility::IsReducedFlash(const UObject* WorldContext)
{
	const USettingsMenuSubsystem* Settings = FindAccessibilitySettings(WorldContext);
	return Settings && IsFeatureEnabled(EFeatureId::FLOW_45) && Settings->IsReducedFlashSaved();
}

float UmbrellaAccessibility::GetShakeScale(const UObject* WorldContext)
{
	return ShakeScaleFor(IsReducedMotion(WorldContext));
}

float UmbrellaAccessibility::TextScaleFromPercent(int32 Percent)
{
	const int32 Clamped = FMath::Clamp(Percent, SettingsConstants::TextScaleMin, SettingsConstants::TextScaleMax);
	return static_cast<float>(Clamped) / static_cast<float>(SettingsConstants::TextScaleMin);
}

int32 UmbrellaAccessibility::ScaledFontSize(int32 BaseSize, int32 Percent)
{
	return FMath::RoundToInt(static_cast<float>(BaseSize) * TextScaleFromPercent(Percent));
}

float UmbrellaAccessibility::ShakeScaleFor(bool bReducedMotion)
{
	return bReducedMotion ? 0.0f : 1.0f;
}
