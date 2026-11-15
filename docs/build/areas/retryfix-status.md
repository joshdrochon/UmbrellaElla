# retryfix status

## Built
- `AUmbrellaPlayerController`: Retry in a world with a viewport reopens the map with `FFlowRules::RetryOption` ("UmbrellaRetry=<mode>.<count>");
  the new controller starts that mode at once, tutorial skipped, retry count kept. Test worlds keep the in-world reset.
- `UmbrellaElla.Flow.RetryReloadOptionNamesModeAndCount`.

## Measured
- Offscreen journey, Start Game, real input: click Retry and Enter each reach Playing in under 0.2 s at 3/3 lives, phase wings, after a
  fresh LoadMap (3 map loads in the run). Flow / Keeper / Encounter tests 93/93.
