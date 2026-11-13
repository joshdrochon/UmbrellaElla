#include "Feedback/Build/BuildIdentity.h"
#include "Core/UmbrellaTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "HAL/PlatformProperties.h"
#include "Misc/App.h"
#include "Misc/EngineVersion.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

#ifndef UMBRELLAELLA_BUILD_COMMIT
#define UMBRELLAELLA_BUILD_COMMIT "unknown"
#endif

namespace
{
	const TCHAR* BuildIdentityBuildInfoFile = TEXT("BUILD_INFO.txt");
	const TCHAR* BuildIdentityUnknown = TEXT("unknown");
}

FString FBuildIdentity::ToText() const
{
	return FString::Printf(TEXT("engine=%s\nconfig=%s\nplatform=%s\nunits_per_pixel=%.4f\ncamera_aspect=%.6f\npackaging=%s\nmanifest=%s\nrevision=%s\nasset_manifest=%s"),
		*EngineVersion, *Configuration, *Platform, UnitsPerPixel, CameraAspectRatio, *Packaging, GetFeatureManifestVersion(), *Revision, *AssetManifest);
}

FString FBuildIdentity::ParseBuildInfoValue(const FString& Text, const FString& Key)
{
	TArray<FString> Lines;
	Text.ParseIntoArrayLines(Lines);
	const FString Prefix = Key + TEXT("=");
	for (const FString& Line : Lines)
	{
		if (Line.StartsWith(Prefix))
		{
			return Line.Mid(Prefix.Len()).TrimStartAndEnd();
		}
	}
	return FString();
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
	Id.Revision = ANSI_TO_TCHAR(UMBRELLAELLA_BUILD_COMMIT);
	Id.AssetManifest = BuildIdentityUnknown;
	FString Info;
	if (FFileHelper::LoadFileToString(Info, *FPaths::Combine(FPaths::LaunchDir(), BuildIdentityBuildInfoFile)))
	{
		const FString Value = ParseBuildInfoValue(Info, TEXT("asset_manifest"));
		if (!Value.IsEmpty())
		{
			Id.AssetManifest = Value;
		}
	}
	return Id;
}
