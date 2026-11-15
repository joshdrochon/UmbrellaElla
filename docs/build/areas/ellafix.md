# Area: ellafix

Goal (Josh, 14 Nov, Director's Cut screenshot): Ella drew upright with a closed umbrella set down beside her, not in hand.
Cause: the Down picture (ella-down defeat clip; its last cells show the umbrella closed beside her) had no hold time, so after a
checkpoint retry she kept it; since ellaanim it plays to that last cell.
Lane: Source/UmbrellaElla/{Public,Private}/Feedback/Anim/EllaAnimPresenterComponent.*, Smoke/SmokeHookSubsystem.* (-SmokeDown),
Tests/Feedback/EllaGridPlaybackTests.cpp.
Done when: alive (health back) Ella never keeps Down (UmbrellaElla.Feedback.World.EllaDownOnlyWhileDefeated), offscreen frames of
Idle, Hurt and Down-after-retry show the umbrella in hand, UmbrellaElla.Feedback PASS.
