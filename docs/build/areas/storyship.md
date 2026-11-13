# Ship the Director's Cut story. Branch area/storyship. Read docs/build/worker-rules.md first.
Josh: do not wait on canon sign-off. The PROPOSED story-bible facts P1-P8 and the names Ella and Mother are adopted as
agent defaults (docs/decisions.md D-new-story-canon). Update pipeline/story/story-bible.md so those rows read CONFIRMED
(agent default, Nov 12; team may override), restore the strongest version of each of the 7 Director's Cut lines in
pipeline/story/lines.csv with ship=yes, then loop with the blind story critic (tools/build/critic.sh story <out>; it
judges shipped lines) until it passes, fixing only what it names. python3 tools/story_check.py must pass;
python3 tools/story_check.py --calibrate must PASS before you trust the critic.
Critic sanity (Josh): if the critic looks defective (the same piece failing for different reasons each round, reasons that contradict the GDD or the references, reasons it cannot judge, a piece that measurably meets every number but keeps failing, calibration drift), test the critic: it must pass the reference itself, fail a known-bad sample, and agree with itself on the same piece twice. Fix a real defect in its prompt, packet or calibration and write the fix and the evidence in docs/build/areas/<you>-status.md (the lead copies it to the build log). Never loosen the bar.
Lane: pipeline/story/**, Source/UmbrellaElla/{Public,Private}/Story/** (text data only), Tests/Story/**.
