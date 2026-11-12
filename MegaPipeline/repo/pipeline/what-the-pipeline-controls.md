# What the pipeline controls

The pipeline checks some things with a tool, the same way every time. Other things are taste and feel: a person decides.
If it is not on the first list, no tool will catch it. Say so on the card.

## Checked by a tool (pass or fail)

| What | Tool |
|---|---|
| Art lines up with its collider (coverage, spill, fairness margin per role); colliders are data and never move; an art swap waits for a PASS | `tools/hitbox_check.py check` (`fit` moves only the art) |
| Sprite sheets: size, clean background, soft edges, halo, pivot drift, tile seams | `tools/sprite_check.py --scan Art` |
| Art numbers on a capture: on-palette share, accent area, dark share, hue bands, paper texture | `tools/art_check.py` |
| Text size, contrast, outlines, colour-blind states, flashes, shake size | `tools/ui_check.py` (`contrast`, `grayscale`, `flashes`, `shake`) |
| Every sound has a visual, every colour has a second signal | `tools/ui_check.py signals` |
| Strings: sentence case, no baked key names, plain words | `tools/ui_check.py strings` |
| A Quit exists (title Quit, pause Quit to title, quit code in the game) | `tools/ui_check.py quit` |
| The packaged flow: play, pause, cards, restart, quits, keyboard, mouse in menus | `tools/ui_check.py flow-check` on QA's UIFLOW line |
| Hand-check lines for each gate: survive, fail, retry, quit from play, both menu quits | `tools/ue_run.py playthrough-check` |
| Build, package, smoke: it builds, boots, holds frame rate, takes input, quits with exit 0 | `tools/ue/daily.sh` / `daily.ps1`, `tools/ue_run.py` |
| Automation tests ran and none went missing | `tools/check_automation_report.py --test-map pipeline/qa/test-map.md` |
| Owl encounter data: telegraphs, spacing, gust coverage | `tools/encounter_check.py` |
| Feel numbers stay in their limits | `tools/feel_check.py` |
| Shipped defaults equal the approved preset | `tools/bake_preset.py check` |
| Feature list matches the GDD | `tools/manifest_check.py` |
| Code stays in its modules; C++ rules | `tools/module_check.py` |
| Audio list and source files | `tools/audio_check.py` |
| A card is complete before work starts; gate records are filled and true | `tools/check_card.py` |
| A PR has its evidence, and the evidence is for this commit | `tools/check_pr.py` |
| Agents stay in their lane and off gate files | `pipeline/agent-ops/hook.py`, `tools/git_gate.py`, `tools/check_card.py --lanes` |
| No secrets in the repo | `tools/secrets_check.py` |
| Docs agree with each other; no dead links | `tools/pipeline_check.py` |
| Submission zip, page, credits, rules | `tools/submission_check.py` |
| Which prompt, pipeline version, agent, model and GDD made a run | `tools/journal.py runs`, `compare` |

## Human taste and feel (a person decides)

- Is it fun? Does the umbrella feel good to float with?
- Does the art look good and read as one style? (The Art Director signs; tools only give numbers.)
- Is the owl fair? Are the telegraphs readable in the moment? (Playtests, `pipeline/qa/playtests.md`.)
- Do the sounds and music fit? Is the mix pleasant?
- Is the difficulty right? Is 90 seconds the right length?
- Does the theme come through?
- Is a hitbox fair in play? The tool checks the numbers; playtests set them. A collider change is Richard's call.
- Do the menus feel clear? The tools check that they work, not that they are nice.
- Should a feature be cut? (Scope decision-maker.)

Checks prove a build works. They never prove it is good.
