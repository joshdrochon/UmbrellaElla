#include "Feedback/Vfx/VfxCatalog.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Harness/UmbrellaFeatureFlags.h"
TConstArrayView<FVfxArtRow> VfxCatalog::Rows()
{
	return MakeArrayView(VfxCatalogData::Rows);
}

const FVfxArtRow* VfxCatalog::Find(FName Key)
{
	for (const FVfxArtRow& Row : VfxCatalogData::Rows)
	{
		if (Key == FName(Row.Key))
		{
			return &Row;
		}
	}
	return nullptr;
}

float VfxCatalog::LayerY(EVfxLayer Layer)
{
	switch (Layer)
	{
	case EVfxLayer::Hazard:
		return UmbrellaDrawOrder::HazardY;
	case EVfxLayer::Foreground:
		return UmbrellaDrawOrder::ForegroundY;
	case EVfxLayer::Backdrop:
		return UmbrellaDrawOrder::BackgroundNearY;
	case EVfxLayer::Vfx:
	default:
		return UmbrellaDrawOrder::VfxY;
	}
}

float VfxCatalog::Duration(const FVfxArtRow& Row)
{
	return Row.Fps > 0.0f ? static_cast<float>(Row.Frames) / Row.Fps : 0.0f;
}

int32 VfxCatalog::FrameAt(const FVfxArtRow& Row, float Elapsed)
{
	if (Row.Frames <= 1 || Row.Fps <= 0.0f)
	{
		return 0;
	}
	const int32 Raw = FMath::FloorToInt32(FMath::Max(Elapsed, 0.0f) * Row.Fps);
	return Row.bLoop ? Raw % Row.Frames : FMath::Min(Raw, Row.Frames - 1);
}

int32 VfxCatalog::FrameAt(const FVfxArtRow& Row, float Elapsed, bool bReducedMotion)
{
	// Reduced motion: a looping effect holds one still frame; one-shots still play, they are short feedback.
	return (bReducedMotion && Row.bLoop && IsFeatureEnabled(EFeatureId::VFX_10)) ? 0 : FrameAt(Row, Elapsed);
}

bool VfxCatalog::IsFinished(const FVfxArtRow& Row, float Elapsed)
{
	return !Row.bLoop && Elapsed >= Duration(Row);
}

FName VfxCatalog::WeaponKey(EUmbrellaSpell Spell, EVfxWeaponStage Stage)
{
	switch (Spell)
	{
	case EUmbrellaSpell::SmallBlasts:
		switch (Stage)
		{
		case EVfxWeaponStage::Release: return TEXT("SmallBlastRelease");
		case EVfxWeaponStage::Travel: return TEXT("SmallBlastTravel");
		case EVfxWeaponStage::Impact: return TEXT("SmallBlastImpact");
		case EVfxWeaponStage::Fade: return TEXT("SmallBlastFade");
		default: return NAME_None;
		}
	case EUmbrellaSpell::StreamedBlast:
		switch (Stage)
		{
		case EVfxWeaponStage::Release: return TEXT("StreamStartup");
		case EVfxWeaponStage::Sustain: return TEXT("StreamSustain");
		case EVfxWeaponStage::Impact: return TEXT("StreamContact");
		case EVfxWeaponStage::Fade: return TEXT("StreamStop");
		default: return NAME_None;
		}
	case EUmbrellaSpell::TwinStars:
		switch (Stage)
		{
		case EVfxWeaponStage::Release: return TEXT("TwinStarRelease");
		case EVfxWeaponStage::Travel: return TEXT("TwinStarHead");
		case EVfxWeaponStage::Impact: return TEXT("TwinStarImpact");
		case EVfxWeaponStage::Fade: return TEXT("TwinStarFade");
		default: return NAME_None;
		}
	case EUmbrellaSpell::Needle:
		switch (Stage)
		{
		case EVfxWeaponStage::Channel: return TEXT("NeedleChannel");
		case EVfxWeaponStage::Release: return TEXT("NeedlePulse");
		case EVfxWeaponStage::Travel: return TEXT("NeedleSliver");
		case EVfxWeaponStage::Pierce: return TEXT("NeedlePierce");
		case EVfxWeaponStage::Impact: return TEXT("NeedleImpact");
		case EVfxWeaponStage::Fade: return TEXT("NeedleFade");
		default: return NAME_None;
		}
	default:
		return NAME_None;
	}
}

FName VfxCatalog::ProtectedContactKey()
{
	return TEXT("ProtectedContact");
}

FLinearColor VfxCatalog::LightColour(const FVfxArtRow& Row)
{
	return FLinearColor(FColor::FromHex(FString::Printf(TEXT("%06X"), Row.LightHex)));
}

TArray<FString> VfxCatalog::TexturePaths(const FVfxArtRow& Row)
{
	const FString Folder = TEXT("/Game/UmbrellaElla/Art/VFX/");
	const FString Passed = FString::Printf(TEXT("T_%s"), Row.Sheet);
	const FString Placeholder = Passed + TEXT("_PH");
	return { Folder + Passed + TEXT(".") + Passed, Folder + Placeholder + TEXT(".") + Placeholder };
}

TArray<FName> VfxCatalog::Sheets()
{
	TArray<FName> Out;
	for (const FVfxArtRow& Row : VfxCatalogData::Rows)
	{
		Out.AddUnique(FName(Row.Sheet));
	}
	return Out;
}
