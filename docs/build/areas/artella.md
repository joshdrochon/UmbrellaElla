# Art loop: ella-up-open, ella-attack, ella-shield, ella-closed (Ella's four states). Branch area/artella. Read docs/build/worker-rules.md first.
Josh, Nov 11: Blender only, reference bar enforced (option A). Nobody reviews by hand: you build to the bar and do not
stop until each piece passes. Pieces (card "MVP 15"; list them with python3 tools/art_loop.py pieces --card "MVP 15"): ella-up-open, ella-attack, ella-shield, ella-closed (Ella's four states).
Loop per piece (tools/art_loop.py --help, pipeline/art/README.md, pipeline/art/art-bible.md, pipeline/art/references.json):
1. Build or revise the piece in Blender: /Applications/Blender.app/Contents/MacOS/Blender -b (scripts under
   Art/Source/<Asset>/, committed; run renders through tools/build/ue_slot.sh so they share the machine's slots).
2. Deterministic checks: tools/art_check.py, tools/screen_check.py, tools/art_ref_check.py (and tools/hitbox_check.py for
   gameplay sprites). A FAIL goes straight back to step 1.
3. Blind panel: python3 tools/art_loop.py blind/panel/verdict for the piece (reference pair AND quality-bar pair: bar-casters
   for characters and shots, bar-other-realm for scene and wind). Each critic is a FRESH session you start in the empty
   packet folder: cd <packet> && env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT claude -p "$(cat tools/art_judge_prompt.md or
   the prompt art_loop names)" --disallowedTools Bash Edit Write --model claude-sonnet-5-5. Record each verdict with
   art_loop verdict. Pass = the panel picks ours or SAME in every pair and every deterministic check passes.
4. Only a passing piece replaces its _PH: shipped image under Art/<Asset>/ (outside Art/Source), its .artloop.json record,
   provenance row in pipeline/art/provenance.csv, imported into Content/UmbrellaElla/Art/<Asset>/ by a committed editor
   script (UnrealEditor-Cmd ... -run=pythonscript ... -unattended -nullrhi -nosplash -nocrashreports). Until then the _PH stays.
Commit after each round that improves a piece; log piece, round, verdict and gap in docs/build/areas/artella-status.md.
Critic sanity (Josh): if the critic looks defective (the same piece failing for different reasons each round, reasons that contradict the GDD or the references, reasons it cannot judge, a piece that measurably meets every number but keeps failing, calibration drift), test the critic: it must pass the reference itself, fail a known-bad sample, and agree with itself on the same piece twice. Fix a real defect in its prompt, packet or calibration and write the fix and the evidence in docs/build/areas/<you>-status.md (the lead copies it to the build log). Never loosen the bar.
Lane: Art/Source/<these assets>/**, Art/<these assets>/**, Content/UmbrellaElla/Art/<these assets>/**,
tools/build/assets/art_ella*.py, pipeline/art/provenance.csv (append your rows only). Never gameplay code.
