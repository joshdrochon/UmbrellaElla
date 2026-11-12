using UnrealBuildTool;

public class UmbrellaElla : ModuleRules
{
	public UmbrellaElla(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		IWYUSupport = IWYUSupport.Full;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
		PrivateDependencyModuleNames.AddRange(new string[] { "Paper2D", "EnhancedInput", "DeveloperSettings" });
	}
}
