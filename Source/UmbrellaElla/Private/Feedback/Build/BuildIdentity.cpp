#include "Feedback/Build/BuildIdentity.h"
#include "Core/UmbrellaTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "HAL/PlatformProperties.h"
#include "Misc/App.h"
#include "Misc/EngineVersion.h"

FString FBuildIdentity::ToText() const
{
	return FString::Printf(TEXT("engine=%s\nconfig=%s\nplatform=%s\nunits_per_pixel=%.4f\ncamera_aspect=%.6f\npackaging=%s\nmanifest=%s"),
		*EngineVersion, *Configuration, *Platform, UnitsPerPixel, CameraAspectRatio, *Packaging, GetFeatureManifestVersion());
}

FBuildIdentity FBuildIdentity::Capture()
{
	FBuildIdentity Id;
	if (!IsFeatureEnabled(EFeatureId::CORE_06))
	{
		return Id;
	}
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	Id.EngineVersion = FEngineVersion::Current().ToString(EVersionComponent::Patch);
	Id.Configuration = LexToString(FApp::GetBuildConfiguration());
	Id.Platform = FPlatformProperties::IniPlatformName();
	Id.UnitsPerPixel = T.ArenaHeight / UmbrellaBuildConst::QualifiedOutputHeight;
	Id.CameraAspectRatio = T.CameraAspectRatio;
	Id.Packaging = FApp::IsGame() ? TEXT("game") : TEXT("editor");
	return Id;
}
