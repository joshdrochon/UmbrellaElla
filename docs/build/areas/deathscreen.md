# Area: deathscreen

Started by the build lead from Josh's request (2026-11-13 22:40). It is the definition of done.

The death (Defeated) screen shows the in-game backdrop (the paused game scene: the T_Bg*_PH layers), never the title
picture. The title screen and the credits keep the title picture unchanged. Death text and buttons stay readable.
A test fails if the death screen uses the title picture (UmbrellaElla.UI.DeathScreenNotTitlePicture).
Proof: pipeline/art/proof/deathscreen (1280x720 offscreen, before/after, title after).
