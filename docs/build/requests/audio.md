# Requests from area/audio

## tools/build/gate.sh: record the gate critic's verdicts (Nov 12 2026)
Why: `audio_check --scan` now fails when a take is marked `placeholder:` while the latest committed critic record on
the same bytes passes (pipeline/audio/critic/<Id>.json). The gate marks placeholders without writing a record, so a gate
fail on bytes an area critic passed would turn audio_scan red on main. The latest verdict on the same bytes wins, so the
gate only has to record its own.
Change, in the audio critic block, right after the `critic.sh audio` line:

    for id in $(echo "$ids" | tr ',' ' '); do python3 pipeline/audio/build/provenance.py record "$id" >/dev/null 2>&1 || true; done

and in both places the block commits, add the records (when nothing failed, commit them alone):

    git add pipeline/art/provenance.csv pipeline/audio/critic

Decision for Josh/the lead: when the gate critic fails bytes an area critic passed on the same model, which wins?
Built default: the later verdict. Alternative: any pass on those bytes stands (then the gate must not mark them).
