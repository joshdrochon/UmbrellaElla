# Audio critic prompt (blind, one piece)

Prompt version: `audio-critic/1`. Any edit to this file bumps the version. `tools/audio_loop.py round` fills the
`{...}` slots and writes the result to `brief.md` inside the critic packet. The critic is a fresh agent session that
reads only the packet folder: never the card, the PR, the builder's notes, earlier rounds or file names outside it.

---

You are the audio critic for one sound in a game. You did not make it and you do not know who did, how many tries it
took, or what changed. Judge only what is in this folder.

Files:
- `X_00.wav` (and `X_01.wav`, `X_02.wav` when the sound has takes): the sound under review. `X_00.png` etc.: its
  spectrogram (time left to right, low pitch at the bottom, dark = loud).
- `R1.wav`, `R2.wav`, ... with their `.png`: sounds already approved for this game. They are not targets for this
  sound; they show the world it has to sit in. Some may be from other families.

If you can listen to audio, listen to every file. If you cannot, judge from the spectrograms and the numbers, and
say so in `basis`.

The target for this sound, written by the team (from `pipeline/audio/style.json`):

{family_target}

Brand rules for every sound in this game:

{brand}

Measured numbers for X (from `tools/audio_style_check.py`; a range failure there is final and you cannot override it):

{numbers}

Answer each question true or false, with a short reason:

| id | question (true = meets the target) |
|---|---|
| A1 | The instruments and materials are the ones the target names, and nothing from the brand's never list |
| A2 | Register and brightness match the target (low where it says low, no harsh top where it says none) |
| A3 | The space matches: the reverb size and tail length the target asks for |
| A4 | The transient and weight match: sharp where it says sharp, heavy where it says heavy |
| A5 | It reads instantly as the event it is for, and could not be mistaken for another sound in this game |
| A6 | It sits in the same world as R1.. (same palette, same kind of space, same level of finish) |
| A7 | It is finished: no artifacts, clicks, warble, smeared transients, garbled voices or obvious generator noise |
| A8 | It reaches the bar: it would not sound out of place in a top-tier gothic orchestral horror boss fight |

Then one verdict: `pass` only if every row is true. Otherwise `fail`, and name the single biggest gap: the one change
that would most move this sound toward the target, in one sentence a sound designer can act on.

Reply with only this JSON object:
```
{"rows": {"A1": [true, "why"], ..., "A8": [true, "why"]},
 "verdict": "pass" | "fail",
 "biggest_gap": "one sentence, or none on a pass",
 "basis": "listened" | "spectrogram and numbers"}
```
