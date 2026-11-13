# sndhit status

Round 1 (loop card `sndhit`, state in Saved/AudioLoop, not committed): blind critics ran on all 18 pieces, spectrogram and numbers only (no audio playback). All 18 FAIL; measured checks (audio_style_check, audio_check --scan) pass. Takes stay tracked placeholders in provenance.csv (origin `placeholder: ...`).

| Sound | Critic's biggest gap |
|---|---|
| CourierDisable | Add a defined, heavy low-mid spring-release and gear-clank transient at the start, and replace the broadband noise wash with a distinct, darker spinning-gear whirr that winds down into separate ticks in a stone-hall tail. |
| EllaDown | Replace the broadband noise decay with a clear descending low sub drop (pitch visibly falling) under a short rib-crack and cloth-crumple transient, with a little metallic partial to match the references. |
| EyeHit | Replace the flat noise body with a distinct sharp transient on a real material, such as a leather slap or heavy thud with a metallic partial, followed by a shaped decaying hall tail instead of a sustained noise wash. |
| FloodDisable | Replace the diffuse noise body with articulated clockwork content: a sharp spring-release and gear-clank hit, then a pitched low gear whirr that winds down into distinct ticks, inside a stone-hall reverb. |
| GlassCrack | Replace the broadband noise burst with a distinct structured crack: a sharp mid-high glassy or rib-snap transient with tonal ring, on a heavy low thud, with a stone-hall tail. |
| HitClock | Add a clear bright brass clank transient with a ringing bell partial (energy in the 2-6 kHz range) and clean up the noisy broadband mid layer so the metal reads as a clock hit. |
| HitEnemy | Replace the broadband noise body with distinct clockwork content: a real metallic gear clank transient followed by a spinning-gear whirr and a decaying tick train, in a stone-hall tail. |
| HitProtected | Add a distinct sharp mid-frequency rib-crack and canvas-snap transient (about 1-3 kHz) on top of the low thud, with a clean stone-hall tail, so the protected hit is identifiable and not a muddy noisy thud. |
| HitWing | Replace the low-heavy noise wash with a distinct leathery slap (sharp mid-band crack around 1-3 kHz) followed by a short, airy feather flutter, and cut the low thud so it reads as a wing and not a body hit. |
| MechanismBreak | Replace the sustained low-frequency block with a few distinct, dry, metallic mid-to-high transients (escapement ticks, a spring lurch, skipped gear teeth) with clear gaps between them and only a short low body. |
| NeedlePierce | Clean up the grainy broadband noise under the partials and give the pluck a distinct soft spark on top, so it sounds finished and clearly Ella's magic. |
| OutOfBounds | Replace the dense broadband noise bed with one clean low impact (thud with a brass or iron partial) followed by a clearly descending sub drop that fades into a dark hall tail. |
| ShutterClose | Replace the noise burst with a sharp wooden or metal shutter clack: a dry, heavy impact plus a short spring or latch ring with distinct resonant partials, instead of broadband noise. |
| SmallBlastImpact | Raise the brightness: shift the pluck up and add a high chime and spark layer so the centroid sits around 3-5 kHz and 4-8 kHz carries real energy. |
| TwinStarsImpact | Raise the energy into the 3-8 kHz band (higher-pitched celesta partials plus a tiny bright chime or spark layer) so the centroid sits near 3-4 kHz instead of about 1.8 kHz. |
| WandBoltFade | Shorten the tail to about 0.4-0.5 s and remove the broadband noise wash so only a clean celesta pluck with a few bright partials and a small spark remains. |
| WardenDisable | Add one heavy, distinct spring-release and gear-clank transient at the start, then let the following ticks and whirr drop clearly in level and spacing so the sound has a hit, a body and a wind-down instead of an even tick texture. |
| WingsBreak | Replace the filtered-noise burst with a real mechanical event built from discrete metallic impulses (a heavy dry escapement tick, then two or three skipping gear teeth and a spring lurch with an audible resonant ring), so it has a clear transient shape and clockwork material instead of a smeared noise wash. |

Common theme: layers read as broadband noise wash; critics want distinct transients (crack/clank), clearer pitched partials, more top end on wand sounds.

Left: revise recipes in pipeline/audio/build/sndhit.py per the gaps, `sndhit.py regen <Id>` (needs the ElevenLabs key and credits), new round, fresh critic; repeat until pass. Not done.
