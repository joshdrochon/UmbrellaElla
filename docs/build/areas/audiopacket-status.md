# audiopacket status

Done (check defect from sndtele: the blind critic packet now names the event and kind).
- Merged area/sndworld (8cd7f7b loop-range fix included).
- tools/audio_loop.py: `event_text` puts the sound-list event into the packet with no sound id, CamelCase name,
  rule id or scope note; `kind_of` gives one-shot / loop / music stem (stem = style.json music.stems); `KIND_NOTE` says
  how each kind plays. Loops and stems still get no attack_ms / decay_s ranges or numbers.
- tools/audio_critic_prompt.md: `{event}` slot, A5 points at the named event; version audio-critic/3.
- Tests (tests/test_audio_loop.py, 16 OK): test_packet_names_its_event_and_kind,
  test_event_text_is_blind_for_every_sound_list_row, test_known_bad_takes_still_fail, plus the sndworld loop test.

Open: pipeline_check flags docs/build/areas/audiopacket.md line 2 (docs/build/requests/sndtele.md exists only on
area/sndtele). That file is the build lead's brief, not this lane.
