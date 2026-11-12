using UnrealBuildTool;
using System.Collections.Generic;

public class UmbrellaEllaWorkbenchTarget : TargetRules
{
	public UmbrellaEllaWorkbenchTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.AddRange(new string[] { "UmbrellaElla" });
		ProjectDefinitions.Add("UMBRELLAELLA_WORKBENCH=1");
		ProjectDefinitions.Add("UMBRELLAELLA_BUILD_COMMIT=\"" + (System.Environment.GetEnvironmentVariable("UMBRELLAELLA_BUILD_COMMIT") ?? "unknown") + "\"");
	}
}
