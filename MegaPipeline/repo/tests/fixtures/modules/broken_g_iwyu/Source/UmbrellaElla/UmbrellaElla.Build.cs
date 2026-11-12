using UnrealBuildTool;

public class UmbrellaElla : ModuleRules
{
	public UmbrellaElla(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "Paper2D" });
		PrivateDependencyModuleNames.AddRange(new string[] { "EnhancedInput", "DeveloperSettings" });
	}
}
