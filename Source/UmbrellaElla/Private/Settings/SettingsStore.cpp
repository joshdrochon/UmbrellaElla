#include "Settings/SettingsStore.h"
#include "HAL/FileManager.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"
#include "Settings/SettingsConstants.h"
#include "Settings/SettingsModel.h"

namespace
{
	const TCHAR* const SoundSection = TEXT("Sound");
	const TCHAR* const AccessSection = TEXT("Accessibility");
	const TCHAR* const BindingSection = TEXT("Bindings");
	const TCHAR* const BindingSeparator = TEXT("|");

	FString EncodeBinding(const FUmbrellaDefaultBinding& Binding)
	{
		return FString::Printf(TEXT("%s|%s|%g"), *UmbrellaInputBindings::ActionName(Binding.Action).ToString(), *Binding.Key.ToString(), Binding.Scale);
	}

	bool DecodeBinding(const FString& Text, FUmbrellaDefaultBinding& Out)
	{
		TArray<FString> Fields;
		Text.ParseIntoArray(Fields, BindingSeparator);
		if (Fields.Num() != SettingsConstants::BindingFieldCount)
		{
			return false;
		}
		bool bFound = false;
		for (int32 Index = 0; Index < static_cast<int32>(EUmbrellaInputAction::Count); ++Index)
		{
			const EUmbrellaInputAction Action = static_cast<EUmbrellaInputAction>(Index);
			if (UmbrellaInputBindings::ActionName(Action).ToString() == Fields[0])
			{
				Out.Action = Action;
				bFound = true;
				break;
			}
		}
		const FKey Key(*Fields[1]);
		if (!bFound || !Key.IsValid())
		{
			return false;
		}
		Out.Key = Key;
		Out.Scale = FCString::Atof(*Fields[2]);
		return true;
	}

	int32 ReadInt(const FConfigFile& File, const TCHAR* Section, const TCHAR* Key, int32 Fallback)
	{
		int32 Value = Fallback;
		File.GetInt(Section, Key, Value);
		return Value;
	}
}

FString SettingsStore::GetDefaultPath()
{
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("SaveGames"), TEXT("UmbrellaSettings.ini"));
}

ESettingsResult SettingsStore::Write(const FString& Path, const FUmbrellaSettingsData& Data)
{
	FConfigFile File;
	File.SetInt64(SoundSection, TEXT("Master"), Data.MasterVolume);
	File.SetInt64(SoundSection, TEXT("Sfx"), Data.SfxVolume);
	File.SetInt64(SoundSection, TEXT("Music"), Data.MusicVolume);
	File.SetInt64(AccessSection, TEXT("TextScale"), Data.TextScalePercent);
	File.SetInt64(AccessSection, TEXT("ReducedMotion"), Data.bReducedMotion ? 1 : 0);
	FConfigSection& Section = File.Add(BindingSection, FConfigSection());
	for (const FUmbrellaDefaultBinding& Binding : Data.Bindings)
	{
		Section.Add(FName(TEXT("Binding")), FConfigValue(EncodeBinding(Binding)));
	}
	IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path), true);
	return File.Write(Path) ? ESettingsResult::Ok : ESettingsResult::Failed;
}

ESettingsResult SettingsStore::Read(const FString& Path, FUmbrellaSettingsData& Data)
{
	Data = SettingsRules::MakeDefaults();
	if (!IFileManager::Get().FileExists(*Path))
	{
		return ESettingsResult::Failed;
	}
	FConfigFile File;
	File.Read(Path);
	Data.MasterVolume = SettingsRules::ClampVolume(ReadInt(File, SoundSection, TEXT("Master"), Data.MasterVolume));
	Data.SfxVolume = SettingsRules::ClampVolume(ReadInt(File, SoundSection, TEXT("Sfx"), Data.SfxVolume));
	Data.MusicVolume = SettingsRules::ClampVolume(ReadInt(File, SoundSection, TEXT("Music"), Data.MusicVolume));
	Data.TextScalePercent = SettingsRules::ClampTextScale(ReadInt(File, AccessSection, TEXT("TextScale"), Data.TextScalePercent));
	Data.bReducedMotion = ReadInt(File, AccessSection, TEXT("ReducedMotion"), 0) != 0;

	TArray<FString> Encoded;
	File.GetArray(BindingSection, TEXT("Binding"), Encoded);
	if (Encoded.Num() > 0)
	{
		TArray<FUmbrellaDefaultBinding> Loaded;
		for (const FString& Text : Encoded)
		{
			FUmbrellaDefaultBinding Binding;
			if (DecodeBinding(Text, Binding))
			{
				Loaded.Add(Binding);
			}
		}
		// A saved file with a different binding count (an older build) falls back to defaults rather than half-applying.
		if (Loaded.Num() == Data.Bindings.Num())
		{
			Data.Bindings = Loaded;
		}
	}
	return ESettingsResult::Ok;
}

void SettingsStore::Delete(const FString& Path)
{
	IFileManager::Get().Delete(*Path, false, true, true);
}
