using UnrealBuildTool;

// Submission target: the workbench is compiled out (D-new-workbench-debug).
public class UmbrellaEllaTarget : TargetRules
{
	public UmbrellaEllaTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		ExtraModuleNames.Add("UmbrellaElla");
		ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=0");
		// The package script stamps the commit at build start; the smoke hook logs it (pipeline/unreal-rules.md Smoke hook)
		ProjectDefinitions.Add("UMBRELLAELLA_BUILD_COMMIT=\"" + (System.Environment.GetEnvironmentVariable("UMBRELLAELLA_BUILD_COMMIT") ?? "unknown") + "\"");
	}
}
