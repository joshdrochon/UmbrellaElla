# Follow-up: settings. Branch area/fixsettings. Read docs/build/worker-rules.md first.
(1) Settings calls visuals' `SetReducedFlash` (docs/build/requests/visuals.md) from the reduced-flash/accessibility
option, on Save and at startup from the saved value; test. (2) Test that a saved key binding reaches the live
IMC_Default after respawn (move applies them in UEllaInputAdapterComponent::BindInput; build a game instance in the test
so the subsystem lookup is covered). (3) Minor items from ../UmbrellaElla-areas/logs/review-settings.txt in Settings/**.
Lane: Settings/**, UI/Settings/**, Tests/Settings/**. Done: worker-rules DoD.
