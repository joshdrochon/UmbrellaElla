# Requests from area/sndui (UI sounds)

The lane is `Audio/Source/<ids>/**`, `Content/UmbrellaElla/Audio/<ids>/**` and provenance rows, so the scripts the lane
needed live here until the build lead moves them. Nothing in `pipeline/audio/build/` or `tools/` was edited.

## 1. Recipes outside recipes.py (audio lane file)
Six sound lanes cannot all edit `pipeline/audio/build/recipes.py`. Each sndui sound keeps its recipe next to its take:
`Audio/Source/<Id>/recipe.json` (same keys as a `RECIPES` entry). Requested change in `recipes.py`, at the end:

    import json, pathlib
    for _f in sorted((pathlib.Path(__file__).resolve().parents[3] / "Audio/Source").glob("*/recipe.json")):
        RECIPES[_f.parent.name] = json.loads(_f.read_text())

Until then `docs/build/requests/sndui_snd.py` does the same load and then runs the audio lane's own `regen.py` and
`provenance.py` unchanged (no fork):

    set -a; . ~/.umbrella-ella.env; set +a          # only in this shell, never printed
    REGEN_DIR=/tmp/sndui/gen python3 docs/build/requests/sndui_snd.py gen <Id>    # build, level-match to the ui RMS target
    python3 docs/build/requests/sndui_snd.py prov <Id>                            # provenance row, sorted among Audio/Source rows
    docs/build/requests/sndui_crit.sh <Id> [<Id>...]                              # blind critic, one loop card per piece (SNDUI-<Id>)

## 2. regen.py: trim runs before the lead-silence cut
`mix()` applies `atrim=0:<trim>` before `silenceremove`, so a layer whose generated file starts with more silence than
`trim` is cut to nothing (seen on UiBack, UiOpen, PauseOut: the first layer vanished). Workaround used in the sndui recipes:
no `trim` key; the layer's `filter` starts with `atrim=0:<s>,asetpts=PTS-STARTPTS,`, which runs after the silence cut.
Suggested fix for the audio lane: move the trim after `silenceremove`.

## 3. Import script
`tools/build/assets/arena_audio_import.py` has a fixed cue table and imports to the Audio root. The UI sounds import with
`docs/build/requests/sndui_audio_import.py` (to `/Game/UmbrellaElla/Audio/<Id>/SW_<Id>_00`, class SCL_UI, concurrency
SCON_UI). Requested: move it to `tools/build/assets/`.
