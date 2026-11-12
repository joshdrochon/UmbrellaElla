#!/usr/bin/env bash
# The daily integration build as one graph (Mac): clean-tree, build (non-unity: -DisableUnity -NoPCH -NoSharedPCH,
# same as NONUNITY=1 tools/ue/build.sh), test, alone, validate, package,
# smoke every map, display runs, client-test, shipping-alive, then the tester package (workbench) (steps: tools/ue/daily-checklist.md). Stops at the first failing step, so a commit whose tests failed is never
# packaged or smoked. Prints one record line and appends it to Saved/Logs/pipeline/daily-records.txt.
# Usage: tools/ue/daily.sh [--allow-dirty]. Env: SMOKE_EXE, SMOKE_DISPLAY_MODES, RULE_MAX_SECONDS (1.0),
# CLIENT_TESTS=1 (packaged-client automation run), SMOKE_RESTART_CYCLES=5,
# SMOKE_REQUIRE_INPUT (1), SMOKE_DESKTOP_RES (WxH; else read from the OS), SHIPPING_EXE (step shipping-alive, on a Shipping
# package, only if D-new-smoke picks it), ALONE_NEW (1), COOK_WARN_DECISION=<decision id> (accepts a cook
# warning rise), SMOKE_MAX_LOAD_MS (10000). Each check left off is listed in "Not checked".
# Steps and record format: tools/ue_run.py `daily`. Merge coverage: tools/ue_run.py merge-check --since <ref>.
source "$(dirname "$0")/common.sh"
"${UE_RUN[@]}" daily --shell sh "$@"
