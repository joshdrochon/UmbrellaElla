using UnrealBuildTool;
using System.Collections.Generic;

public class UmbrellaEllaEditorTarget : TargetRules
{
	public UmbrellaEllaEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.AddRange(new string[] { "UmbrellaElla", "UmbrellaEllaEditor" });
		ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=1");
		ProjectDefinitions.Add("UMBRELLAELLA_BUILD_COMMIT=\"" + (System.Environment.GetEnvironmentVariable("UMBRELLAELLA_BUILD_COMMIT") ?? "unknown") + "\"");
	}
}
