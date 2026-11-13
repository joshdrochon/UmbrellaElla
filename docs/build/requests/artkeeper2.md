# artkeeper2 request (Nov 13)
In the -SmokeKeeper capture (Saved/Logs/pipeline/keeper-owl-shot.png, 1280x720) a flat lilac cube (StandInKeeperColor) is drawn over the Keeper art slot
(T_Keeper_Owl_PH holds the R10 owl; it shows only above and below the block). Source: `KeeperPresenterSubsystem::ShowStandIn` and/or the
`AKeeperOfTime::MakeVisual` cubes keep a flat-colour cube visible when the slot has art. Ask (Feedback/Anim + Owl lanes): hide the cube
when `ArtSlot::HasArt` is true, and show only the textured quad. Until then every in-game `context` pair fails on a lilac block, not on our art.
