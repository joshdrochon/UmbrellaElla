using UnrealBuildTool;

public class UmbrellaEllaEditorTarget : TargetRules
{
	public UmbrellaEllaEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		ExtraModuleNames.Add("UmbrellaElla");
		ExtraModuleNames.Add("UmbrellaEllaEditor");
		ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=1");
		// The package script stamps the commit at build start; the smoke hook logs it (pipeline/unreal-rules.md Smoke hook)
		ProjectDefinitions.Add("UMBRELLAELLA_BUILD_COMMIT=\"" + (System.Environment.GetEnvironmentVariable("UMBRELLAELLA_BUILD_COMMIT") ?? "unknown") + "\"");
	}
}
