using UnrealBuildTool;

public class UmbrellaElla : ModuleRules
{
	public UmbrellaElla(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "Paper2D", "DeveloperSettings", "UMG", "Slate", "SlateCore" });
		IWYUSupport = IWYUSupport.Full;
	}
}
