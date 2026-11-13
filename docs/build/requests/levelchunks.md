# Requests from the levelchunks area

1. Core (`Core/UmbrellaGameMode.cpp`, `BeginRoute`): a new run places Ella with `PlaceAtCheckpoint(Pawn, 1)`, which is
   refuge CP1 after slot 3, so the run skips group A (CH01-CH03). Change: `LevelDirector->PlaceAtCheckpoint(Player->GetPawn(), 0);`
   (CP0 = the route start at interface N; levelchunks adds it). Retry keeps `max(1, GetCheckpointReached())` unchanged.
   Why: HAZ-37 group A and the tutorial-first order are never played otherwise.
2. Playtest (`Smoke/PlaytestRun.cpp`, `MeasureFlow28`): the threat count is taken right after `BuildRoute`, before the
   handoff, so it counts the live route enemies the handoff then clears. Count `AUmbrellaEnemy` after
   `StepFollow(KeeperHandoffX(), 1)` (or read `AUmbrellaLevelDirector::GetThreatsRemaining()`), which is what FLOW-28 asks.
