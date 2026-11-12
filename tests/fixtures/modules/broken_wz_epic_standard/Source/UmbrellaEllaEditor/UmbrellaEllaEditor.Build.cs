using UnrealBuildTool;

public class UmbrellaEllaEditor : ModuleRules
{
	public UmbrellaEllaEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		IWYUSupport = IWYUSupport.Full;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
		PrivateDependencyModuleNames.AddRange(new string[] { "UmbrellaElla", "UnrealEd", "DataValidation" });
	}
}
