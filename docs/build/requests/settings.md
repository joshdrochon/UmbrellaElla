# Requests from settings

## 1. Apply saved bindings when Ella spawns (Core / move lane)
Remaps only reach the live input if something applies them after the adapter builds IMC_Default.
In `UEllaInputAdapterComponent::BindInput` (Input/EllaInputAdapterComponent.cpp), after `BuildInputAssets();` add:

    if (UGameInstance* GI = GetWorld() ? GetWorld()->GetGameInstance() : nullptr)
    {
        if (USettingsMenuSubsystem* Settings = GI->GetSubsystem<USettingsMenuSubsystem>())
        {
            USettingsMenuSubsystem::ApplyBindingsToContext(MappingContext, Settings->GetSession().GetSaved());
        }
    }

(include `Settings/SettingsMenuSubsystem.h`). Until then, saved bindings apply when the player presses Save in the
menu (`ApplySavedBindings`), and are lost for the next spawn after a restart of the game.

## 2. Tell the settings subsystem the play mode (flow)
Flow calls `USettingsMenuSubsystem::SetPlayMode(EUmbrellaPlayMode)` when a run starts (Start Game / Director's Cut).
Default is StartGame, so Game Options stays hidden if flow never calls it.
Flow's pause and title menus call `OpenSettings(PlayerController)`.

## 3. Sound classes (audio / feedback lane)
Sliders drive the engine's `/Engine/EngineSounds/Master`, `SFX` and `Music` sound classes (Master is their parent).
Sound cues/waves must be assigned to the SFX or Music class for those sliders to change them; Master affects all.

## 4. Tuning struct (Core)
No `FSettingsTuning` member exists in `UUmbrellaTuning`. Settings numbers are true constants in
`Settings/SettingsConstants.h` (slider 0 to 100 from the GDD, text 100 to 200%), so none is needed unless defaults
(GDD says default sound values are OPEN) should be tunable.

## 5. Input actions are runtime objects, not player-mappable assets
IA_* actions are built in C++ by the adapter, so there are no `.uasset` actions to mark player-mappable. Settings
rebuilds the keys of the live context itself (`ApplyBindingsToContext`) and persists them in
`Saved/SaveGames/UmbrellaSettings.ini`, so `UEnhancedInputUserSettings` is not used. No change requested.
