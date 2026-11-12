# Requests from the level area
1. Flow (`Flow/UmbrellaPlayerController` or the Director's Cut mode start): spawn `AUmbrellaLevelDirector` once, call `BuildRoute(Seed)`
   and, on retry, `PlaceAtCheckpoint(Ella, LastCheckpoint)`. Nothing spawns it yet, so the route is not in the map until flow does.
2. The package script should append `asset_manifest=<id>` to BUILD_INFO.txt (`tools/ue_run.py build_info`); `FBuildIdentity` reads it, "unknown" until then.
