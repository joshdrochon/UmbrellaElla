
## Main does not compile: SettingsMenuWidget.cpp include order (Nov 13, after main e99e1856 + storyinventory)
- `Source/UmbrellaElla/Private/UI/Settings/SettingsMenuWidget.cpp(1): error: Expected SettingsMenuWidget.h to be first header included.`
- Fix (UI lane): move `#include "UI/Settings/SettingsMenuWidget.h"` to line 1. screenfix builds with that local, uncommitted change and reverts it.

## affected_tests.py is too slow (Nov 13, owner of tools/affected_tests.py)
- `python3 tools/affected_tests.py --base origin/main` takes over 10 min just to list tests on this machine (AGENTS.md target: 5 min for the run).
- Also `python3 -m unittest tests.test_gdd_check tests.test_area` alone takes over 4 min here.
- Ask: cache the changed-file to test map, or skip the full-history diff when `--base` is given.
