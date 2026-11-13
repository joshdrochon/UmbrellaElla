# artui2 requests
- artui (not mine): `Source/UmbrellaElla/Private/UI/Style/UmbrellaUIStyle.cpp:192` uses `UmbrellaUI::BodyLetterSpacing`, which
  does not exist, so area/artui does not compile (even at bccc77a6). Fix: use `UmbrellaUI::DisplayLetterSpacing` (one word) or add the constant.
  I patched it locally only, not committed.
- ui-journey-complete, ui-spell-wheel, ui-xp-ring are in-game widgets with no `-UIShots` shot; they need a smoke shot at the right moment (not in my lane's files).
