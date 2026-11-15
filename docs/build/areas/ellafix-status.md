# ellafix status

## Done
1. EllaAnimPresenterComponent::TickComponent: Down returns to Idle once her health is back (IsAliveAgain). Test
   UmbrellaElla.Feedback.World.EllaDownOnlyWhileDefeated. UmbrellaElla.Feedback PASS 69/69; build 0 warnings; module_check 0.
2. -SmokeDown smoke flag. Offscreen 1280x720 frames: Idle tex=T_Ella_Idle_PH, Hurt tex=T_Ella_Hurt_PH (umbrella in hand),
   Down then alive tex=T_Ella_Idle_PH.

## Left
- The Down art itself (ella-down stand-in, not passed) ends with the umbrella set down; right only on the defeat screen. Art call.
- visual_qa captures only idle and hurt; a per-state capture judged against the approved idle is not built yet.
