# Check defect: the audio critic packet. Branch area/audiopacket. Read docs/build/worker-rules.md first.
Triage verdict (build lead): check defect, evidence in the sndtele lane request file on area/sndtele (its requests file, item 1). The blind packet
(tools/audio_loop.py write_packet / cmd_round) gives the family target but never says which event the sound is for or
whether it is a loop, so question A5 cannot be answered (critics guessed between Bolt, Gust and Arc); and it prints
one-shot ranges (attack_ms, decay_s) for loops. sndworld already fixed the loop ranges on area/sndworld (8cd7f7b):
merge that branch first (git merge area/sndworld), then:
1. Put the sound's own event text and kind (one-shot / loop / music stem) from pipeline/audio/sound-list.csv into the
   packet, without the sound id or anything that reveals it is ours.
2. Tests: a packet for a loop has no one-shot ranges; a packet names its event; a known-bad take still fails the critic
   (the bar is not loosened).
Lane: tools/audio_loop.py, tools/audio_critic_prompt.md (only if the prompt must name the new fields; bump its version),
tests/test_audio_loop*.py. Done: tests OK; tell nothing else.
