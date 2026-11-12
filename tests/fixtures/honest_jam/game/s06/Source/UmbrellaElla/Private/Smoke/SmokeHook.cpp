#include "Core/UmbrellaLog.h"
#include "Core/UmbrellaTuning.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"

// Card 0.6: -SmokeQuitAfter=15 logs one SMOKE_OK line per the contract in tools/ue_run.py, with input_vz the Z
// velocity measured while IA_Attack is held through Enhanced Input (GDD 1.3 ATTACK_DESCENT falls). At the first
// gameplay frame it logs SMOKE_EFFECTIVE: the compiled-in UMBRELLAELLA_BUILD_COMMIT and UMBRELLAELLA_WORKBENCH, the
// platform, and every reflected field of the UUmbrellaTuning structs and each harness flag (pipeline/unreal-rules.md, Smoke
// hook contract), at the first gameplay frame and again when the run ends.

namespace
{
	/** One SMOKE_EFFECTIVE line (tools/ue_run.py contract), read where gameplay reads: GetDefault<UUmbrellaTuning>()
	 *  and the harness flags. Reflection, so a card that marks a new `// bake:` key never edits this file. */
	void LogEffective(const UWorld* World, const TCHAR* At)
	{
		FString Line = FString::Printf(TEXT("SMOKE_EFFECTIVE %s commit=%s workbench=%d platform=%s"), At,
			TEXT(UMBRELLAELLA_BUILD_COMMIT), UMBRELLAELLA_WORKBENCH, *UGameplayStatics::GetPlatformName());
		const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
		for (TFieldIterator<FStructProperty> Member(UUmbrellaTuning::StaticClass()); Member; ++Member)
		{
			const void* Struct = Member->ContainerPtrToValuePtr<void>(Tuning);
			for (TFieldIterator<FProperty> Field(Member->Struct); Field; ++Field)
			{
				FString Value;
				Field->ExportTextItem_Direct(Value, Field->ContainerPtrToValuePtr<void>(Struct), nullptr, nullptr, PPF_None);
				Line += FString::Printf(TEXT(" %s.%s=%s"), *Member->Struct->GetName(), *Field->GetName(), *Value);
			}
		}
		if (const UHarnessSubsystem* Harness = UHarnessSubsystem::Get(World))
		{
			Line += FString::Printf(TEXT(" manifest=%s"), Harness->ManifestVersion());
			Harness->ForEachFlag([&Line, Harness](EFeatureId Id, const FString& Name)
			{
				Line += FString::Printf(TEXT(" %s.enabled=%d"), *Name, Harness->IsFeatureEnabled(Id) ? 1 : 0);
			});
		}
		UE_LOG(LogUmbrellaElla, Display, TEXT("%s"), *Line);
	}
}
// LogEffective(World, TEXT("at=start")) at the first gameplay frame; LogEffective(World, TEXT("at=end outcome=..."))
// at the Survived or fail screen, else just before the -SmokeQuitAfter quit (final-10 B H3).
