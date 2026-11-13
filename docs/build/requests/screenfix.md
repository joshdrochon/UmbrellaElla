
## Main does not compile: SettingsMenuWidget.cpp include order (Nov 13, after main e99e1856 + storyinventory)
- `Source/UmbrellaElla/Private/UI/Settings/SettingsMenuWidget.cpp(1): error: Expected SettingsMenuWidget.h to be first header included.`
- Fix (UI lane): move `#include "UI/Settings/SettingsMenuWidget.h"` to line 1. screenfix builds with that local, uncommitted change and reverts it.
