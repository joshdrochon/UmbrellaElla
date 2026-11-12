> Generated from `docs/port-log.md` at `f8c8edc` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Port log: the inherited pipeline → Umbrella Ella pipeline
Inherited files, keys: PI Project Instr · RM README · SP Studio · PP Production · PC Producer · TDP Tech Dev · TD TD charter · DvP Development · LD Lead Dev · AP Art Pipeline · AD Art Dir · DsP Design · GD Game Designer. Line numbers ±2. Full rule-by-rule map, 0 missing: `docs/coverage-map.md`. Checks: pipeline_check 0 problems; unittest 1223 OK (2 skipped).

| Inherited file:line | Now in | Why |
|---|---|---|
| PP:308-315, TDP:428 | qa-build.md P0-P3 labels | audit §8 said kept; it was missing |
| PP:452-466; PC:121 | producer.md Gate record + exceptions | Gates had no record or outcome list |
| PP:382; PC:145,189 | producer.md status line (blocked hours, review queue, forecast) | A cut could only fire after a miss |
| PP:370-374; PC:141 | producer.md flow limits, D-new-port-3 | Agents out-produce human reviewers |
| PP:214; SP:205 | AGENTS §4, producer.md `cut`/`superseded` labels | "closed = done" hid cuts |
| SP:97,185 | D-new-port-1 | PR `Closes #` contradicts "a human marks done" |
| SP:232,260 | AGENTS §4.6 `ROLE: … \| session` on comments | Reviewer ≠ owner invisible on GitHub |
| SP:392; PC:179; TD:614 | AGENTS §4.7 GitHub-only handoffs, "prepared, not posted" | audit said kept; missing |
| SP:596; PI:34; LD:684,884-910; TD:753,782 | AGENTS §1 session-start lines + `CAN RUN`; §6 session-end handoff | No handoff when a session stops early |
| TDP:242; DvP:189; LD:897; SP:324,456 | AGENTS §5 evidence header, stale SHA, saved/pushed proof, correct by new comment | Logs had no commit; silent edits |
| LD:641; PC:185; PP:390 | AGENTS §6 blocked cause class; split instead of growing | Blocked notes had no cause |
| TDP:120,484; SP:468; DvP:255 | AGENTS §7 engine pin, repo settings, warning pragmas | Unguarded changes |
| DsP:186,427; TDP:186 | AGENTS §9 options + decide-rule; §10 squash (D-new-port-7) | Unknowns had no lean; reverts |
| TDP:146; TD:277,524; PC:199; SP:210 | decisions.md "Rules for deciding" | DECIDED with no result; rows rewritten |
| PP:131-149; TDP:218; AP:599 | templates/spike-card.md, day0 0.11 | 8 rows ask for spikes; no format |
| PP:115,182,346; TDP:191,290,476 | checklists/submission.md | Cited by 2 cards, did not exist |
| PP:285-302,346; TDP:259,283,340,391,422,437,457; LD:817 | qa-build.md record fields, checks 2-8, kept zips, bug closing, evidence labels | Smoke was one line; bugs closed on code change |
| TDP:406 | qa/test-map.md (`--require`) | Tests could vanish silently |
| TDP:124,317 | day0 0.3 Win/Mac same totals; 0.5 MustFail | Runner never shown failing on real UE |
| TDP:449; AP:141,346; PP:268 | day0 0.10 style frame, D-new-port-9/10 | Bulk art before one proved frame |
| PP:202,259,342,368,374; TDP:58,215,216,286; LD:706 | task-card fields, checklists/card-ready.md, D-new-port-11 | Happy-path Done-when; producer vs day0 conflict |
| DvP:47,140-212,251; TDP:38; TD:129,297; LD:572-586 | dev-lead #9-15, style=low, Keep unchanged, disputes | SIMPLE/LD rules claimed kept; only AI-01 was |
| DvP:53,195,257; LD:390,405; DsP:407 | gameplay-dev How to work #5-15 | Invented behavior, drive-bys, clone classes |
| AD:226,924-951; AP:93,462-469 | art-director Outputs + #11 | Revision format and fact labels claimed kept; missing |
| AP:145,150,273,285,305,385; TD:361; PP:270 | art-director #7-10, checklists/animation-review.md | Stills-only approval; art waived import checks |
| AP:303,317,544-595; AD:863-886 | templates/asset-brief.md | No visual goal, states or handoff |
| AP:151,228,249,262,346,348,489; PP:344 | asset-specialist checklist (+ tools/sprite_check.py) | Anchor first, reimport in place, scoped revisions |
| AP:45,381 | animation-review Sounds, playtests P10 | No audio import or muted check |
| TDP:203,279; DvP:100,156 | technical-director validator card, tuning units | audit §7 gap; unitless tuning |
| DsP:95,152,242,562; GD:1270,1417 | checklists/design-review.md | No design role or design check |
| DsP:194-212,362-380,488,527,616; GD:1621-1701 | qa/playtests.md protocol, validity, class, severity | audit said kept; none were |
| DsP:212,388-411; GD:1787; RM:173 | checklists/tuning.md | No one-change-at-a-time rule |
| DsP:290,320; GD:289,1139,1197 | checklists/level-sections.md, integrator CAM_Eval_Stress | Sections had goals, no acceptance |
| PP:388-421; RM:339; GD:265 | jam-brief risk table + cut-order rule; card-ready stretch line | No triggers or fallbacks |
| DvP:77,160; PP:260; PC:205 | file-hygiene.md | Dumping-ground files, stray TODOs |
| RM:109-111; GD:2181-2184 (coverage map) | PR template `Could not read:`; check_pr rule unread | Unread inputs were implied read; audit §8 claimed RM:111 was kept |
| TD:418 | task-card `Context:` field, task.yml, check_card required | dev-lead.md already cited a Context line that did not exist |
| PP:462,486-487,531; TD:869; LD:978 | gate-record `Verdicts:`, `Process change:`, `Incidents since last gate:`; `--gate-record` | No per-discipline sign-off, no incident review |
| DvP:177; DvP:169,179; DvP:108,118 | module_check rules N (determinism), O (mutable static), P (writable container getter) | GDD QA-08 needs repeatable runs; PIE keeps statics |
| DvP:77,147-148,178,247; LD:574-579 | cpp-rules one type per header, one state change per statement, TMap order; gameplay-code log once, no personal data; gameplay-dev #10 isolate | SIMPLE-02 was claimed ported and was not; debug loop was half there |
| TDP:190 | agent-ops README rotate rule; `secrets_check.py --text` | Secrets outside git were unchecked |
| AP:382; AP:151,430-435,531-532 | `sprite_check.py --sources`; card 0.10b round trip, timed | No proof an asset can be edited and reimported |
| SP:468,516; PI:29; PC:163; AD:579 | agent-ops.md Never (no spending), asset-brief `Tool:` | Nothing stopped a paid sign-up |
| AD:39,423-437; GD:2087-2103; GD:1789-1805 | art-director #15, game-designer #7 and Outputs 4, playtests step 3 | Challenge was optional; dominant strategies were not diagnosed |
| PP:250; DsP:290,320,409-418,535 | design-review: no hidden help, gamepad too, §3 what else it can break | GDD targets controller; regressions after art/camera changes |
| LD:466,708; SP:210; PC:229 | card-ready lines; tracker-table reply size | Tiny cards, over-specified briefs, unverified stretch approver |

Rejected: approval-per-Push, EP gates, 9-14-state lifecycles, decision matrices (SP:187, PP:214, LD:211, AP:72); number bans (AP:26, GD:1430, TDP:146); saves/localization/consoles (TDP:41,103,105); usage meters and compaction (SP:470-566, PI:29); reference registers and self-ratings; C# style and `_camelCase` (DvP:93-162); asset ID registry, GimpCLI, backups (AP:176-246,329); debt register, trace IDs (TDP:484, DsP:260).

Reviewer eval (measured, scratch copy, clean cases only): with the new dev-lead.md, 14/15/32/33/35 approve. 34 failed on my first wording (Config/** needs package); I narrowed rule 9 and it approved 2/2. Case 13 fails with the new prompt 0/6 and with the OLD prompt 1/5, so it is broken by the in-flight case/unreal-rules edits, not by this port. Defect cases not re-run.

For other lanes:
- unreal-rules.md: single writer per fact + numbered invariants (TDP:38-44); per-component UENUM state (D-new-port-4); EndPlay unbind/timer clear; no per-frame actor searches; no runtime GetMutableDefault; ctor/BeginPlay/EndPlay split with logged missing refs; one log category; no std::/exceptions/dynamic_cast; no gameplay on flipbook/AnimNotify/sound events (AP:307, PP:287); draw-order depths in one header (AP:128); dev-only debug cvar (TDP:480); test that BP_* refs are set (AP:424).
- tools/: check_pr path-based package rule, lane globs, evidence header, linked "Not done" lines, `Next:`; pipeline_check greps (bare TODO, warning pragmas, `ROLE:` in Source/Config, *Helpers/*Manager, `_PH` before G4, unprefixed assets, LFS bytes); tools/ue timeouts, dirty-tree refusal, BUILD_INFO.txt, smoke exit code + Ensure/Fatal/Accessed None counts; art_check WARN band; flipbook pivot-drift check.
- evals/: case 13 needs fixing; full eval must be re-run (dev-lead.md changed); a speculative-interface case (TD:129); rejected captures into art-judge calibration (AP:214).
- .github/: PR template `Part of #` (D-new-port-1), evidence header, `Next:`; task.yml needs Player outcome / Out of scope / Used by / Needs (check_card.py already reads them from task-card.md).
- docs/audit.md §8 overstates what was kept (P0-P3, SIMPLE, revision format, DsP:95/194/366/562, GD:1417/1651, LD:578/899, PC:179/185). Now ported; §8 should be corrected.
