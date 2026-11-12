# References used for the pipeline audit (issue #11)

Every source the audit and pipeline were built from. Read-only: none of these were edited.
Retrieved 2026-11-06 by Josh (with Claude Code).

## Source of truth for jam rules
| # | Source | Where | What we took from it |
|---|---|---|---|
| R0 | 2026 Epic AI MegaJam Official Rules (16 pages, last updated November 5, 2026; sha256 71457d4dc8bea132e2a45dbffcffddcd6b9c69330706595b1e5fe32e9f042603), downloaded by Josh 2026-11-09 | `docs/rules/2026_Epic_AI_MegaJam_Official_Rules_EN.pdf` (Git LFS), text in `docs/rules/official-rules.md`. Canonical: https://epicgames.box.com/s/svkmfifwv7336vyq1h0y7eucdr9d6ooc, linked from https://www.unrealengine.com/news/2026-epic-ai-megajam. Downloaded from https://epicgames.ent.box.com/s/a7xcgl07fqoieeb99sjtd3juhj4agc4z | **Top source for jam rules: the Official Rules prevail over everything else in this repo**, the itch page included. `docs/jam-rules.md` cites its sections; `manifest_check.py` rule rules-pin pins the file; `submission_check.py rules` ties the checks to its text |

## Task and team context
| # | Source | Where | What we took from it |
|---|---|---|---|
| R1 | Issue #11 "[Task] Review of Agents [Due by Morning 11/7]" | https://github.com/RickTheBuilder/GameJam2026/issues/11 | Done-when: recommendations incl. architecture changes and additional evals |
| R2 | Inherited-pipeline author's comment on #11 | same issue, comment | Roles = studio level; Pipelines = IP-based; Project Instructions = agent instructions; README ties it together. No QA/Marketing/Legal/Localization roles yet. Tech and Dev pipelines reference Unity. Art Director must be refocused on our art direction |
| R3 | The inherited pipeline (13 files, 77,707 words) | https://1drv.ms/f/c/4a13810d04e8bc13/IgDjPh4OQAr7SKVjDiBJ5SBQAeapbon0qkSInMjZ-jceAdw?e=qp03r8 | The material under audit. Not copied into this repo; link only |
| R4 | Rick's review summary of the inherited pipeline (shared in chat) | Pasted by Rick to the team | Baseline findings: other game leaks, Unity-specific, ~78k words too large, describes but does not enforce, README status conflict, Lead Dev clause names Art Director, "UEProject" folder describes Unity |
| R5 | Rick's "Game Jam AI Development Pipeline" | https://docs.google.com/document/d/1z4wlXLt4OfSqyGxf_2e9RaNc04-MllK47_990_6B4C4/edit?tab=t.0#heading=h.o8z2hdhspqkf | 7 proposed roles, Dev Lead owns the code-quality gate, "test the reviewer with known problems", unknowns format, smaller core set, model/reasoning guidance |
| R6 | GDD "Umbrella Ella GDD Draft v1" (THE LAST HOUR, Draft 1.0, 6 Nov 2026), doc id 1m3seh8jm58AnBLvH0Mx1G-wuyZ3Yuh7wh3V1REt-ONY | Google Doc | Mechanics, P0/P1/P2, open team decisions. Source of truth for MECHANICS. Replaced the earlier Draft 1 (doc 14JG2d2w2wNKR57owgEk8c-08LZIw4_KK2a0BHJdqcwY, a five-section platformer) on 2026-11-07 |
| R7 | Target key art image (shared in chat by Josh) | `pipeline/art/reference/target-keyart.png` (Git LFS) | Source of truth for ART (team decision, 2026-11-06). Described in `pipeline/art/art-bible.md` |
| R8 | Issue #2 Tooling Decisions | https://github.com/RickTheBuilder/GameJam2026/issues/2 | Candidate tools: Meshy.ai, Blender, GIMP, Aseprite, ElevenLabs, Suno, MCP connections |
| R9 | Issue #4 Test the AI pipeline on every machine | https://github.com/RickTheBuilder/GameJam2026/issues/4 | Per-machine pipeline smoke test; scope decision-maker and packaging owner must be recorded |
| R10 | Issue #14 Setup Unreal | https://github.com/RickTheBuilder/GameJam2026/issues/14 | Unreal Engine 5.8.4; agents connect through Unreal's MCP |
| R11 | Issues #1, #12, #13 | repo issues | Working hours, GDD due EOD 11/7, architecture defense due 7pm 11/7 PST |
| R12 | A public build video | https://www.youtube.com/watch?v=mjg_JUMar04 | The top model for hard calls (plans, reviews, verdicts), Opus for mechanics (`pipeline/agent-ops/model-tiers.md`); a fresh session per card (AGENTS.md §4); Blender models as headless scripts (`pipeline/art/import-rules.md` §6) |

## Direction from Josh (prompt, 2026-11-06)
- Act as a staff AI-native software engineer running the audit; that role is stated in `docs/audit.md`.
- Goal: pipeline, prompts and guardrails strong enough to one-shot the game.
- Technical Director owns the Unreal equivalent of Unity assembly definitions (module boundaries).
- Art Director gets strict evals where needed.
- Set a hard bar for evals: a judge must catch planted defects before anyone trusts it.
- End with a summary in the style of Rick's review (R4).
- Do not write to shared docs. Do not push until the team confirms.
