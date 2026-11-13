# Check defect: audio critic spectrograms. Branch area/spectro. Read docs/build/worker-rules.md first.
Triage verdict (build lead): check defect, evidence in sndlaunch's requests file item 1a (area/sndlaunch). The critic
packet's spectrogram (tools/audio_style_check.py `spectrogram_png`) uses one 1024-sample FFT (47 Hz bins) for every row,
so rows under about 500 Hz hold 1-2 bins and a reverb tail draws column stripes there; critics read them as "evenly
spaced gear ticks". The approved references show the same stripes. Fix: a second grid with a 4096-sample window for rows
whose lower edge is under 500 Hz, windows centred on their column, bins starting at 1 (row 0 reads the DC bin today).
Tests: the same WAV drawn with the new code has no low-band stripes; a real tick train still shows its ticks; existing
audio_style_check tests pass. Lane: tools/audio_style_check.py, tests/test_audio_style*.py. Done: tests OK; commit, stop.
