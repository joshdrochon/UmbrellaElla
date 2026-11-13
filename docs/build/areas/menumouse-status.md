
## Keys after a click (Nov 13)
SFlowMenu now keeps focus itself: an active timer retakes focus onto the selected row whenever focus is on nothing or the game viewport, and Up/Down (arrows, W/S, D-pad, stick) move the selection inside OnKeyDown, so they work whatever holds focus. Covers Start, Pause, Settings stub, Defeated, Level-up. Not covered (other lanes' widgets): the full settings page and Journey Complete. Test: UmbrellaElla.Flow.MenuMouse.EmptyClickKeepsSelectionAndKeys (Flow suite 36/36 pass). Not tested: a real click in the window on Josh's Mac.
