# Area: audioimport

Started by the build lead from this brief (2026-11-12). It is the definition of done.

Area audioimport. All sound lanes have merged (sndui, sndworld, sndhit, sndstate, sndlaunch, sndtele, audio). Do the one central audio import on main's sources: import every Audio/Source take that passes the audio critic (pipeline/audio/critic records) into Content as the game expects (tools/audio_import.py), making lockable .uasset files writable first (chmod u+w; the UE import fails silently on read-only files) and failing loudly on any import error. Tracked placeholder takes stay placeholders. Then run python3 tools/audio_check.py --scan and report the count of live sounds that pass, placeholders, and missing files (e.g. PhaseChime, AbsorbLoop) in your status, with the owner lane for each missing one. Targeted tests only (Audio prefix). Merge main first. Commit, stop.
