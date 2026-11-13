# Requests from the sndtele lane

## 1. Audio critic packet: name the sound's event and kind (check defect, not a looser bar)

File: `tools/audio_loop.py` (`write_packet`, `cmd_round`). Owner: build lead / audio lane.

Defect: the blind packet gives the critic the family target, which describes several different events of one family
("Bolt: ratchet into a click. Gust: a wing heave, air drawn in. Arc: a pendulum swoop"), but never says which event
the sound under review is for, or whether it is a loop. Question A5 ("reads instantly as the event it is for") cannot
be answered. The numbers block also prints `attack_ms` and `decay_s` for loops, with the family's one-shot ranges
beside them, although `tools/audio_style_check.py` does not apply those two to loops.

Evidence (card SNDTELE, stock packet, critic model claude-opus-5-5, style check PASS on every take):
| piece (round) | what the critic wrote |
|---|---|
| GustWindup (3) | "Without clear ratchet clicks speeding up, the wind-up could be taken for the Gust tell (air drawn in)." It is the gust tell. |
| CastWarning (1) | "if it is the Bolt, put audible ratchet clicks ...; if it is Gust or Arc, swap the ratchet tail for a wing-air intake or a lower pendulum swoop." |
| TalonWarning (2) | "Commit to a single tell: if this is the Arc, cut the double metal click ..." |
| RearMidpointClack (2) | "cut the ticking and tones that come after [the click]". The sound-list event is "the safe pause; must not sound finished". |
| UmbrellaFlap (1), a loop | "Measured decay_s=13.7 against an allowed 0.05..1.2. That range failure is final"; "attack_ms=1216 against an allowed 0..40"; asks for "one cloth-on-ribs event ... with silence after it". |
| EllaFallLoop (1), a loop | "decay_s is inf, so the sound never decays"; "attack_ms is 2868 against a 0-300 range"; asks for "near-silence between hits instead of a constant 3 s wash". |

Change (keeps the packet blind: no id, no history, no notes):

    --- a/tools/audio_loop.py
    +++ b/tools/audio_loop.py
    @@ def write_packet
    -def write_packet(rdir, files, near, results, fam, style):
    +def write_packet(rdir, files, near, results, fam, style, row=None):
    @@
    -        nums.append(f"{name}: " + asc.summary(m, sorted(k for k in m if k != "silent")))
    +        kind = (row or {}).get("kind", "oneshot")
    +        nums.append(f"{name}: " + asc.summary(m, sorted(k for k in m if k != "silent" and asc.applies(k, kind, False))))
    @@
    -    brief = (tpl.replace("{family_target}", family_text(fam, style)).replace("{brand}", brand_text(style))
    +    brief = (tpl.replace("{family_target}", family_text(fam, style) + event_text(row)).replace("{brand}", brand_text(style))
    @@ new function
    +def event_text(row):
    +    if not row:
    +        return ""
    +    loop = row["kind"] == "loop"
    +    return (f"\n\nThe event X is for, from the team's sound list: {row['event']} "
    +            f"({'a seamless loop' if loop else 'a one-shot'}; class {row['class']}). Judge A5 against this event; "
    +            "the family target above also describes other events of the same family."
    +            + (" X is a loop that plays for as long as the event lasts: it has no onset and no tail by design, and "
    +               "attack_ms and decay_s (one-shot measures) are not checked for it." if loop else ""))
    @@ def cmd_round
    -    pk = write_packet(rdir, files, near, results, pc["family"], style)
    +    pk = write_packet(rdir, files, near, results, pc["family"], style, next((r for r in rows if r["id"] == a.piece), None))

(`asc.applies(metric, kind, stem)` exists in `tools/audio_style_check.py`; a music stem passes `True`.) Bump the prompt
version in `tools/audio_critic_prompt.md` and add a test: a loop piece's brief names the event and prints no
`attack_ms`/`decay_s`.

Local workaround until this is on main: `tools/build/assets/sndtele_audio.py critic <Id> --event` runs the audio
lane's `critic.sh` unchanged except for one step that adds the same event sentence to the copied `brief.md`. The gate
critic (`tools/build/critic.sh audio`) still sends the stock packet, so it will repeat the fails above until the change lands.

## 2. Critic references on this branch are failed takes

`audio_loop.neighbours` fills R1..R3 with whatever takes are in `Audio/Source`. On branches cut from main before
area/audio merged, those are the 11 placeholder takes the critic already failed, shown to the critic as "sounds already
approved for this game". Suggested: skip takes whose provenance origin is `placeholder:` when picking neighbours.

## 2. style.json `enemy` family target describes only the owl's projectiles (check defect)

File: `pipeline/audio/style.json`, family `enemy` (`character`, `instruments`). Owner: build lead / audio lane.
Defect: members include WardenMove, FloodStiltMove (movement loops) and the Courier/Warden/Flood warnings, but the
target text is "The owl's projectiles. Launch... Travel... Fade...". With audio-critic/3 (event now named) the critic
fails WardenMove: "the event row (Roadwarden movement loop) and the family target (owl projectile) describe different
sounds". Fix: add one line per event kind to `character`, e.g. "Movement loops (Warden, Floodstrider): an even
armoured or stilted gait, heavy low footfalls with strap and buckle rattle, no projectile whirr. Warnings: a brace
strike, a tightening ratchet or spin-up, ending on a catch." No bar or range changes. Until applied WardenMove stays
a tracked placeholder.
