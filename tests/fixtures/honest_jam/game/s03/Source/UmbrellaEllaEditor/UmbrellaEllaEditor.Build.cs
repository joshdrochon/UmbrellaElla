using UnrealBuildTool;

public class UmbrellaEllaEditor : ModuleRules
{
	public UmbrellaEllaEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		IWYUSupport = IWYUSupport.Full;
		PrivateDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "UnrealEd", "UmbrellaElla" });
	}
}
