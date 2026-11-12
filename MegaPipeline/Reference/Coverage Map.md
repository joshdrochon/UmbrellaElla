> Generated from `docs/coverage-map.md` at `f8c8edc` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Coverage map: the inherited pipeline → Umbrella Ella pipeline

Bar: take the inherited pipeline and make it more robust; lose nothing meaningful. The inherited pipeline is 13 files
(about 78k words) written for another game on another engine. Agents never load it (`docs/references.md` R3). This map
goes through every file section by section and rule by rule, and records where each rule lives in ours.

Statuses: **COVERED** ours has it (location + how it is enforced). **STRENGTHENED** ours has it and adds a check it
lacked. **ADAPTED** same intent, changed for Unreal, this game or a 4-day jam ("DISPUTABLE:" marks a place where ours
does the opposite on purpose). **PORTED** was missing; added in this pass. **DROPPED** (a) other engine or other game
with no engine-neutral intent, (b) human approval steps that would stall a 4-day jam, (c) nothing an agent can observe.
Line numbers are the inherited files' `cat -n` lines. Our locations are `path:line` after the final-11 fixes (built at 364734e, re-verified at f81a824, remapped from bd2f865, then to the round-13 Official Rules and gap changes on top of 2236f37; Still missing stays 0).
Earlier ports with their source lines: `docs/port-log.md`.

## Summary

| Inherited file | Items | Covered | Strengthened | Adapted | Ported now | Dropped | Still missing |
|---|---|---|---|---|---|---|---|
| Project Instructions | 84 | 39 | 14 | 24 | 1 | 6 | 0 |
| README (project structure) | 65 | 25 | 8 | 25 | 1 | 6 | 0 |
| Studio Pipeline | 140 | 59 | 25 | 40 | 3 | 13 | 0 |
| Production Pipeline | 168 | 77 | 26 | 50 | 4 | 11 | 0 |
| Producer charter | 122 | 45 | 29 | 40 | 2 | 6 | 0 |
| Technical Development Pipeline | 179 | 76 | 31 | 53 | 1 | 18 | 0 |
| Technical Director charter | 135 | 59 | 29 | 39 | 2 | 6 | 0 |
| Development Pipeline | 118 | 22 | 21 | 52 | 6 | 17 | 0 |
| Lead Developer charter | 119 | 54 | 31 | 24 | 3 | 7 | 0 |
| Art Pipeline | 167 | 66 | 27 | 57 | 4 | 13 | 0 |
| Art Director charter | 95 | 32 | 19 | 31 | 3 | 10 | 0 |
| Design Pipeline | 128 | 49 | 24 | 36 | 5 | 14 | 0 |
| Game Designer charter | 141 | 59 | 20 | 50 | 3 | 9 | 0 |
| **Total** | **1661** | **662** | **304** | **521** | **38** | **136** | **0** |
## Re-verification at f81a824 (after the GDD 1.3 re-file, dry-run fix rounds 5-10 and eval rounds 8-11)

Every cited `path:line` was traced from 364734e to f81a824 with a line diff, and every rewritten line was read.
Status counts before → after: all unchanged (table above). Still missing: 0 → 0. Nothing needed porting back.
- 416 rows had their line numbers updated. 0 cited files were deleted; 0 rules were deleted. Rewritten lines kept the
  rule and changed the game facts (GDD B1.0 → 1.3: MVP 1-12, ATTACK/SHIELD holds, 90 s END-01, test-map one test per row).
- Every test, tool and flag named in the Enforcement column still exists at f81a824. The full suite passes at the
  map's commit.
- Fixed while checking: `.github/CODEOWNERS.example:12-15` cited a line past the end (now 12-14). Enforcement text for
  the D-new-p0-signoff rows now says it was answered by GDD 1.3 §2.
- Rules a later fix weakened or contradicts (marked `FLAG f81a824` in their rows):
  - `encounter_check.py` E4, E19, E24 and part of E6 run only with 2+ owl patterns, and E25 only with SURV-04 lift loss
    on (6130c77, deliberate for GDD 1.3's one bolt). Six Game Designer charter rows and two Design Pipeline rows rest on
    them, so in the current game their enforcement is doc only.
  - `pipeline/ui/accessibility.md:49` E1 calls the Hold/Toggle setting open (`docs/gdd/questions-1.3.md` Q8), but the
    settled `docs/decisions.md:74` D18 says Toggle is a saved setting and `ui_check.py tests` still requires
    `HoldToggleSetting`. The design owner settles Q8; then one of the three changes.

## What this pass ported (38 rows, 20 changes)

| Change | Rows | Where | Enforced by |
|---|---|---|---|
| Unread inputs are declared, never implied read | README:109-111, Game Designer charter:2181-2184 | `.github/PULL_REQUEST_TEMPLATE.md` `Could not read:` | `check_pr.py` rule unread (test) |
| Card `Context:` field: what the code next to Outputs does today | Technical Director charter:418 | `pipeline/templates/task-card.md`, `.github/ISSUE_TEMPLATE/task.yml` | `check_card.py` required field (form test) |
| Gate record: each discipline signs its verdict; a fail blocks Pass | Production Pipeline:462, :531 | `pipeline/templates/gate-record.md` `Verdicts:` | `check_card.py --gate-record` (tests) |
| Gate record: incident review after a P0 or main-red revert | Technical Director charter:869, Lead Developer charter:978 | gate-record `Incidents since last gate:` | `--gate-record` (tests) |
| Gate record: a repeated slowdown becomes a card with an owner | Production Pipeline:486-487 | gate-record `Process change:` | `--gate-record` (tests) |
| Determinism: no wall clock or unseeded random in gameplay | Development Pipeline:177 | `pipeline/unreal/cpp-rules.md` | `module_check.py` rule N (tests) |
| No mutable static state or static delegates (PIE keeps it) | Development Pipeline:169,179 | cpp-rules | `module_check.py` rule O (tests) |
| No getter hands out a writable container | Development Pipeline:108,118 | cpp-rules | `module_check.py` rule P (tests) |
| Secrets outside git (PR bodies, comments, package) + rotate same hour | Technical Development Pipeline:190 | `pipeline/agent-ops/README.md` | `secrets_check.py --text` (tests) |
| Every imported asset keeps a layered source | Art Pipeline:382 | `pipeline/roles/asset-specialist.md` | `sprite_check.py --sources` (tests) |
| Day-0 source → reimport round trip, timed | Art Pipeline:151, :430-435, :531-532 | card 0.10b Done-when | card evidence |
| No agent spending or paid sign-ups | Studio Pipeline:468, :516; Project Instructions:29; Producer charter:163; Art Director charter:579 | `pipeline/roles/agent-ops.md` Never, asset brief `Tool:` | `Spend OK:` link by a named human |
| Art Director and Game Designer must challenge a request that breaks a rule or target | Art Director charter:39, :423-437; Game Designer charter:2087-2103 | role cards | §9 block + decision row |
| Dominant strategies found in play get a cause | Game Designer charter:1789-1805 | `pipeline/qa/playtests.md`, game-designer Outputs | playtest notes |
| No hidden difficulty help | Production Pipeline:250 | `pipeline/checklists/design-review.md` | checklist |
| Gamepad parity (GDD B §9 targets controller) | Design Pipeline:290, :320, :535 | design-review, playtests | checklist; device noted |
| Re-run what a change can break (captures, P-tests, encounter codes) | Design Pipeline:409-418 | design-review §3 | checklist |
| No tiny cards; Done-when says what, not how; stretch approval author is the human | Lead Developer charter:466, :708; Studio Pipeline:210 | `pipeline/checklists/card-ready.md` | Producer readiness |
| Log once per run, no personal data in logs; one type per header; one state change per statement | Development Pipeline:77, :147-148, :178, :247 | cpp-rules, `pipeline/unreal/gameplay-code.md` | reviewer |
| Reply size matches the question | Producer charter:229 | `pipeline/templates/tracker-table.md` | doc only |

Also fixed while checking: `pipeline/roles/dev-lead.md` already told the reviewer to read the card's Context line, which
did not exist (now it does). The debug loop (Lead Developer charter:574-579) had only "reproduce" and "regression test";
`pipeline/roles/gameplay-dev.md` step 10 now has isolate, one testable cause and a temporary log line. Earlier claims
corrected: `docs/audit.md` §8 said README:111 lived in AGENTS.md §2 (it did not; now the `Could not read:` line);
`docs/port-log.md` said Development Pipeline SIMPLE-02 went to dev-lead.md (it is now cpp-rules "one state change per
statement") and that pipeline_check greps `*Helpers`/`*Manager` names (it does not; dev-lead #10 and file-hygiene cover them as text).

## Choices a reasonable person might dispute

- Ours fixes numbers up front (fps 55, P-test pass lines, 120/60 min card caps, review queue 3) and changes them only with a measurement. The inherited pipeline bans numbers before measurement (Art Pipeline:26, Game Designer charter:1430, Technical Development Pipeline:144).
- Ours fixes the deadline and cuts scope by trigger; the inherited pipeline keeps scope and moves time (README:331, Production Pipeline:376, Technical Development Pipeline:34). Gates are clock times, which it bans (Production Pipeline:100-105).
- Ours builds the stated default while a decision is open; it stops work until decided (Producer charter:66, Project Instructions:15).
- Ours ranks sources by level; it says its list is not a precedence order (Studio Pipeline:29-45). Ours relies on many small checks; it forbids bespoke automation (Studio Pipeline:172, :224).
- Ours puts readability above vision (Art Director charter:74-86) and hard-fails palette drift it wanted as warnings (Art Pipeline:374-377).
- Ours requires warn-and-fall-back for unknown events; it bans broad fallbacks (Development Pipeline:137-138).
- Dropped as out of jam scope: save and crash recovery (Production Pipeline:141), localization and pseudo-localization (Art Pipeline:311, Technical Development Pipeline:103), self-ratings and reference registers (Technical Director charter:871, Game Designer charter:2300; the latter also dropped an outside accessibility-guidelines citation).
- Context-window and compaction rules dropped as (c); continuity is the journal hooks, with no checkpoint before compaction (Studio Pipeline:478, :520-538).
- Not ported, judged covered: the `ROLE:` comment prefix (doc only; a hook check on `gh` comment bodies would enforce it), engine version in `BUILD_INFO.txt` (engine is pinned).

## Item by item

### inherited: Project Instructions

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Project Instructions:1,11,17,21,24,28,32,36 | Section headings | DROPPED | - | no rule content |
| Project Instructions:2a | Top authority activates roles by command | STRENGTHENED | AGENTS.md:9,18; pipeline/agent-ops/README.md:21 | hook.py guard; launch with JAM_ROLE via tools/agent.sh |
| Project Instructions:2b | Read the applicable role charter | COVERED | AGENTS.md:9 | doc only |
| Project Instructions:2c | Disclose missing or provisional authority | ADAPTED | docs/jam-brief.md:85-100; AGENTS.md:17 | doc only; People table Confirmed column, CAN RUN line |
| Project Instructions:2d | Role-charter use needs top approval | DROPPED | - | (b) charter approval step; our role cards are gate paths changed by human PR |
| Project Instructions:2e | Command switches role; consultation does not | STRENGTHENED | AGENTS.md:52 | hook.py guard (one JAM_ROLE per session) |
| Project Instructions:2f | Quoted names never activate roles | STRENGTHENED | pipeline/agent-ops/hook.py:126-127; pipeline/agent-ops/README.md:21 | hook.py ignores typed ROLE lines |
| Project Instructions:2g | New assignment starts with recipient role | COVERED | AGENTS.md:9; pipeline/templates/task-card.md:17 | check_card.py owner role field |
| Project Instructions:2h | Multi-role work names coordinator and owners | STRENGTHENED | AGENTS.md:53; pipeline/templates/task-card.md:17-19 | check_card.py (owner, reviewer, human) |
| Project Instructions:2i | Perspectives in one chat are not independent | COVERED | AGENTS.md:52 | doc only |
| Project Instructions:3 | Top authority: vision, priorities, closure | ADAPTED | AGENTS.md:67-68; docs/jam-brief.md:87-88 | doc only; scope decision-maker and creative director seats |
| Project Instructions:4 | Producer: roadmap, backlog, deps, records | COVERED | pipeline/roles/producer.md:6-11 | check_card.py --status, --tracker |
| Project Instructions:5 | Designer: mechanics, tuning, design acceptance | COVERED | AGENTS.md:45; docs/jam-brief.md:93 | doc only |
| Project Instructions:6 | Art Director: visual intent, art acceptance | COVERED | AGENTS.md:41 | doc only |
| Project Instructions:7 | Technical Director: architecture, interfaces, standards | COVERED | AGENTS.md:39,99 | doc only + CODEOWNERS.example |
| Project Instructions:8 | Lead Developer: code, builds, tests, verification | ADAPTED | AGENTS.md:36-37,43 | doc only; split into Dev Lead, Gameplay Dev, QA and Build |
| Project Instructions:9a | QA authority comes from its charter | COVERED | pipeline/roles/qa-build.md:7-9 | doc only |
| Project Instructions:9b | Never override others' accepted requirements | COVERED | AGENTS.md:98; pipeline/roles/gameplay-dev.md:50 | doc only |
| Project Instructions:9c | Separate chats share no execution or permissions | COVERED | AGENTS.md:17,64-65 | doc only |
| Project Instructions:12a | Studio pipeline governs coordination and records | ADAPTED | AGENTS.md:3,5-13 | doc only; one always-loaded file plus on-demand docs |
| Project Instructions:12b | Consult the named departmental pipeline list | DROPPED | - | (a) other game's document set; agents do not load it (docs/references.md R3) |
| Project Instructions:13a | Each pipeline governs its own discipline | ADAPTED | AGENTS.md:11-13,23-27 | doc only; Unreal rules, art bible, GDD by subject |
| Project Instructions:13b | Keep TD architecture and lead implementation authority | COVERED | AGENTS.md:100; pipeline/roles/gameplay-dev.md:47 | doc only |
| Project Instructions:14a | Published coding standards apply | STRENGTHENED | pipeline/unreal/cpp-rules.md:42 | module_check.py in CI |
| Project Instructions:14b | Automated enforcement needs separate authorization | ADAPTED | AGENTS.md:107-127 | DISPUTABLE: ours turns checks on by default in CI |
| Project Instructions:14c | Publishing a standard authorizes no changes | COVERED | AGENTS.md:58 | doc only (no card, no work) |
| Project Instructions:15a | Pipelines never override GDD or decisions | COVERED | AGENTS.md:23-28 | doc only |
| Project Instructions:15b | Resolve conflicts with owner before execution | ADAPTED | AGENTS.md:30-31 | pipeline_check.py (row exists); DISPUTABLE: ours builds the default instead of waiting |
| Project Instructions:15c | New documents not binding without approval | STRENGTHENED | pipeline/agent-ops/gates.json:3-20; .github/CODEOWNERS.example:12-14 | hook.py guard on gate paths |
| Project Instructions:18a | Producer owns roadmap, backlog, schedule, reports | ADAPTED | pipeline/roles/producer.md:6-11 | doc only; defects owned by QA and Build (qa-build.md:16) |
| Project Instructions:18b | Rolling-wave: detail current milestone only | COVERED | pipeline/checklists/card-ready.md:5; pipeline/roles/producer.md:31 | doc only (D-new-port-11) |
| Project Instructions:18c | Future detail follows evidence, not guessed dates | COVERED | pipeline/checklists/card-ready.md:5 | doc only |
| Project Instructions:18d | Milestone, package, push, assignment hierarchy | ADAPTED | AGENTS.md:57-60; pipeline/roles/producer.md:40-47 | doc only; gate then card |
| Project Instructions:18e | Favor integrated playable results | STRENGTHENED | AGENTS.md:76; pipeline/roles/producer.md:42 | check_pr.py package rule; gates pass in a packaged build |
| Project Instructions:19a | Push cadence with approval before execution | DROPPED | - | (b) per-batch approval stalls a 4-day jam; daily cadence in producer.md:26-37 |
| Project Instructions:19b | Stand-ups triggered by work, not sprints | ADAPTED | pipeline/roles/producer.md:32,36 | check_card.py --status; daily status line |
| Project Instructions:19c | Consult only necessary specialists | COVERED | AGENTS.md:50 | doc only |
| Project Instructions:19d | Escalate material blockers and conflicts | COVERED | AGENTS.md:30-31,82-83 | doc only (blocked label, decision row) |
| Project Instructions:19e | Push done does not close milestone | COVERED | pipeline/roles/producer.md:40,73 | doc only |
| Project Instructions:22a | Nine-stage authorization lifecycle | ADAPTED | AGENTS.md:70 | labels; four states plus blocked, cut, superseded |
| Project Instructions:22b | Plans, issues, commits, outputs prove nothing | COVERED | AGENTS.md:63,72; .github/PULL_REQUEST_TEMPLATE.md:3-5 | doc only |
| Project Instructions:22c | Routine tasks proceed within existing authority | COVERED | AGENTS.md:67-68 | doc only |
| Project Instructions:22d | Top approval for new work and material changes | ADAPTED | AGENTS.md:58-59,66-67 | check_card.py features authorized; no per-Push approval |
| Project Instructions:22e | Specialists keep departmental acceptance | COVERED | AGENTS.md:63-64 | doc only (reviewer role verdict) |
| Project Instructions:22f | Producer keeps records, never grants or closes | COVERED | pipeline/roles/producer.md:73-75; AGENTS.md:98 | doc only |
| Project Instructions:25a | GitHub is the operational system of record | COVERED | AGENTS.md:19,64 | doc only |
| Project Instructions:25b | Who owns projects, access, implementation, credentials | ADAPTED | AGENTS.md:103; pipeline/roles/producer.md:6-11 | hook.py guard asks on gh secret, gh repo edit |
| Project Instructions:25c | Verify access per environment; approvals don't transfer | COVERED | AGENTS.md:17; pipeline/agent-ops/README.md:104 | doc only (CAN RUN line) |
| Project Instructions:25d | Prefer existing tools over custom systems | ADAPTED | AGENTS.md:100; pipeline/roles/dev-lead.md:37 | doc only; DISPUTABLE: ours builds stdlib checks on purpose |
| Project Instructions:26a | Attributable record: role, action, reason, verification | ADAPTED | AGENTS.md:64,134; .github/PULL_REQUEST_TEMPLATE.md | check_pr.py; fields spread over ROLE prefix and PR template |
| Project Instructions:26b | Group coherent changes, not per-field comments | COVERED | AGENTS.md:64-65 | doc only |
| Project Instructions:26c | Record failures, partial changes, reversals | COVERED | AGENTS.md:80,82,86; pipeline/roles/qa-build.md:45 | main-red.yml revert PR |
| Project Instructions:26d | Account identity alone is insufficient | COVERED | AGENTS.md:64 | doc only (ROLE prefix) |
| Project Instructions:26e | Comments never grant authorization or acceptance | ADAPTED | docs/decisions.md:12; pipeline/roles/producer.md:76 | doc only; a linked human comment approves stretch cards, author not checked |
| Project Instructions:26f | No parallel local Markdown admin logs | COVERED | AGENTS.md:18-19,64 | doc only; local journal is machine record only |
| Project Instructions:26g | Status, merge, card move is not acceptance | COVERED | AGENTS.md:63; pipeline/templates/gate-record.md:34 | check_card.py --gate-record |
| Project Instructions:29a | Usage readings at start and end of work | ADAPTED | pipeline/agent-ops/README.md:118-125 | prompt_log.py status; daily per machine |
| Project Instructions:29b | Check usage between costly increments | ADAPTED | pipeline/templates/task-card.md:42-43; AGENTS.md:89 | check_card.py --overrun; time budget per card |
| Project Instructions:29c | Shared readings; Producer consolidates usage | ADAPTED | pipeline/agent-ops/README.md:118 | Producer pastes AGENT-OPS line daily |
| Project Instructions:29d | Hard remaining-allowance floors as stops | ADAPTED | pipeline/agent-ops/README.md:122-124; pipeline/roles/agent-ops.md:42 | prompt_log.py cap=OVER exits 1 |
| Project Instructions:29e | Never start work likely to breach floors | COVERED | pipeline/roles/agent-ops.md:42 | prompt_log.py cap=OVER |
| Project Instructions:29f | No unapproved spending or billing changes | PORTED | pipeline/roles/agent-ops.md:73; pipeline/templates/asset-brief.md:17 | doc only; `Spend OK:` link by a named human; brief `Tool:` field |
| Project Instructions:29g | No unapproved agent expansion | COVERED | pipeline/agent-ops/README.md:21; AGENTS.md:100 | hook.py guard (subagents need a known role) |
| Project Instructions:30a | Record error and env, diagnose once, name owner | STRENGTHENED | AGENTS.md:83-84; pipeline/agent-ops/README.md:80 | prompt_log.py attempts |
| Project Instructions:30b | Give humans the exact action for barriers | COVERED | AGENTS.md:17,82; pipeline/roles/gameplay-dev.md:29 | doc only (Not run with who runs it) |
| Project Instructions:30c | No retries, speculative delegation, permission growth | STRENGTHENED | AGENTS.md:83; pipeline/agent-ops/README.md:34 | bypass mode disabled in settings.json |
| Project Instructions:30d | Continue unrelated authorized work | COVERED | AGENTS.md:87-88 | check_card.py --blocked-by |
| Project Instructions:33a | Set objective, owners, deps, verification, stop criteria | STRENGTHENED | pipeline/templates/task-card.md:6-47 | check_card.py field check |
| Project Instructions:33b | Verify tool, repo, file, build access | COVERED | AGENTS.md:15-17 | doc only |
| Project Instructions:33c | Report revisions, tests run and not run, risks | STRENGTHENED | .github/PULL_REQUEST_TEMPLATE.md:14-29 | check_pr.py header, proof, links |
| Project Instructions:33d | Separate intent, generated, developer-tested, accepted | STRENGTHENED | AGENTS.md:76; pipeline/roles/qa-build.md:48; pipeline/qa/playtests.md:66 | check_pr.py package rule, evidence label |
| Project Instructions:33e | Conflicts: requirement, owner, options; stop affected only | COVERED | AGENTS.md:30-31,87,131 | doc only |
| Project Instructions:34a | Durable handoff with outputs, blockers, next owner | STRENGTHENED | AGENTS.md:86; .github/PULL_REQUEST_TEMPLATE.md:26-39 | check_pr.py journal, next; journal.py export |
| Project Instructions:34b | Prefer GitHub records, no redundant local reports | COVERED | AGENTS.md:65 | doc only |
| Project Instructions:34c | Preserve role, decisions, state before compaction | ADAPTED | pipeline/agent-ops/journal_hook.py:5-12; pipeline/agent-ops/settings.json:71-80 | Stop hook checkpoint; SessionStart re-prints resume |
| Project Instructions:34d | Run compact after handoff and verify | DROPPED | - | (a) other tool's command |
| Project Instructions:34e | Compaction is not evidence or reset | COVERED | AGENTS.md:73 | doc only (only pasted output counts) |
| Project Instructions:37a | Follow naming, versioning, discovery conventions | ADAPTED | AGENTS.md:5-13; docs/gdd/README.md:5-10 | doc only; read order and GDD snapshot naming |
| Project Instructions:37b | New uploads are references, not approvals | ADAPTED | docs/gdd/README.md:12-17; AGENTS.md:8,97 | check_pr.py gdd; a new GDD lands by PR, manifest never promoted by agents |
| Project Instructions:37c | Version meaningful artifacts, not minor replies | ADAPTED | docs/gdd/README.md:6 | doc only; git history plus GDD snapshots |
| Project Instructions:37d | Route changes through owning authority | STRENGTHENED | pipeline/agent-ops/gates.json:3-20; .github/CODEOWNERS.example | hook.py guard on gate paths |
| Project Instructions:37e | Keep verified decisions in approved systems | COVERED | docs/decisions.md:11-18 | pipeline_check.py (cited rows exist) |
| Project Instructions:37f | Keep governance apart from code and gameplay rules | COVERED | AGENTS.md:5-13 | doc only (AGENTS, pipeline/unreal/, GDD separate) |
| Project Instructions:37g | Value craft, candor, sustainability, efficiency | DROPPED | - | (c) values statement, nothing observable |

### inherited: README (project structure)

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| README (project structure):1-9 | Title, version, status, approval route | DROPPED | - | no rule content; (b) Producer + EP publication route |
| README (project structure):11-13 | Purpose: organization, sources, ownership, versions, handoffs | DROPPED | - | no rule content |
| README (project structure):15 | Governance doc is stable, not a live status register | COVERED | AGENTS.md:7-8; docs/gdd/README.md:7 | manifest_check.py (reads CURRENT); AGENTS not edited per GDD revision |
| README (project structure):17 | Behavior governed by instructions + role charters | COVERED | AGENTS.md:5-13 | doc only |
| README (project structure):19-27 | Project identity block (studio, platform, players) | ADAPTED | docs/jam-brief.md:5-9 | doc only; other game's identity replaced by ours |
| README (project structure):29-39 | Design north star; concept doc governs it | ADAPTED | docs/jam-brief.md:6,9 | doc only; other game's loop replaced; GDD snapshot governs |
| README (project structure):41-49 | Five governance sources by responsibility | ADAPTED | AGENTS.md:23-28; docs/jam-brief.md:38-40 | doc only; strict ranking instead of "complementary" |
| README (project structure):51 | Sources complementary; README doesn't replace others | COVERED | AGENTS.md:23-28 | doc only |
| README (project structure):53 | Conflict: escalate, never silently pick convenient reading | STRENGTHENED | AGENTS.md:30-31; docs/jam-brief.md:3 | pipeline_check.py (cited row must exist); PR states default |
| README (project structure):55-57 | Discover relevant docs at start of work | ADAPTED | AGENTS.md:5-14 | doc only; fixed read order instead of discovery |
| README (project structure):59-74 | Group docs by family regardless of version | ADAPTED | docs/gdd/README.md:5-10 | doc only; one family per folder, snapshots by revision |
| README (project structure):76-85 | Numeric version compare; working ref vs binding baseline | ADAPTED | docs/gdd/README.md:6-8; docs/gdd/CURRENT | manifest_check.py; explicit CURRENT pointer replaces numeric sort |
| README (project structure):87 | Upload date or newest ≠ approved | STRENGTHENED | docs/gdd/README.md:17; AGENTS.md:58-59 | manifest_check.py authorized; check_card.py |
| README (project structure):89 | No explicit status → Unverified, working only | ADAPTED | pipeline/art/style.json:223; pipeline/agent-ops/README.md:105-109 | [VERIFY] tags; tests/test_sprite_check.py |
| README (project structure):91-99 | New version becomes working ref; no README edit | ADAPTED | docs/gdd/README.md:12-24 | check_pr.py (GDD impact section); one PR moves CURRENT |
| README (project structure):101 | Don't re-ask version confirmation when clear | COVERED | AGENTS.md:67-68 | doc only |
| README (project structure):103-105 | Two files same version, different content: compare | ADAPTED | docs/gdd/README.md:6 | doc only; one snapshot per revision, never edited, git history |
| README (project structure):107 | Draft vs approved conflict kept for reconciliation | ADAPTED | docs/gdd/README.md:17; AGENTS.md:30-31 | manifest_check.py; statuses never promoted by agents; decision row |
| README (project structure):109-111 | Inaccessible docs: disclose; never claim inspected | PORTED | .github/PULL_REQUEST_TEMPLATE.md:28; tools/check_pr.py | check_pr rule unread (test_could_not_read_line_required) |
| README (project structure):113-115 | Authority by subject, not by most recent upload | COVERED | AGENTS.md:23-28; docs/jam-brief.md:38-40 | doc only |
| README (project structure):117-126 | Authority table per document family | ADAPTED | docs/jam-brief.md:38-40; AGENTS.md:23-28 | doc only; no TDD, unreal-rules + roles carry technical authority |
| README (project structure):128 | Historical docs never override newer approved | COVERED | AGENTS.md:7; docs/decisions.md:16 | doc only (archive never read) |
| README (project structure):130 | Downstream meets upstream without silently redefining | COVERED | pipeline/roles/dev-lead.md:38 | gate (review checklist #11, decision row needed) |
| README (project structure):132 | Upstream doesn't dictate downstream implementation | ADAPTED | pipeline/templates/task-card.md:23-27 | check_card.py; DISPUTABLE: our cards prescribe outputs and lanes on purpose |
| README (project structure):134-138 | Pipelines govern methods, not requirements or approval | COVERED | AGENTS.md:23-28 | doc only (pipeline docs rank "everything else") |
| README (project structure):140-148 | Pipeline ownership table | ADAPTED | AGENTS.md:33-48 | pipeline_check.py (roles); roles table replaces pipeline owners |
| README (project structure):150 | TD owns architecture; Lead Dev owns implementation review | ADAPTED | AGENTS.md:37-39; pipeline/roles/technical-director.md:38 | module_check.py; TD modules/build, Dev Lead review |
| README (project structure):152-154 | Locate Development Pipeline by family/version | DROPPED | - | (b) bookkeeping for one of his files |
| README (project structure):156 | Dev and tech pipelines complementary; neither authorizes | ADAPTED | AGENTS.md:58-59 | check_card.py; authorization lives in the manifest |
| README (project structure):158a | Publishing a rule ≠ enforcement installed; verify deploy | COVERED | AGENTS.md:129-130; pipeline/day0-cards.md:58 | gate (card 0.17 pastes branch protection) |
| README (project structure):158b | Four stable-filename exceptions unchanged; no rename | DROPPED | - | no rule content |
| README (project structure):160-169 | Conflict owner by discipline | COVERED | AGENTS.md:23-28,53 | doc only (D34, scope decision-maker) |
| README (project structure):171 | Cross-discipline disagreement: requirements, impact, owners, fix | STRENGTHENED | AGENTS.md:30-31; docs/decisions.md:21 | pipeline_check.py (row, owner seat) |
| README (project structure):173 | Evidence may justify change, does not authorize it | COVERED | docs/decisions.md:13-15; pipeline/checklists/tuning.md:9 | doc only |
| README (project structure):175 | Material conflicts go to the executive | COVERED | AGENTS.md:54,66-67 | doc only (scope decision-maker) |
| README (project structure):177-185 | Design evidence vs technical evidence (examples) | ADAPTED | pipeline/qa/playtests.md; pipeline/qa/test-map.md | tests + playtest rows; other game's examples dropped |
| README (project structure):187-193 | Who owns design/tech hypotheses, validation, gates | ADAPTED | pipeline/checklists/design-review.md:11; AGENTS.md:33-48 | doc only |
| README (project structure):195 | A documented hypothesis is not proof | COVERED | pipeline/checklists/design-review.md:11; docs/decisions.md:13 | doc only |
| README (project structure):197-201 | Approved design doesn't authorize coding/spikes | STRENGTHENED | AGENTS.md:57-59; pipeline/templates/task-card.md:13-15 | check_card.py (implementation_authorized, Hook only) |
| README (project structure):203-205 | Evidence cycle ending Keep / Revise / Cut | COVERED | pipeline/templates/spike-card.md:25; pipeline/templates/test-note.md:12 | required field (Recommendation, Decision) |
| README (project structure):207 | Owning discipline reconciles evidence-based changes | COVERED | docs/decisions.md:12; docs/gdd/README.md:17 | doc only |
| README (project structure):209 | Routine authorized work needs no repeat approval | COVERED | AGENTS.md:67-68 | doc only |
| README (project structure):211-223 | Document naming convention, consistent family names | ADAPTED | docs/gdd/README.md:6 | doc only; `GDD-<rev>.md`, other files stable names |
| README (project structure):226-239 | Stable filenames; history keeps prior versions | ADAPTED | AGENTS.md:95,135 | doc only; git history replaces archived snapshots |
| README (project structure):242-251 | Controlled-doc metadata fields | ADAPTED | docs/gdd/README.md:13 | doc only; GDD header has revision, date, source commit; no owner/status on pipeline docs |
| README (project structure):253-257 | Status words Draft → Approved → Superseded | ADAPTED | pipeline/roles/producer.md:16; docs/decisions.md:16 | doc only; "Superseded by" banner, manifest statuses |
| README (project structure):261 | New release keeps prior and lists material changes | STRENGTHENED | docs/gdd/README.md:6,18-20 | gdd_impact.py; check_pr.py (GDD impact) |
| README (project structure):263 | Never silently overwrite approved versions | COVERED | AGENTS.md:95,97 | doc only |
| README (project structure):265 | Version increments reflect real maturity | DROPPED | - | (b) manual versioning; git commits replace it |
| README (project structure):267 | Owner recommends; other approvals stay distinct | COVERED | pipeline/templates/task-card.md:17-19; AGENTS.md:63,92 | check_card.py (owner ≠ reviewer, Human) |
| README (project structure):269 | Highest = working; highest approved = binding | ADAPTED | docs/gdd/CURRENT; docs/feature-manifest.json | manifest_check.py; see RM:76-85 |
| README (project structure):271-282 | Handoff fields: sources, decisions, risks, verification, next | STRENGTHENED | .github/PULL_REQUEST_TEMPLATE.md:2-39; pipeline/templates/task-card.md:12 | check_pr.py (sections, links, Next:, Journal); GDD revision field |
| README (project structure):284 | Release the full artifact, not only a summary | COVERED | pipeline/roles/dev-lead.md:27; docs/gdd/README.md:13 | doc only |
| README (project structure):286 | Preserve prior releases; follow delivery conventions | COVERED | AGENTS.md:60,94,135 | doc only (branch + PR, squash) |
| README (project structure):288 | Never claim saved/uploaded unless verified | STRENGTHENED | AGENTS.md:86; pipeline/templates/gate-record.md:12,33 | check_card.py --gate-record (re-downloaded and launched) |
| README (project structure):290-306 | Intended repository root and folders | ADAPTED | AGENTS.md:5-13 | pipeline_check.py; our layout (docs/, pipeline/, tools/, Source/) |
| README (project structure):308 | Don't assume folders exist without checking | STRENGTHENED | pipeline/checklists/card-ready.md:6 | pipeline_check.py (cited path must exist) |
| README (project structure):310 | Repo structure changes via TD and Production | COVERED | AGENTS.md:53,99 | doc only |
| README (project structure):312-327 | Project decisions in controlled docs, not README index | COVERED | docs/decisions.md; AGENTS.md:7 | pipeline_check.py (cited IDs need a row); examples are other game's |
| README (project structure):331 | Don't optimize against an arbitrary deadline | ADAPTED | pipeline/roles/producer.md:64 | doc only; DISPUTABLE: ours says scope moves, not the deadline |
| README (project structure):333-335 | Difficult ≠ bad; keep justified complexity | ADAPTED | docs/jam-brief.md:60-61 | doc only; DISPUTABLE: ours defaults to cutting, gated features only after MVP |
| README (project structure):337 | Simplify complexity lacking player value | COVERED | pipeline/roles/dev-lead.md:37; pipeline/roles/gameplay-dev.md:30 | gate (review checklist #10) |
| README (project structure):339 | Narrow breadth before cutting core cause and effect | COVERED | docs/jam-brief.md:64-70; pipeline/roles/producer.md:54 | doc only (cut list, Never cut) |
| README (project structure):341-357 | Working principle steps | COVERED | AGENTS.md:5-19,23-30,55-69 | doc only |
| README (project structure):359-365 | v1.5 revision evidence, hashes, review disposition | DROPPED | - | (b) publication record for his files; status conflicts with RM:5 |

### inherited: Studio Pipeline

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Studio Pipeline:1-15 | Title, owner, status, version stamps | DROPPED | - | no rule content |
| Studio Pipeline:17-23 | Purpose and scope statement | DROPPED | - | no rule content |
| Studio Pipeline:27 | Top authority holds reserved approvals | ADAPTED | AGENTS.md:67-68; docs/jam-brief.md:87 | doc only; EP becomes the scope decision-maker plus a short human-approval list |
| Studio Pipeline:29-45 | Source list by responsibility, not precedence | ADAPTED | AGENTS.md:23-31 | doc only; DISPUTABLE: ours sets an explicit precedence order, his refuses one |
| Studio Pipeline:47 | On conflict name requirement, owner, decision | COVERED | AGENTS.md:30-31; AGENTS.md:133 | doc only (decision row format) |
| Studio Pipeline:49 | New pipeline rules bind only once approved | STRENGTHENED | pipeline/agent-ops/gates.json:3-20; pipeline/agent-ops/README.md:20; .github/CODEOWNERS.example:12-13 | hook.py guard blocks agent edits to AGENTS.md, roles, tools; human PR |
| Studio Pipeline:53 | Every action has an accountable role | STRENGTHENED | AGENTS.md:9; pipeline/agent-ops/README.md:21 | hook.py guard exits 2 on writes without JAM_ROLE |
| Studio Pipeline:55-67 | Role list and acceptance domains | ADAPTED | AGENTS.md:33-48 | doc only; 13 jam roles, EP folded into human seats in docs/jam-brief.md:79-96 |
| Studio Pipeline:69 | No impersonating another discipline's approval | COVERED | AGENTS.md:94; AGENTS.md:52; pipeline/roles/dev-lead.md:56 | doc only |
| Studio Pipeline:69 | Do not revise another's accepted requirements | STRENGTHENED | AGENTS.md:98; docs/gdd/README.md:6,17 | doc only + gate paths; GDD snapshots read-only, manifest never promoted |
| Studio Pipeline:71 | Multi-role work names coordinator and owners | STRENGTHENED | AGENTS.md:53; pipeline/templates/task-card.md:17-19 | check_card.py (owner role, reviewer role, human required) |
| Studio Pipeline:75-89 | Assignment states objective, owner, deps, evidence, stop | STRENGTHENED | pipeline/templates/task-card.md:6-47; .github/ISSUE_TEMPLATE/task.yml | check_card.py field check |
| Studio Pipeline:91-95 | Nine-stage authorization lifecycle | ADAPTED | AGENTS.md:70; pipeline/templates/task-card.md:57-58 | labels; four states plus blocked, cut, superseded |
| Studio Pipeline:97 | Issue, merge or test is not acceptance | COVERED | AGENTS.md:63; docs/decisions.md (D-new-port-1); .github/PULL_REQUEST_TEMPLATE.md:3-5 | doc only; Part of # default |
| Studio Pipeline:99 | Routine work needs no repeated approval | COVERED | AGENTS.md:67-68 | doc only |
| Studio Pipeline:101 | New work and material changes need top approval | ADAPTED | AGENTS.md:58-59,66-67; docs/gdd/README.md:17 | check_card.py features must be implementation_authorized; no per-Push approval |
| Studio Pipeline:105 | Use approved systems of record, no parallel admin | COVERED | AGENTS.md:65; AGENTS.md:18-19 | doc only; local journal is a machine record, GitHub is truth |
| Studio Pipeline:107-117 | Issues, projects, milestones, commits, controlled docs map | ADAPTED | AGENTS.md:57-70; pipeline/roles/producer.md:20-23 | doc only; issues + labels + pinned tracker, no Projects or Milestones |
| Studio Pipeline:119 | Board card is a view, not requirements | COVERED | AGENTS.md:23-28 | doc only (cards rank below GDD and manifest) |
| Studio Pipeline:121-123 | No duplicate local Markdown; docs when justified | COVERED | AGENTS.md:65; pipeline/roles/producer.md:16 | doc only |
| Studio Pipeline:127-143 | Producer reconciles board fields with verified work | STRENGTHENED | pipeline/roles/producer.md:20-24,32 | check_card.py --status, --tracker, --lanes |
| Studio Pipeline:145 | Assigning a role is not authorization | COVERED | AGENTS.md:58-59 | check_card.py (features authorized, card ready) |
| Studio Pipeline:147 | Status reflects real state, not activity | COVERED | AGENTS.md:63,69; pipeline/roles/qa-build.md:44 | doc only; human marks done after evidence |
| Studio Pipeline:149 | Producer cannot invent authorization or close milestones | COVERED | pipeline/roles/producer.md:40,73-75 | doc only |
| Studio Pipeline:153 | Hierarchy milestone, package, push, assignment | ADAPTED | AGENTS.md:57-60; pipeline/roles/producer.md:40-47 | doc only; gate then card, one card one PR |
| Studio Pipeline:153 | Issue type and relationships explicit | ADAPTED | .github/ISSUE_TEMPLATE/task.yml:4; pipeline/roles/qa-build.md:17-20; pipeline/templates/task-card.md:28 | labels task, P0-P3; decisions live in docs/decisions.md, not issues |
| Studio Pipeline:153 | Gate is a checkpoint, issue only if useful | COVERED | pipeline/templates/gate-record.md:3 | check_card.py --gate-record; gate is a tracker comment |
| Studio Pipeline:155 | Detail current milestone only, no speculative backlog | COVERED | pipeline/checklists/card-ready.md:5; pipeline/roles/producer.md:31 | doc only (D-new-port-11) |
| Studio Pipeline:155 | Current milestone shows deps, critical path, risks | ADAPTED | docs/jam-brief.md:73-81; pipeline/roles/producer.md:21-22 | check_card.py --blocked-by, --status; no explicit critical path |
| Studio Pipeline:155 | Link blockers natively or with direct link | STRENGTHENED | AGENTS.md:88; pipeline/templates/task-card.md:28 | check_card.py --blocked-by, Used by follow-up card check |
| Studio Pipeline:155 | Planning card may exist without execution | COVERED | pipeline/roles/producer.md:31,68 | doc only (one-line placeholders) |
| Studio Pipeline:157 | Every milestone item actually published and linked | STRENGTHENED | pipeline/roles/producer.md:23,68 | check_card.py --tracker (MVP table) |
| Studio Pipeline:157 | No assignments for departments with no work | COVERED | AGENTS.md:50 | doc only |
| Studio Pipeline:161 | Stable unique IDs, outcome titles, never renumber | ADAPTED | AGENTS.md:60; pipeline/templates/task-card.md:7-8; docs/decisions.md:7,16 | check_card.py id check; one UE- prefix instead of area prefixes |
| Studio Pipeline:163-170 | Issue minimum content: outcome, owner, placement, constraints | STRENGTHENED | pipeline/templates/task-card.md:6-47 | check_card.py field check |
| Studio Pipeline:172 | Defect needs repro, impact, disposition | COVERED | pipeline/roles/qa-build.md:17-20 | doc only |
| Studio Pipeline:172 | Incomplete issue is not decision-ready | STRENGTHENED | AGENTS.md:58; pipeline/checklists/card-ready.md:3 | check_card.py (empty field fails) |
| Studio Pipeline:172 | Prefer template, no automation prerequisite | ADAPTED | .github/ISSUE_TEMPLATE/task.yml | form + check_card.py; DISPUTABLE: ours makes automation central |
| Studio Pipeline:176-181 | Separate status, authorization and approval fields | ADAPTED | AGENTS.md:70; docs/feature-manifest.json; docs/decisions.md:11-18 | labels for status, manifest for authorization, decision rows for approval |
| Studio Pipeline:178 | No approval stage as an execution status | COVERED | AGENTS.md:70 | doc only (states have no approval state) |
| Studio Pipeline:180 | Blank approval value is not approval | COVERED | pipeline/templates/task-card.md:4 | check_card.py (empty field fails) |
| Studio Pipeline:183 | Kanban and approvals board views | DROPPED | - | (b) board views add admin with no gate effect in 4 days |
| Studio Pipeline:183 | No silent workflow or automation changes | STRENGTHENED | AGENTS.md:103; pipeline/agent-ops/README.md:23 | hook.py guard asks a human on gh repo edit, gh api |
| Studio Pipeline:185 | Done needs verified completion and acceptance | COVERED | AGENTS.md:63; pipeline/templates/task-card.md:57-58; pipeline/templates/gate-record.md:34 | check_card.py --gate-record (counts only passed) |
| Studio Pipeline:185 | Correct misleading state set by automation | COVERED | .github/PULL_REQUEST_TEMPLATE.md:3-5; pipeline/roles/producer.md:59-60 | check_pr.py task check; cut/superseded labels |
| Studio Pipeline:189 | Approval covers exact scope, not later work | ADAPTED | docs/decisions.md:11-18; AGENTS.md:58-59 | doc only; approval is a DECIDED row or authorized feature, not a field |
| Studio Pipeline:191-201 | Decision request: one sentence, recommendation, risks, effect | ADAPTED | AGENTS.md:30-31,131; docs/decisions.md:21 | pipeline_check.py (row ID and owner); options + lean, no 7-part form |
| Studio Pipeline:201 | Ambiguous multi-option choice not decision-ready | COVERED | AGENTS.md:133 | doc only (your lean and why) |
| Studio Pipeline:205 | Approved: verify actor, read comments, execute | ADAPTED | docs/decisions.md:12; AGENTS.md:19 | doc only; owner edits row from own account |
| Studio Pipeline:206 | Changes requested: revise and resubmit, no execution | ADAPTED | pipeline/roles/dev-lead.md:49-50; pipeline/roles/producer.md:55 | doc only; request_changes loop for PRs |
| Studio Pipeline:207 | Rejected: no retry via revised card | COVERED | pipeline/roles/producer.md:60; docs/decisions.md:15 | doc only (no re-filing cut scope) |
| Studio Pipeline:208 | Not-required only within documented delegation | COVERED | AGENTS.md:67-68 | doc only |
| Studio Pipeline:210 | Never self-grant approval | COVERED | AGENTS.md:94; pipeline/roles/producer.md:73 | doc only |
| Studio Pipeline:210 | Verify approver identity, not just a field | PORTED | pipeline/checklists/card-ready.md:12 | Producer opens the link: author account + no `ROLE:` line |
| Studio Pipeline:210 | Unclear approval evidence blocks only affected work | COVERED | AGENTS.md:88 | check_card.py --blocked-by |
| Studio Pipeline:210 | Material scope changes need new approval | COVERED | AGENTS.md:67-68,84 | doc only (split proposal) |
| Studio Pipeline:212 | Preserve decision evidence and scope | COVERED | docs/decisions.md:12-16 | doc only |
| Studio Pipeline:216 | Link artifacts, disclose checks not done | STRENGTHENED | .github/PULL_REQUEST_TEMPLATE.md:14-29; AGENTS.md:77 | check_pr.py proof, links, next |
| Studio Pipeline:216 | Owners accept; Producer records integrated acceptance | ADAPTED | AGENTS.md:63-64; pipeline/templates/gate-record.md | check_card.py --gate-record; human closes gate |
| Studio Pipeline:218 | One meaningful comment over per-field comments | ADAPTED | AGENTS.md:64-65 | doc only; one ROLE-prefixed comment or PR |
| Studio Pipeline:218 | Verify outcome before Done; Push not milestone | COVERED | pipeline/templates/task-card.md:57-58; pipeline/roles/producer.md:40 | doc only |
| Studio Pipeline:218 | No fake independent QA evidence | STRENGTHENED | pipeline/roles/qa-build.md:48,58 | check_pr.py evidence label line |
| Studio Pipeline:222 | Start: read pipeline, card, comments, prior handoff | STRENGTHENED | AGENTS.md:15-19 | journal.py resume via SessionStart hook |
| Studio Pipeline:222 | Previous session access not assumed current | COVERED | AGENTS.md:17,19 | doc only (CAN RUN line, re-run claimed checks) |
| Studio Pipeline:222 | Resolve stale or contradictory records first | ADAPTED | AGENTS.md:30-31 | doc only; build the default and proceed |
| Studio Pipeline:224 | Handoff on existing issue or PR | STRENGTHENED | AGENTS.md:86; .github/PULL_REQUEST_TEMPLATE.md:38-39 | check_pr.py journal |
| Studio Pipeline:224 | Producer tells active roles about workflow changes | ADAPTED | AGENTS.md:5,19 | doc only; each session re-reads docs from main |
| Studio Pipeline:224 | Review the standard when gaps recur | COVERED | pipeline/templates/gate-record.md:18,31 | check_card.py --status (questions required) |
| Studio Pipeline:224 | No parallel tracking docs or bespoke automation | ADAPTED | AGENTS.md:65 | doc only; DISPUTABLE: ours builds checks on purpose |
| Studio Pipeline:230-234 | Every shared change attributable to a role | COVERED | AGENTS.md:64,134 | doc only (ROLE prefix, commit trailer); no check |
| Studio Pipeline:232 | Account identity alone is not attribution | COVERED | AGENTS.md:64; pipeline/agent-ops/hook.py:126-127 | doc only |
| Studio Pipeline:238-254 | Covered change types; read-only exempt | ADAPTED | AGENTS.md:64,82,134 | doc only; label moves carry no record except blocked diagnosis |
| Studio Pipeline:258-274 | Record actor, action, reason, authority, verification, outcome, time | ADAPTED | AGENTS.md:64,78; .github/PULL_REQUEST_TEMPLATE.md | check_pr.py; fields spread over ROLE prefix and PR template |
| Studio Pipeline:278-292 | Record where work is tracked; one change set | COVERED | AGENTS.md:64-65,134; pipeline/roles/producer.md:20 | doc only |
| Studio Pipeline:296-316 | Fixed change-record block format | ADAPTED | AGENTS.md:64; .github/PULL_REQUEST_TEMPLATE.md | check_pr.py; no generic block |
| Studio Pipeline:320 | Never report attempted change as completed | COVERED | AGENTS.md:77 | doc only |
| Studio Pipeline:322 | Verify resulting state after material writes | ADAPTED | pipeline/templates/gate-record.md:5 | check_card.py --gate-record re-reads tracker; not general |
| Studio Pipeline:324 | Record partial runs, failures, reversals | COVERED | AGENTS.md:83,86; pipeline/roles/qa-build.md:45 | main-red.yml revert PR |
| Studio Pipeline:326-328 | No silent history rewrite; corrections link earlier | COVERED | AGENTS.md:80,94; docs/decisions.md:16 | doc only |
| Studio Pipeline:330 | Never fabricate actor, approval, result | COVERED | AGENTS.md:77; pipeline/agent-ops/README.md:21 | hook.py ignores typed ROLE lines |
| Studio Pipeline:332 | Change comment is not authorization | ADAPTED | docs/decisions.md:12; pipeline/roles/producer.md:76 | doc only; a linked human comment does approve stretch cards |
| Studio Pipeline:334-336 | Record fails: report, keep evidence, restore | COVERED | AGENTS.md:66 | doc only (prepared, not posted) |
| Studio Pipeline:340-360 | Cross-department sequence with top approval | ADAPTED | AGENTS.md:57-66 | doc only; card flow, no approval step for routine cards |
| Studio Pipeline:346 | Check existing decisions before new work | COVERED | AGENTS.md:12; pipeline/roles/producer.md:77 | pipeline_check.py (cited IDs exist) |
| Studio Pipeline:362 | Consult only needed specialists | COVERED | AGENTS.md:50 | doc only |
| Studio Pipeline:364 | Role views in one chat not independent | COVERED | AGENTS.md:52 | hook.py guard (one JAM_ROLE per session) |
| Studio Pipeline:366 | Consulting does not transfer decision rights | COVERED | AGENTS.md:54; docs/decisions.md:6 | doc only |
| Studio Pipeline:370-390 | Specialist handoff fields to coordinator | STRENGTHENED | AGENTS.md:86; .github/PULL_REQUEST_TEMPLATE.md:14-39 | check_pr.py journal, next, links |
| Studio Pipeline:388 | Opening and closing resource readings | ADAPTED | pipeline/agent-ops/README.md:117-125 | prompt_log.py status; per machine per day, not per card |
| Studio Pipeline:392-398 | Separate-chat reply is not delivery; no false claims | COVERED | AGENTS.md:65-66 | doc only |
| Studio Pipeline:402-416 | Producer reconciles results; delivered vs awaited | STRENGTHENED | pipeline/roles/producer.md:21-22 | check_card.py --status |
| Studio Pipeline:418-420 | No summed overlapping usage; report limits | ADAPTED | pipeline/agent-ops/README.md:122-125 | prompt_log.py; per-host totals, cap=n/a when unknown |
| Studio Pipeline:422 | Routine reconciliation needs no approval | COVERED | AGENTS.md:67-68 | doc only |
| Studio Pipeline:426-428 | Directly commissioned work still gets handoff | COVERED | AGENTS.md:58,64 | doc only (no card, no work) |
| Studio Pipeline:432-436 | Push cadence with approval step | DROPPED | - | (b) per-batch approval stalls a 4-day jam; daily cadence instead |
| Studio Pipeline:438-440 | Push done is not milestone closed; next work proposed | COVERED | pipeline/roles/producer.md:40,73 | doc only |
| Studio Pipeline:444-454 | Produced, verified, accepted, closed are distinct | ADAPTED | AGENTS.md:63,69; pipeline/roles/qa-build.md:48 | check_pr.py evidence label; four states |
| Studio Pipeline:456 | Report tests run, env, revision, defects | STRENGTHENED | AGENTS.md:79; .github/PULL_REQUEST_TEMPLATE.md:15 | check_pr.py header (stale SHA fails) |
| Studio Pipeline:458 | Generated vs integrated, intent vs observed, dev vs QA | STRENGTHENED | AGENTS.md:76; pipeline/qa/playtests.md:66; pipeline/roles/qa-build.md:48 | check_pr.py package rule |
| Studio Pipeline:460 | No claiming another role's acceptance | COVERED | AGENTS.md:94; pipeline/roles/qa-build.md:58 | doc only |
| Studio Pipeline:464 | Existing tools before custom infrastructure | ADAPTED | AGENTS.md:100; pipeline/roles/dev-lead.md:37 | doc only; DISPUTABLE: ours builds stdlib checks on purpose |
| Studio Pipeline:466 | Verify access in this environment | COVERED | AGENTS.md:17; pipeline/agent-ops/README.md:104 | doc only (CAN RUN line) |
| Studio Pipeline:468 | Credentials and elevated permissions need approval | STRENGTHENED | AGENTS.md:103; pipeline/agent-ops/README.md:23,34,36 | hook.py guard, settings deny rules |
| Studio Pipeline:468 | External spending needs approval | PORTED | pipeline/roles/agent-ops.md:73; pipeline/templates/asset-brief.md:17 | doc only; `Spend OK:` link by a named human; brief `Tool:` field |
| Studio Pipeline:472-486 | Per-assignment usage readings and checks | ADAPTED | pipeline/agent-ops/README.md:118-125; pipeline/roles/agent-ops.md:42 | prompt_log.py status; daily per machine, REVIEW at 2x median card |
| Studio Pipeline:478 | Capture context-window use | DROPPED | - | (c) the agent cannot read its context fill reliably |
| Studio Pipeline:488 | Use the status command | DROPPED | - | (a) other tool's command |
| Studio Pipeline:490 | Never report a command not seen run | COVERED | AGENTS.md:77 | doc only |
| Studio Pipeline:492 | Unavailable measurement marked unavailable | COVERED | pipeline/roles/qa-build.md:53; pipeline/agent-ops/README.md:125 | doc only (Not checked, cap=n/a) |
| Studio Pipeline:494 | Checks at boundaries, not every message | DROPPED | - | no rule content beyond SP:472 |
| Studio Pipeline:498-508 | Hard usage floors; stop before crossing | ADAPTED | pipeline/agent-ops/README.md:122-124 | prompt_log.py cap=OVER exits 1; daily token cap |
| Studio Pipeline:510 | Assess, bounded work, verify, check, continue | ADAPTED | pipeline/templates/task-card.md:42-44; AGENTS.md:89 | check_card.py --overrun; time budget per card |
| Studio Pipeline:512-514 | Shared readings are not per-role costs | DROPPED | - | (a) other tool's shared-account meter |
| Studio Pipeline:516 | No spending, billing or floor exceptions | PORTED | pipeline/roles/agent-ops.md:73; pipeline/templates/asset-brief.md:17 | doc only; `Spend OK:` link by a named human; brief `Tool:` field |
| Studio Pipeline:520-530 | Context use vs allowance; no guessed percent | DROPPED | - | (c) context fill not observable by the agent |
| Studio Pipeline:534-538 | Compact at 80% context | DROPPED | - | (c) threshold the agent cannot see |
| Studio Pipeline:540-556 | Preserve role, decisions, next step before compaction | ADAPTED | pipeline/agent-ops/journal_hook.py:5-12; pipeline/agent-ops/settings.json:71-80 | Stop hook checkpoint; SessionStart re-prints resume after compaction |
| Studio Pipeline:558-562 | Use compact command; verify it worked | DROPPED | - | (a) other tool's command |
| Studio Pipeline:564-566 | Compaction is not evidence; not after every task | COVERED | AGENTS.md:73 | doc only (only pasted output counts) |
| Studio Pipeline:570-576 | Proportionate monitoring, no redundant usage logs | COVERED | pipeline/agent-ops/README.md:118 | prompt_log.py status once daily |
| Studio Pipeline:580-586 | On failure record error, diagnose once, name owner | STRENGTHENED | AGENTS.md:83-84; pipeline/agent-ops/README.md:80 | prompt_log.py attempts |
| Studio Pipeline:588-590 | No speculative retries or permission expansion | STRENGTHENED | AGENTS.md:83; pipeline/agent-ops/README.md:34 | bypass mode disabled in settings.json |
| Studio Pipeline:592 | Continue unrelated work | COVERED | AGENTS.md:87-88 | check_card.py --blocked-by |
| Studio Pipeline:596-616 | Durable handoff record fields | STRENGTHENED | AGENTS.md:86; .github/PULL_REQUEST_TEMPLATE.md:26-39 | check_pr.py journal, next; journal.py export |
| Studio Pipeline:612-614 | Resource and context readings in handoff | DROPPED | - | (c) context not observable; usage is daily per machine |
| Studio Pipeline:618-620 | Prefer issue or PR; summary is not evidence | COVERED | AGENTS.md:65,72 | doc only |
| Studio Pipeline:624-632 | Final outcome: done, partial, blocked, failed | ADAPTED | AGENTS.md:70,82,85 | journal.py export; labels plus Not done list |
| Studio Pipeline:634-646 | Opening and closing allowance report | ADAPTED | pipeline/agent-ops/README.md:118 | prompt_log.py status AGENT-OPS line daily |
| Studio Pipeline:650-652 | Separate chats share nothing; confirmed delivery | COVERED | AGENTS.md:65-66 | doc only |
| Studio Pipeline:654-656 | Coordinator gets enough references to reconcile | COVERED | pipeline/roles/producer.md:21-22; AGENTS.md:86 | check_card.py --status |
| Studio Pipeline:660-674 | Compaction preserve list | ADAPTED | pipeline/agent-ops/journal_hook.py:5-12 | journal hooks; see SP:540-556 |
| Studio Pipeline:676 | Summary separates facts from guesses | COVERED | AGENTS.md:77; pipeline/qa/playtests.md:66; pipeline/roles/art-director.md:34 | doc only |
| Studio Pipeline:678-680 | Compaction not record, approval or reset | COVERED | AGENTS.md:65,72 | doc only |
| Studio Pipeline:684-688 | Owner approves pipeline changes; affected owners review | STRENGTHENED | pipeline/agent-ops/gates.json:3-20; .github/CODEOWNERS.example:12-14 | hook.py guard on gate paths |
| Studio Pipeline:690-692 | Version meaningful docs; skip routine edits | ADAPTED | docs/gdd/README.md:6-7; pipeline/roles/producer.md:16 | doc only; git history plus GDD snapshots, no doc version stamps |
| Studio Pipeline:696-698 | Revision states version, owner, changes | ADAPTED | docs/gdd/README.md:12-24 | check_pr.py gdd (gdd_impact.py output) |
| Studio Pipeline:700 | Communicate changes; find docs needing amendment | STRENGTHENED | AGENTS.md:53; docs/gdd/README.md:22 | pipeline_check.py cross-doc consistency; gdd_impact.py cited-by |
| Studio Pipeline:702 | Revised pipeline does not authorize work | COVERED | AGENTS.md:58 | doc only (no card, no work) |
| Studio Pipeline:704-713 | Revision history table | DROPPED | - | no rule content |
| Studio Pipeline:717 | Success: attributable, verifiable, recorded once | COVERED | AGENTS.md:64-65,72 | doc only (summary of rows above) |

### inherited: Production Pipeline

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Production Pipeline:1-11 | Title, version, approval stamps | DROPPED | - | no rule content |
| Production Pipeline:12-15 | Document existing does not authorize work | COVERED | AGENTS.md:57 | doc only; "No card, no work" |
| Production Pipeline:16-18 | Mandate: integrated, demonstrably working game | ADAPTED | docs/jam-brief.md:42 | gate; MVP true in a packaged build |
| Production Pipeline:19-20 | Minimum game is the complete loop, not a fragment | ADAPTED | docs/jam-brief.md:6; docs/jam-brief.md:57 | gate; other game's loop replaced by survive-or-fail full loop |
| Production Pipeline:21-23 | Integrated vertical slices, not departmental waterfalls | COVERED | pipeline/roles/producer.md:44; docs/jam-brief.md:108 | gate; G1 is the whole loop in graybox |
| Production Pipeline:24 | Validate expensive unknowns early | COVERED | pipeline/day0-cards.md:39; pipeline/day0-cards.md:51; pipeline/checklists/card-ready.md:8 | gate; card 0.6 real-engine proof, spike cards due Day 0/1 |
| Production Pipeline:25 | Keep game continuously integrable | COVERED | docs/jam-brief.md:108; pipeline/roles/qa-build.md:27 | gate; daily.ps1 DAILY line within 1 h of merge |
| Production Pipeline:26 | Scale only what has proved its value | COVERED | pipeline/roles/producer.md:54 | doc only; no bulk asset cards before style frame (D-new-port-9) |
| Production Pipeline:27-28 | One person many tasks; acceptance rights stay distinct | COVERED | AGENTS.md:52; AGENTS.md:63 | doc only; reviewer is a different role in a fresh session |
| Production Pipeline:29-43 | Fixed product boundaries of the other game | ADAPTED | docs/jam-brief.md:42-61; docs/jam-brief.md:70 | doc only; other game's list replaced by our MVP and Never cut list |
| Production Pipeline:44 | Cut breadth before causal links; no quiet reclassification | COVERED | docs/jam-brief.md:64-71; AGENTS.md:67-68 | doc only; humans approve MVP or cut-list changes |
| Production Pipeline:45-52 | Latest approved version binding; discovery by README | COVERED | AGENTS.md:7-8; docs/gdd/README.md | manifest_check; GDD snapshot named by docs/gdd/CURRENT, never archive |
| Production Pipeline:53-63 | Source families and what each governs | ADAPTED | AGENTS.md:23-28; docs/jam-brief.md:38-40 | doc only; per-subject list, our docs |
| Production Pipeline:64-65 | Never silently upgrade a document's approval status | STRENGTHENED | docs/jam-brief.md:43; AGENTS.md:98 | check_card fails a card whose feature is not implementation_authorized; D-new-p0-signoff answered by GDD 1.3 §2 (a new revision, docs/gdd/README.md:26-28); agents never promote a manifest status |
| Production Pipeline:66-67 | Precedence by subject; evidence reopens, never overrides | COVERED | AGENTS.md:23-31; docs/decisions.md:15 | doc only; reopen needs a new row with a new measurement |
| Production Pipeline:68-73 | Role-switching in one chat is not independent review | COVERED | AGENTS.md:52 | doc only |
| Production Pipeline:74-84 | Function / accountable owner table | ADAPTED | AGENTS.md:33-49; docs/jam-brief.md:83-100 | check_card --people; EP replaced by scope decision-maker and creative director |
| Production Pipeline:85-86 | Decision routing; coordinator never impersonates acceptance | COVERED | AGENTS.md:30-31; AGENTS.md:54; pipeline/roles/producer.md:73 | doc only |
| Production Pipeline:87-90 | Ten-step acceptance state ladder | ADAPTED | AGENTS.md:70 | doc only; four labels plus blocked, cut, superseded |
| Production Pipeline:91-93 | Generated means produced; tested only as far as ran | COVERED | AGENTS.md:74; AGENTS.md:77 | check_pr; pasted output, "Not run" stated |
| Production Pipeline:94 | Art approval does not prove in-engine import | COVERED | pipeline/roles/art-director.md:4; pipeline/roles/art-director.md:38 | sprite_check, art_check on in-engine captures |
| Production Pipeline:95 | Technical acceptance does not prove fun | COVERED | pipeline/roles/qa-build.md:4; pipeline/qa/playtests.md:1 | doc only; cold human playtests |
| Production Pipeline:96-97 | QA does not move decision ownership; gate sign-off reserved | COVERED | pipeline/roles/producer.md:40; pipeline/roles/producer.md:73; docs/decisions.md:12 | gate; scope decision-maker closes gates |
| Production Pipeline:98-99 | Conditional acceptance needs owner, expiry, visibility | STRENGTHENED | pipeline/templates/gate-record.md:29; pipeline/templates/gate-record.md:34 | check_card --gate-record; exception owner + hour, status line repeats it |
| Production Pipeline:100-105 | Milestones are evidence gates, not dates | ADAPTED | pipeline/roles/producer.md:40-47; pipeline/roles/producer.md:62-63 | check_card --clock; DISPUTABLE: ours are clock-timed gates with an automatic cut |
| Production Pipeline:106-115 | M0 to M6 gate table | ADAPTED | pipeline/roles/producer.md:42-47 | check_card --gate-record; four jam gates G1 to G4 |
| Production Pipeline:116 | M7 launch, support, closeout | DROPPED | - | (a) jam ends at submission; lessons go to devlog and retro questions |
| Production Pipeline:117-118 | Listing gates authorizes nothing; no invented targets | COVERED | pipeline/checklists/card-ready.md:5; AGENTS.md:57 | doc only; full cards only for next gate (D-new-port-11) |
| Production Pipeline:119-123 | M0 entry and owners | ADAPTED | pipeline/day0-cards.md:28 | check_card --people; card 0.0 names people and clock |
| Production Pipeline:124-127 | Confirm which baselines are approved | COVERED | pipeline/day0-cards.md:28 | manifest_check; D-new-p0-signoff on card 0.0 |
| Production Pipeline:128 | Verify real environment; never infer repo exists | STRENGTHENED | AGENTS.md:15-17; pipeline/day0-cards.md:47 | required field; CAN RUN line, card 0.9 per-machine smoke |
| Production Pipeline:129 | Mockups vs editable; no bulk-importing screenshots | COVERED | pipeline/art/provenance.csv:2; pipeline/roles/asset-specialist.md:17 | tests/test_provenance.py; reference only, never shipped |
| Production Pipeline:130 | One tracker, one evidence place, no duplicate logs | COVERED | AGENTS.md:19; AGENTS.md:65; pipeline/day0-cards.md:29 | doc only; GitHub is the shared truth |
| Production Pipeline:131 | Narrow experiment briefs with stop rule | STRENGTHENED | pipeline/templates/spike-card.md:9-18 | check_card spike check (Decision row, Decides it, 60 min box) |
| Production Pipeline:132 | Define acceptance package before the stage | COVERED | pipeline/roles/producer.md:42-47; pipeline/templates/gate-record.md | gate |
| Production Pipeline:133-135 | Basic readiness not blocked by unfinished infra | ADAPTED | docs/decisions.md:29 | doc only; D-new-06-block default "no block", unproven checks listed Not checked |
| Production Pipeline:136-140 | Reproducible build, headless tests, clean environment | COVERED | pipeline/day0-cards.md:31; pipeline/day0-cards.md:36; pipeline/roles/qa-build.md:36 | gate; Win/Mac same totals, MustFail, fresh-clone package |
| Production Pipeline:141 | Transaction and save durability spike | DROPPED | - | (a) single-encounter game with no save or economy |
| Production Pipeline:142 | Visual representation spike at gameplay distance | STRENGTHENED | pipeline/day0-cards.md:50 | art_check on style frame; Ella 80-100 px (D-new-port-10) |
| Production Pipeline:143 | Layout access and edit-rollback spike | DROPPED | - | (a) other game's player-edited layout |
| Production Pipeline:144 | Input spike: parity, safe cancellation | ADAPTED | pipeline/checklists/design-review.md:19; pipeline/day0-cards.md:51 | doc only; input conflicts per card, DEC-01 bindings spike; keyboard first |
| Production Pipeline:145 | Numeric budgets from measurement, not intuition | COVERED | pipeline/roles/qa-build.md:30; pipeline/roles/qa-build.md:32 | SMOKE_OK contract in tools/ue_run.py; REF_HOST frame time |
| Production Pipeline:146-147 | Record candidate to Keep/Revise/Cut; escalate contradictions | COVERED | pipeline/templates/spike-card.md:20-26; AGENTS.md:30-31 | doc only; result posted on the decision row |
| Production Pipeline:148-149 | One passing spike never replaces an unrun test | COVERED | pipeline/templates/spike-card.md:21 | doc only; spike branch never merged, normal card rebuilds with tests |
| Production Pipeline:150-154 | First full loop, placeholders allowed | ADAPTED | pipeline/roles/producer.md:44-45 | gate; G1/G2 graybox MVP 1-8 |
| Production Pipeline:155-163 | Nine-step loop of the other game | ADAPTED | docs/jam-brief.md:44-51 | gate; our MVP list replaces it |
| Production Pipeline:164 | Interruption never duplicates consequences | ADAPTED | pipeline/day0-cards.md:40; pipeline/roles/qa-build.md:34 | SMOKE_CYCLE actors/health per restart; no save state to restore |
| Production Pipeline:165-166 | Player explains cause without hidden numbers | COVERED | pipeline/checklists/design-review.md:15; pipeline/qa/playtests.md:7; pipeline/qa/playtests.md:15 | encounter_check --playtest explained=n; owner watches every gate playtest |
| Production Pipeline:167-172 | Slice tests value, look, usability, cadence together | ADAPTED | pipeline/roles/producer.md:46 | gate; G3 full encounter with key-art style |
| Production Pipeline:173-174 | Reproducible from source; video or mockups not evidence | STRENGTHENED | pipeline/roles/qa-build.md:36; pipeline/roles/ui-ux.md:52; AGENTS.md:75 | fresh-clone package before each gate; screenshots show looks only |
| Production Pipeline:175-178 | Continue/Revise/Reduce/Stop before multiplying content | ADAPTED | pipeline/templates/gate-record.md:23 | check_card --gate-record; Pass, Pass with exceptions, Miss then cut |
| Production Pipeline:179-180 | Expand breadth after interfaces stable; tests per system | COVERED | pipeline/roles/producer.md:45; pipeline/checklists/design-review.md:29 | test-map --require; gated features only after MVP 1-8, each alone |
| Production Pipeline:181 | Late stage: new systems need explicit exception | STRENGTHENED | pipeline/roles/producer.md:56 | gate; feature freeze after G3 (D-new-port-12) |
| Production Pipeline:182 | Release: reproducibility, licences, provenance, rollback | ADAPTED | pipeline/checklists/submission.md:24-39; pipeline/roles/qa-build.md:22; AGENTS.md:101 | submission_check zip; itch page instead of storefront, kept zip is rollback |
| Production Pipeline:183-185 | Post-launch patching and support | DROPPED | - | (a) no post-jam patch phase |
| Production Pipeline:186-191 | One lightweight path for all work | COVERED | AGENTS.md:56-69 | doc only |
| Production Pipeline:192-198 | Single record per work item | COVERED | pipeline/templates/task-card.md:3; AGENTS.md:57 | required field; GitHub Task card form |
| Production Pipeline:199-200 | Stable ID, title, parent milestone | COVERED | pipeline/templates/task-card.md:7-9 | check_card; ID, Title, MVP item |
| Production Pipeline:201 | Value, governing contract, approved vs proposed | STRENGTHENED | pipeline/templates/task-card.md:10-16 | check_card fails unauthorized Features and stale GDD revision |
| Production Pipeline:202 | Scope in/out, interfaces, smallest unit | STRENGTHENED | pipeline/templates/task-card.md:23-29 | check_card; File lane, Out of scope, Used by, --lanes |
| Production Pipeline:203 | One owner, named reviewers | COVERED | pipeline/templates/task-card.md:17-19 | check_card; owner role differs from reviewer |
| Production Pipeline:204 | Resource envelope and stop conditions | STRENGTHENED | pipeline/templates/task-card.md:42-44 | check_card --overrun; Budget minutes, Stop if |
| Production Pipeline:205 | Observable acceptance including failure path | STRENGTHENED | pipeline/templates/task-card.md:33-39; pipeline/checklists/card-ready.md:19 | check_card measurable Done-when |
| Production Pipeline:206 | Artifacts and evidence location | COVERED | pipeline/templates/task-card.md:23; pipeline/templates/task-card.md:40 | required field; Outputs, Evidence |
| Production Pipeline:207 | Known risk and blockers | COVERED | pipeline/templates/task-card.md:46 | required field; Unknowns |
| Production Pipeline:208 | Handoff: output, limits, next owner | COVERED | AGENTS.md:86; pipeline/templates/asset-brief.md:27-37; .github/PULL_REQUEST_TEMPLATE.md:29 | check_pr `Next:`; journal export |
| Production Pipeline:209-210 | Compact record for routine work; no paperwork | ADAPTED | AGENTS.md:67-68; pipeline/templates/task-card.md:4 | check_card; every card uses the full form, but needs no approval |
| Production Pipeline:211-214 | Board states; blocked overlay; terminal dispositions | ADAPTED | AGENTS.md:70; AGENTS.md:83-84; pipeline/roles/producer.md:59-60 | doc only; four labels, blocked with cause class, cut/superseded with reason |
| Production Pipeline:215-217 | Ready is not authorization; routine work inherits it | ADAPTED | AGENTS.md:58-59; AGENTS.md:67-68 | check_card; authorization is per feature in the manifest |
| Production Pipeline:218 | Review needs evidence; no inferring tests from logs | COVERED | AGENTS.md:19; AGENTS.md:77 | doc only; re-run any check a handoff claimed |
| Production Pipeline:219-220 | Integrated, validated, accepted, closed are separate | COVERED | AGENTS.md:64; pipeline/templates/task-card.md:57-58; .github/PULL_REQUEST_TEMPLATE.md:3-5 | doc only; human marks done after packaged check (D-new-port-1) |
| Production Pipeline:221-222 | Definition of Ready | STRENGTHENED | pipeline/checklists/card-ready.md:1-22 | check_card |
| Production Pipeline:223-224 | Definition of Done; screenshot or patch is not done | STRENGTHENED | AGENTS.md:72-80 | check_pr evidence header, package evidence |
| Production Pipeline:225-234 | Change classes and their decision routes | COVERED | AGENTS.md:30-31; AGENTS.md:67-68; pipeline/templates/spike-card.md:1-7; docs/decisions.md:17 | doc only |
| Production Pipeline:235-236 | Record binding decisions; keep supersession link | COVERED | docs/decisions.md:16; pipeline/roles/producer.md:16 | doc only; SUPERSEDED rows never deleted |
| Production Pipeline:237-242 | Lanes synchronized inside one integrated package | STRENGTHENED | pipeline/checklists/card-ready.md:20 | check_card; Used by names the follow-up card now |
| Production Pipeline:243-246 | Design lane flow from intent to acceptance | ADAPTED | pipeline/checklists/design-review.md; pipeline/checklists/tuning.md; pipeline/qa/playtests.md | doc only |
| Production Pipeline:247-248 | Design handoff contents; intent tiers; tuning not promise | COVERED | pipeline/checklists/design-review.md:9-35; docs/balance.md:4 | doc only; GDD RULE / DEFAULT / HYPOTHESIS / ILLUSTRATIVE tags |
| Production Pipeline:249-250 | Other game's mandatory design checks | ADAPTED | pipeline/checklists/design-review.md:15-35 | doc only; own checks (cues, blocked path, no feel words) |
| Production Pipeline:250 | Recoverable failure without hidden rubber-banding | PORTED | pipeline/checklists/design-review.md:32 | design-review checkbox (card-ready requires it for rule cards) |
| Production Pipeline:251-254 | Branch, review, tests, merge, verify flow | COVERED | AGENTS.md:60-64 | check_pr; branch protection |
| Production Pipeline:255-256 | Presentation layer never owns authoritative state | ADAPTED | pipeline/unreal/gameplay-code.md:51; pipeline/roles/dev-lead.md:39 | doc only; one writer per fact, Unity terms removed |
| Production Pipeline:257 | One coordinator advances time and order | ADAPTED | pipeline/unreal/gameplay-code.md:20; pipeline/unreal/gameplay-code.md:39 | doc only; Encounter Director owns one state enum |
| Production Pipeline:258 | Validate content IDs; headless scenarios; structured traces | COVERED | pipeline/unreal/gameplay-code.md:35; tools/manifest_check.py:291 | manifest_check, encounter_check |
| Production Pipeline:259 | Test interruption path; rebuild state after restore | COVERED | pipeline/checklists/card-ready.md:19; pipeline/checklists/design-review.md:34; pipeline/roles/qa-build.md:34 | check_card; restart cycles |
| Production Pipeline:260 | Buildable mainline; toggles never posing as complete | COVERED | docs/jam-brief.md:108; pipeline/unreal-rules.md:59; pipeline/templates/task-card.md:13-14 | module_check rule M; FlagsOffBaselineUnchanged, Hook only |
| Production Pipeline:261 | On breakage restore mainline first, keep repro | STRENGTHENED | AGENTS.md:87; pipeline/roles/qa-build.md:52 | main-red.yml opens revert PR (lane_guard) |
| Production Pipeline:262 | Other game's verification program | ADAPTED | pipeline/qa/test-map.md:42 | test-map --require; only seeded replay kept |
| Production Pipeline:263-264 | Minimal tooling policy: protected branch, manifest, smoke | COVERED | AGENTS.md:107-130; pipeline/day0-cards.md:58 | pipeline_check, branch protection card 0.17 |
| Production Pipeline:265-268 | Art lane flow anchor to acceptance | COVERED | pipeline/roles/art-director.md; pipeline/templates/asset-brief.md; pipeline/day0-cards.md:49-50 | art_check, sprite_check |
| Production Pipeline:269-270 | Fix camera and pixel scale before multiplying assets | STRENGTHENED | pipeline/day0-cards.md:50; pipeline/roles/producer.md:54; pipeline/roles/qa-build.md:32 | art_check style frame; CAM_Eval_Stress dense scene |
| Production Pipeline:271-277 | Asset family: function, identity, import, proof | ADAPTED | pipeline/templates/asset-brief.md:6-37; pipeline/roles/asset-specialist.md:42 | sprite_check sidecar; prefixes instead of an asset ID registry |
| Production Pipeline:278-279 | Mockups are not approved production sources | COVERED | pipeline/art/provenance.csv:2; pipeline/roles/asset-specialist.md:17; pipeline/roles/ui-ux.md:52 | doc only |
| Production Pipeline:280-281 | AI art provenance; editable source; decode is not quality | COVERED | AGENTS.md:101; pipeline/roles/asset-specialist.md:42; pipeline/roles/art-director.md:38 | tests/test_provenance.py; art_check; no mandated tool |
| Production Pipeline:282-285 | UX owners; KBM and controller tests; focus; interruptions | ADAPTED | pipeline/roles/ui-ux.md:6; pipeline/ui/accessibility.md:73-85; tools/ue/daily-checklist.md:123 | ui_check, UIFLOW; keyboard-only primary, gamepad only if merged |
| Production Pipeline:286-287 | Localization keys, pseudo-loc, font fallback, currency | ADAPTED | pipeline/day0-cards.md:61; pipeline/ui/accessibility.md:85 | ui_check strings; string table and text scale 200%, no pseudo-loc |
| Production Pipeline:287 | Audio or animation never commits gameplay | COVERED | pipeline/unreal/gameplay-code.md:64; pipeline/roles/audio.md:78 | doc only |
| Production Pipeline:288-291 | QA flow; label developer-tested vs QA-verified | COVERED | pipeline/roles/qa-build.md:48; .github/PULL_REQUEST_TEMPLATE.md:24 | required field; PR template last line |
| Production Pipeline:292-295 | Domain invariant test layer | ADAPTED | pipeline/qa/test-map.md | test-map --require; our rule tests replace other game's invariants |
| Production Pipeline:296 | Integration: seeded deterministic scenarios | COVERED | pipeline/qa/test-map.md:42; pipeline/qa/test-map.md:98 | SameSeedSameEventOrder (QA-08) |
| Production Pipeline:297 | Persistence and fault injection | ADAPTED | pipeline/roles/qa-build.md:30; pipeline/day0-cards.md:39 | daily settings step boots garbage/old ini; SMOKE_FORCE_CRASH |
| Production Pipeline:298 | In-engine play: movement, render, input, perf | COVERED | pipeline/roles/qa-build.md:30-35 | SMOKE_OK contract; display step; frame time |
| Production Pipeline:299 | Scenario and endurance tests | ADAPTED | pipeline/roles/qa-build.md:34; pipeline/roles/qa-build.md:36 | ue_run.py stress-check; restart cycles, repeat 5/5 |
| Production Pipeline:300 | Human playtest for comprehension and causality | COVERED | pipeline/qa/playtests.md:1-15 | encounter_check --playtest; cold players |
| Production Pipeline:301-302 | Test record fields; QA covers only what ran | COVERED | pipeline/roles/qa-build.md:16-17; pipeline/roles/qa-build.md:53 | required field; Not checked list |
| Production Pipeline:303-313 | P0 to P3 severity ladder | COVERED | pipeline/roles/qa-build.md:17-20 | doc only; one priority label per bug |
| Production Pipeline:314-315 | Severity by evidence; no hidden P0/P1 waivers | STRENGTHENED | pipeline/templates/gate-record.md:29; pipeline/templates/gate-record.md:34; pipeline/checklists/submission.md:39 | check_card --gate-record fails Pass with open P0/P1 |
| Production Pipeline:316-321 | Integration build is the measure of progress | COVERED | AGENTS.md:76 | doc only; packaged build measures progress |
| Production Pipeline:322-338 | Proposed repo layout; binaries out of source control | ADAPTED | pipeline/unreal-rules.md:34-45; AGENTS.md:97; pipeline/roles/qa-build.md:22 | pipeline_check junk/LFS; Unreal paths, zips kept outside repo |
| Production Pipeline:339-342 | Merge contract; build ID and hash; state unrun checks | STRENGTHENED | .github/PULL_REQUEST_TEMPLATE.md:14-29; AGENTS.md:79 | check_pr evidence header; BUILD_INFO.txt in package |
| Production Pipeline:343-344 | Per-change-type checks: art, gameplay, UI | COVERED | pipeline/checklists/card-ready.md:22; pipeline/roles/art-director.md:38 | sprite_check, art_check, ui_check ci |
| Production Pipeline:345-346 | Never overwrite verified build or source; archive | COVERED | pipeline/roles/qa-build.md:22; pipeline/roles/asset-specialist.md:42; pipeline/templates/gate-record.md:30 | submission_check zip; gate tags |
| Production Pipeline:347-354 | Five build classes | ADAPTED | AGENTS.md:76; docs/jam-brief.md:7 | doc only; Development package only, PIE is not a build |
| Production Pipeline:355-356 | Build label never implies QA | COVERED | pipeline/roles/qa-build.md:48 | doc only; gate counts only QA-verified |
| Production Pipeline:357-368 | Three planning levels | ADAPTED | pipeline/roles/producer.md:42-47; pipeline/checklists/card-ready.md:5 | doc only; gates, next-gate full cards, ready queue |
| Production Pipeline:369-370 | Kanban flow; reserve review time; AI speed is not capacity | STRENGTHENED | pipeline/roles/producer.md:35; pipeline/roles/producer.md:53 | check_card --queue (D-new-port-3) |
| Production Pipeline:371-374 | Forecast from real hours and review bandwidth | STRENGTHENED | pipeline/checklists/card-ready.md:9; pipeline/templates/asset-brief.md:21-22 | check_card --hours 70% cap (D-new-reserve) |
| Production Pipeline:375-376 | Worse forecast: show assumption, options, owner | ADAPTED | pipeline/roles/producer.md:21; pipeline/roles/producer.md:64 | check_card --status; options narrowed to "Cut proposed" |
| Production Pipeline:376 | Fixed time is not a quality standard | ADAPTED | pipeline/roles/producer.md:64 | doc only; DISPUTABLE: ours says scope moves, not the deadline |
| Production Pipeline:377-384 | Short living status line; archive stale records | STRENGTHENED | pipeline/roles/producer.md:21; pipeline/roles/producer.md:16 | check_card --status; clock.yml every 3 h |
| Production Pipeline:385-388 | Risk record: cause, likelihood, trigger, fallback, review | ADAPTED | docs/jam-brief.md:73-81; pipeline/templates/gate-record.md:22 | check_card --gate-record; trigger/fallback/owner kept, no likelihood |
| Production Pipeline:388 | Do not duplicate one fact in four docs | ADAPTED | docs/jam-brief.md:38-40; AGENTS.md:53 | pipeline_check cross-doc consistency; one source per subject |
| Production Pipeline:389-390 | Stop or reauthorize triggers | COVERED | AGENTS.md:83-91; AGENTS.md:101 | check_card --overrun; same failure twice stops |
| Production Pipeline:391-396 | Confirm receipt; reported is not verified | COVERED | AGENTS.md:19; AGENTS.md:65-66 | check_pr journal; "prepared, not posted" |
| Production Pipeline:397-398 | Update issues; separate verdicts; closure is not acceptance | ADAPTED | pipeline/roles/producer.md:8; AGENTS.md:64; .github/PULL_REQUEST_TEMPLATE.md:3-5 | doc only; labels instead of project fields |
| Production Pipeline:399-402 | Session resource observations and escalation | ADAPTED | pipeline/roles/agent-ops.md:42; pipeline/agent-ops/README.md:42 | prompt_log status cap=OVER; daily token cap, no per-session context reads (c) |
| Production Pipeline:403-410 | Risk table header; save/transaction integrity risk | DROPPED | - | (a) no save or economy |
| Production Pipeline:411 | Nondeterminism: seeded RNG, replay, causal trace | COVERED | pipeline/qa/test-map.md:42; pipeline/unreal/gameplay-code.md:35 | SameSeedSameEventOrder |
| Production Pipeline:412 | Unstable camera/pixel contract | COVERED | pipeline/day0-cards.md:50 | art_check style frame |
| Production Pipeline:413 | Layout path semantics risk | DROPPED | - | (a) other game's layout editing |
| Production Pipeline:414 | Content and animation explosion | STRENGTHENED | docs/jam-brief.md:11; pipeline/checklists/card-ready.md:15 | check_card 60-frame cap |
| Production Pipeline:415 | Systems hide causes; balance feels unfair | ADAPTED | pipeline/qa/playtests.md:15; docs/balance.md:4 | encounter_check --playtest explained=n |
| Production Pipeline:416 | UI pressure and input overload | ADAPTED | pipeline/ui/accessibility.md:70; pipeline/checklists/design-review.md:19 | ui_check; one key per action, input conflicts |
| Production Pipeline:417 | Asset provenance or source loss | COVERED | AGENTS.md:101; pipeline/roles/asset-specialist.md:42 | tests/test_provenance.py |
| Production Pipeline:418 | Unrealistic AI and solo capacity | COVERED | docs/jam-brief.md:81; pipeline/roles/producer.md:53 | check_card --queue |
| Production Pipeline:419 | Platform and publishing obligations | COVERED | docs/jam-rules.md; pipeline/checklists/submission.md | submission_check rules |
| Production Pipeline:420-421 | Risk stays open until evidence accepted | ADAPTED | pipeline/templates/gate-record.md:22 | check_card --gate-record; fired yes/no each gate, no closed state |
| Production Pipeline:422-427 | First assignment: bounded mobilization only | ADAPTED | pipeline/day0-cards.md:28-68 | gate; Day-0 cards, pre-jam vs Nov 12 |
| Production Pipeline:428-435 | Mobilization package: lead, outputs, exit | ADAPTED | pipeline/day0-cards.md:28; pipeline/day0-cards.md:29; pipeline/day0-cards.md:47; pipeline/day0-cards.md:51 | check_card --people, --clock |
| Production Pipeline:436-441 | Burn-down 1: repo, build manifest, test skeleton | COVERED | pipeline/day0-cards.md:31 | check_automation_report |
| Production Pipeline:442 | Burn-down 2: atomic commit and save fixture | DROPPED | - | (a) no save |
| Production Pipeline:443 | Burn-down 3: camera/pixel/art anchor | COVERED | pipeline/day0-cards.md:50 | art_check |
| Production Pipeline:444 | Burn-down 4: layout fixture | DROPPED | - | (a) other game's layout editing |
| Production Pipeline:445 | Burn-down 5: input and modal fixture | ADAPTED | pipeline/day0-cards.md:62; pipeline/ui/accessibility.md:76 | MenuBlocksGameplayInput test; UIFLOW |
| Production Pipeline:446 | Burn-down 6: next slice breakdown | COVERED | pipeline/checklists/card-ready.md:5; pipeline/roles/producer.md:31 | doc only |
| Production Pipeline:447-448 | Limits: attempts, retention, escalation trigger | COVERED | pipeline/templates/task-card.md:42-44; AGENTS.md:90; pipeline/templates/asset-brief.md:21-22 | check_card; no round cap, stuck after 3 flat rounds (D-new-no-round-cap) |
| Production Pipeline:449-450 | Explicit exclusions until authorized | COVERED | docs/jam-brief.md:60; pipeline/roles/producer.md:54; pipeline/roles/producer.md:76 | check_card --lanes (no stretch while MVP is open) |
| Production Pipeline:451-452 | Short gate report format | STRENGTHENED | pipeline/templates/gate-record.md:7-24 | check_card --gate-record; no "actual resources" line |
| Production Pipeline:453-461 | Gate packet: baseline and outputs | COVERED | pipeline/templates/gate-record.md:8-10 | check_card --gate-record |
| Production Pipeline:462 | Each discipline's acceptance named by owner | PORTED | pipeline/templates/gate-record.md:21; tools/check_card.py | `--gate-record`: Verdicts slots, fail blocks Pass (GateRecord tests) |
| Production Pipeline:463 | Quality: regression, P0/P1, P2 exceptions | STRENGTHENED | pipeline/templates/gate-record.md:13-16 | check_card --gate-record |
| Production Pipeline:464 | Forecast: cost vs envelope, risk change | ADAPTED | pipeline/templates/gate-record.md:8; pipeline/templates/gate-record.md:17 | check_card --gate-record; late-by hours, cut fired |
| Production Pipeline:465 | Seven gate outcomes | ADAPTED | pipeline/templates/gate-record.md:23 | check_card --gate-record; three outcomes |
| Production Pipeline:466-467 | Close only on exit criteria; failure kept as evidence | STRENGTHENED | pipeline/templates/gate-record.md:34; pipeline/checklists/card-ready.md:5; pipeline/templates/spike-card.md:24 | check_card --gate-record |
| Production Pipeline:468-469 | Escalation order; no exec review of routine fixes | COVERED | AGENTS.md:30-31; AGENTS.md:54; AGENTS.md:67-68; docs/decisions.md:17 | doc only |
| Production Pipeline:470-475 | Handoff before closure; missing evidence blocks only its claim | COVERED | pipeline/templates/task-card.md:57-58; AGENTS.md:88; pipeline/roles/qa-build.md:41 | check_card --blocked-by |
| Production Pipeline:476-481 | Controlled publication record | DROPPED | - | (b) document approval bureaucracy |
| Production Pipeline:482-483 | Never mark approved from upload or authorship | COVERED | AGENTS.md:98; docs/decisions.md:12 | doc only |
| Production Pipeline:484-485 | Stable filename; history kept; status not in doc revisions | ADAPTED | pipeline/roles/producer.md:16; pipeline/roles/producer.md:20-21 | doc only; git history plus Superseded banner, status on tracker |
| Production Pipeline:486-487 | Pipeline review triggers incl. repeated workflow failure | PORTED | pipeline/templates/gate-record.md:19; tools/check_card.py | `--gate-record`: Process change needs #n + owner or none |
| Production Pipeline:488-489 | Success = integrated playable advance or decisive evidence | COVERED | pipeline/roles/producer.md:42; pipeline/templates/spike-card.md:24 | gate |
| Production Pipeline:490-507 | Work package brief template | COVERED | pipeline/templates/task-card.md:6-47; pipeline/checklists/card-ready.md:6 | check_card |
| Production Pipeline:508-522 | Technical or art evidence card | COVERED | pipeline/templates/spike-card.md:9-25 | check_card spike check |
| Production Pipeline:523-530 | Gate decision record: scope, outputs, tests | STRENGTHENED | pipeline/templates/gate-record.md:7-16 | check_card --gate-record |
| Production Pipeline:531 | Record lists Design/Art/Technical acceptances | PORTED | pipeline/templates/gate-record.md:21; tools/check_card.py | `--gate-record`: Verdicts slots, fail blocks Pass (GateRecord tests) |
| Production Pipeline:532-536 | Defects, exceptions, forecast, decision, next action | ADAPTED | pipeline/templates/gate-record.md:13; pipeline/templates/gate-record.md:17-23; pipeline/templates/gate-record.md:29 | check_card --gate-record; next action is the "change for next gate" line |
| Production Pipeline:537-548 | Origin of each control | DROPPED | - | no rule content |
| Production Pipeline:549-550 | Plain list of what is not yet proven | COVERED | docs/audit.md:111-121 | doc only |

### inherited: Producer charter

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Producer charter:1-16 | Title, version, status, approval metadata | DROPPED | - | no rule content |
| Producer charter:18-20a | Producer is not a mandatory checkpoint for all work | COVERED | AGENTS.md:67-68; pipeline/roles/producer.md:3 | doc only |
| Producer charter:20b | Challenge unsound commitments, protect player experience | ADAPTED | AGENTS.md:133; pipeline/roles/producer.md:21 | doc only; challenge becomes Unknowns format + "will miss" status (see PC:97) |
| Producer charter:20c | Help departments without taking their decisions | COVERED | pipeline/roles/producer.md:3; pipeline/roles/producer.md:75-77 | doc only |
| Producer charter:22a | Producer owns plan, sequence, capacity, risk, acceptance, comms | COVERED | pipeline/roles/producer.md:6-11 | doc only |
| Producer charter:22b | Producer works hands-on (writes plans, cards) | COVERED | pipeline/roles/producer.md:18-24 | check_card.py (cards), --tracker, --gate-record |
| Producer charter:22c | Direct tools only through real mechanisms | COVERED | AGENTS.md:65-66 | doc only |
| Producer charter:22d | Preserve continuity, improve methods on evidence | COVERED | AGENTS.md:86; pipeline/templates/gate-record.md:31 | journal.py; check_card.py --status (What slowed us) |
| Producer charter:24 | Success = accepted outcomes, not reports produced | STRENGTHENED | pipeline/roles/producer.md:21,23 | check_card.py --tracker (gate counts only `passed`) |
| Producer charter:30-32 | Independent judgment; evidence over preference or seniority | ADAPTED | AGENTS.md:133; docs/decisions.md:15 | doc only; options with a lean, rows reopen only on measurement |
| Producer charter:36a | Long expertise list across disciplines | DROPPED | - | no rule content |
| Producer charter:36b | Do not presume every discipline is used | ADAPTED | AGENTS.md:50 | doc only; start with 4 roles, add others when cards need them |
| Producer charter:38-40 | Create plans; delegation keeps Producer accountable | COVERED | pipeline/roles/producer.md:18-24,70 | doc only (every blocked card has next owner) |
| Producer charter:42-44 | Verify project requirements before committing; no assumptions | ADAPTED | AGENTS.md:5-14 | doc only; ours is project-specific, fixed read order replaces discovery |
| Producer charter:48 | Creative intent before scheduling | COVERED | pipeline/templates/task-card.md:16; .github/ISSUE_TEMPLATE/task.yml:23-24 | required field (Player outcome) |
| Producer charter:49 | Reduce breadth before sacrificing essential quality | COVERED | docs/jam-brief.md:64-71; pipeline/roles/producer.md:54 | doc only (cut list order, Never cut, frames before states) |
| Producer charter:50 | Evidence before confidence | STRENGTHENED | AGENTS.md:72-80 | check_pr.py (evidence header, "all good" fails) |
| Producer charter:51 | Sustainability: rework, review capacity, human limits | STRENGTHENED | pipeline/checklists/card-ready.md:9-13 | check_card.py --hours (70% reserve), --queue |
| Producer charter:52 | Task completion is not accepted value | COVERED | pipeline/roles/producer.md:23 | check_card.py --tracker |
| Producer charter:53 | Least process that protects decisions | ADAPTED | AGENTS.md:67-68 | doc only; routine card work needs no approval, but process is check-heavy |
| Producer charter:54 | Challenge, then support the authorized decision | COVERED | docs/decisions.md:15 | doc only |
| Producer charter:55 | Disclose unknowns, defects, actual state | STRENGTHENED | AGENTS.md:75-76; .github/PULL_REQUEST_TEMPLATE.md:26-29 | check_pr.py (Not done lines need links, Next:) |
| Producer charter:56 | Fix recurring system failures, not more effort | STRENGTHENED | AGENTS.md:84,89; pipeline/templates/gate-record.md:31 | check_card.py --status fails without What slowed us questions |
| Producer charter:62-64 | Executive owns scope/strategy; Producer never enlarges bounds | COVERED | AGENTS.md:67-68; pipeline/roles/producer.md:40,73 | gate (scope decision-maker closes gates) |
| Producer charter:66a | Four actions: Recommend / Decide / Initiate / Commit | ADAPTED | AGENTS.md:67-68; docs/decisions.md:6 | doc only; replaced by "agents never decide, humans approve this short list" |
| Producer charter:66b | Brief, tool result or silence is not approval | ADAPTED | docs/decisions.md:6,12; AGENTS.md:63,92 | doc only; DISPUTABLE: ours builds the row's default while undecided; approval = owner edit from own account or human merge |
| Producer charter:68-70a | Production sets sequence; specialists own methods and acceptance | COVERED | AGENTS.md:33-48; pipeline/roles/art-director.md:48 | doc only |
| Producer charter:70b | Department head assigns routine work without Producer | ADAPTED | AGENTS.md:57; pipeline/roles/producer.md:7,18 | check_card.py; DISPUTABLE: all cards pass the Producer's readiness check |
| Producer charter:70c | Notification is not a new approval gate | COVERED | AGENTS.md:67-68 | doc only |
| Producer charter:72a | Production never decides gameplay, art, architecture, QA | COVERED | pipeline/roles/producer.md:3,75,77 | doc only |
| Producer charter:72b | One decision owner set before a decision binds | STRENGTHENED | docs/decisions.md:8,21; pipeline/templates/task-card.md:17-19 | pipeline_check.py (owner must be a People seat); check_card.py (owner ≠ reviewer, Human) |
| Producer charter:72c | Coordinate, never impersonate another discipline | STRENGTHENED | AGENTS.md:9,51,62 | agent hook blocks writes without JAM_ROLE; `ROLE:` prefix |
| Producer charter:74-89 | Delegated decision matrix (12 rows) | ADAPTED | AGENTS.md:67-68; pipeline/roles/producer.md:40,72-77; pipeline/submission/itch-page.md:3 | doc only; matrix rejected (port-log), kept as a short human-approval list; release go/no-go = packaging owner |
| Producer charter:93a | Materiality judged by impact, not thresholds | ADAPTED | AGENTS.md:67-68 | doc only; DISPUTABLE: ours is a fixed list of what humans approve |
| Producer charter:93b | Routine ambiguity must not stop work | COVERED | AGENTS.md:30-31,87 | check_card.py --blocked-by (only dependents wait) |
| Producer charter:97a | Challenge weak estimates, hidden deps, misleading status | ADAPTED | pipeline/roles/producer.md:21,64; pipeline/checklists/card-ready.md:9 | check_card.py --status, budget caps; challenge made mechanical |
| Producer charter:97b | Challenge states concern, evidence, alternatives, recommendation | COVERED | AGENTS.md:133; docs/decisions.md:21 | required field (Unknowns, decision row columns) |
| Producer charter:97c | After decision: support it, reopen only on new evidence | COVERED | docs/decisions.md:15-16 | doc only |
| Producer charter:101-109 | Seven distinct acceptance states | ADAPTED | AGENTS.md:63,69; pipeline/roles/dev-lead.md:20; .github/PULL_REQUEST_TEMPLATE.md:24; pipeline/templates/gate-record.md | check_pr.py; labels + reviewer verdict + evidence label + gate record replace 7 states |
| Producer charter:111 | Only applicable reviews; no ceremonial sign-offs | COVERED | pipeline/templates/task-card.md:18; AGENTS.md:64 | required field (Reviewer role) |
| Producer charter:115 | Keep valid specialist evidence when another gate fails | COVERED | AGENTS.md:64; pipeline/roles/art-director.md:48 | doc only (only the failed reviewer re-reviews) |
| Producer charter:117a | Reviewer disagreement: clarify authority, get evidence, escalate | ADAPTED | pipeline/roles/dev-lead.md:50; AGENTS.md:54 | doc only; disputes need pasted output; ties go to D34 / scope owner |
| Producer charter:117b | Settle acceptance owner before approving | STRENGTHENED | pipeline/templates/task-card.md:17-19 | check_card.py (Reviewer role + Human required) |
| Producer charter:121 | Conditional acceptance: owner, target, non-waivable intact | STRENGTHENED | pipeline/templates/gate-record.md:29; docs/jam-brief.md:70 | check_card.py --gate-record; status line repeats open exceptions |
| Producer charter:123 | Done tasks with unmet exit criteria don't close milestone | STRENGTHENED | pipeline/templates/gate-record.md:34 | check_card.py --gate-record fails Pass while an MVP item fails |
| Producer charter:129a | Loop Discover → … → Learn | ADAPTED | pipeline/templates/spike-card.md:25; AGENTS.md:56-70 | doc only; card flow + spike Keep/Revise/Cut |
| Producer charter:129b | Do not impose fixed methodology or cadence | ADAPTED | pipeline/roles/producer.md:26-38 | check_card.py --status, clock.yml; DISPUTABLE: ours fixes a daily cadence for a 4-day jam |
| Producer charter:131 | Cadence scales with risk; routine status brief | ADAPTED | pipeline/roles/producer.md:21,32 | check_card.py --status; one-line status, every 3 h clock |
| Producer charter:137a | Work breakdown only as deep as useful | STRENGTHENED | pipeline/checklists/card-ready.md:9 | check_card.py (agent >120 / human >60 min = split) |
| Producer charter:137b | Work item: purpose, owner, scope, dependency, outcome, acceptance | STRENGTHENED | pipeline/templates/task-card.md:6-46 | check_card.py (empty field fails) |
| Producer charter:137c | Effort ≠ duration; include review, integration, rework | ADAPTED | pipeline/templates/task-card.md:42; pipeline/checklists/card-ready.md:20 | check_card.py --hours; agent + human minutes, integrator follow-up counted |
| Producer charter:137d | Ranges and confidence over fake precision | ADAPTED | pipeline/templates/task-card.md:42 | check_card.py; DISPUTABLE: single-number budgets, overrun rule handles error |
| Producer charter:141a | Plan on real people, review bandwidth, compute | STRENGTHENED | docs/jam-brief.md:102-105; pipeline/roles/producer.md:53; pipeline/agent-ops/README.md:117-126 | check_card.py --hours, --queue; prompt_log.py status (daily_token_cap) |
| Producer charter:141b | Map dependencies; find critical-path blockers early | STRENGTHENED | AGENTS.md:88; pipeline/roles/producer.md:22 | check_card.py --blocked-by; blocked-report.yml |
| Producer charter:141c | Nominal agent availability is not throughput | COVERED | pipeline/roles/producer.md:53; docs/decisions.md:85 | check_card.py --queue (D-new-port-3) |
| Producer charter:145a | Forecast with confidence words, not invented numbers | ADAPTED | pipeline/roles/producer.md:21 | check_card.py --status; on track / at risk / will miss + reason, no date range |
| Producer charter:145b | Risk: cause, likelihood, impact, owner, mitigation, trigger | ADAPTED | docs/jam-brief.md:73-81; pipeline/templates/gate-record.md:22 | check_card.py --gate-record (each risk fired yes/no); no likelihood/impact columns |
| Producer charter:145c | Track an issue separately from a risk | COVERED | pipeline/roles/producer.md:21 | check_card.py --status (Blockers field) |
| Producer charter:145d | Surface forecast change early | STRENGTHENED | pipeline/roles/producer.md:64 | check_card.py --status fails "will miss" without Cut proposed |
| Producer charter:149 | Change: update only affected records | STRENGTHENED | docs/gdd/README.md:18-23 | gdd_impact.py; check_card.py fails cards whose Features changed |
| Producer charter:153-155 | Routine resequencing without executive approval | COVERED | AGENTS.md:67-68,87 | doc only |
| Producer charter:159a | Material change: assess, consult, alternatives, authorize, communicate | ADAPTED | AGENTS.md:30-31,66-67; pipeline/day0-cards.md:60 | doc only; decision row + human approval; theme change via card 0.19 |
| Producer charter:159b | Nothing enters approved scope automatically | STRENGTHENED | AGENTS.md:58-59; pipeline/roles/producer.md:76 | check_card.py (implementation_authorized, Hook only); --lanes (no stretch while MVP is open) |
| Producer charter:159c | Recommend cutting when value doesn't justify cost | COVERED | pipeline/roles/producer.md:62-64 | check_card.py --clock (CUT FIRES), --status |
| Producer charter:163a | Authorization comes from approved plan/card | ADAPTED | AGENTS.md:57-58 | check_card.py; the card is the authorization |
| Producer charter:163b | Irreversible action or other dept's baseline needs authorization | COVERED | AGENTS.md:67-68,97; pipeline/roles/agent-ops.md:43-44 | agent hook (bulk delete, push to main ask a human) |
| Producer charter:163c | Paid commitment needs authorization | PORTED | pipeline/roles/agent-ops.md:73; pipeline/templates/asset-brief.md:17 | doc only; `Spend OK:` link by a named human; brief `Tool:` field |
| Producer charter:165 | Work package fields incl. stop conditions, resource envelope | STRENGTHENED | pipeline/templates/task-card.md:6-46 | check_card.py; no "methods left to specialists" line |
| Producer charter:167a | Distinct states; never infer a later one | ADAPTED | AGENTS.md:70; pipeline/templates/task-card.md:57-58; .github/PULL_REQUEST_TEMPLATE.md:11 | doc only; 4 states + blocked instead of 9 |
| Producer charter:167b | Near limits: stop, compare options, re-authorize | STRENGTHENED | AGENTS.md:89 | check_card.py --overrun (OVERRUN #n, human answers) |
| Producer charter:171a | Milestone: scope, owners, entry/exit criteria, authority | ADAPTED | pipeline/roles/producer.md:40-47; docs/jam-brief.md:29-36 | check_card.py --clock; four gates with pass rules |
| Producer charter:171b | Readiness review: integration, QA, defects, open conditions | STRENGTHENED | pipeline/templates/gate-record.md:7-24 | check_card.py --gate-record |
| Producer charter:171c | Dispositions; only proper authority binds | COVERED | pipeline/templates/gate-record.md:23; pipeline/roles/producer.md:40,73 | gate (scope decision-maker) |
| Producer charter:173a | Slice proves play + pipeline repeatability, not polish | ADAPTED | pipeline/roles/producer.md:44; pipeline/templates/gate-record.md:33; AGENTS.md:74 | --gate-record (packaged, re-downloaded); G1 graybox + style frame card 0.10 |
| Producer charter:173b | Slice: hypotheses, representative content, Keep/Revise/Cut | ADAPTED | pipeline/templates/spike-card.md:25; pipeline/roles/producer.md:54 | doc only |
| Producer charter:173c | Release readiness; release owner holds go/no-go | STRENGTHENED | pipeline/checklists/submission.md; pipeline/submission/itch-page.md:3; AGENTS.md:67-68 | submission_check.py |
| Producer charter:177a | Focused consult: issue, owner, input, deadline | STRENGTHENED | docs/decisions.md:18,21 | pipeline_check.py (owner seat); Blocks column |
| Producer charter:177b | No memo if a talk resolves it | ADAPTED | AGENTS.md:65 | doc only; ours always needs a GitHub record |
| Producer charter:179a | Prepared vs submitted vs acknowledged communication | COVERED | AGENTS.md:66 | doc only ("prepared, not posted") |
| Producer charter:179b | Never fabricate agreement or acceptance | COVERED | AGENTS.md:93; docs/decisions.md:12 | doc only |
| Producer charter:179c | Escalate material conflicts with alternatives only | COVERED | AGENTS.md:30-31,131 | doc only |
| Producer charter:183a | Verify real access, tools, compute, paths, channels | COVERED | AGENTS.md:15-17; pipeline/templates/task-card.md:30 | required field (CAN RUN line, Needs) |
| Producer charter:183b | Specialists own briefs, methods, review | COVERED | AGENTS.md:33-48; pipeline/templates/asset-brief.md | doc only |
| Producer charter:185a | Total effective cost; no variants for own sake | STRENGTHENED | pipeline/templates/asset-brief.md:21,35; pipeline/roles/asset-specialist.md:46; pipeline/agent-ops/README.md:121 | prompt_log.py status (REVIEW >2x median) |
| Producer charter:185b | Review actual outputs, not success messages | COVERED | pipeline/roles/dev-lead.md:27; pipeline/roles/art-director.md:4,38 | gate (review checklist) |
| Producer charter:185c | Revision: defect, impact, fix, protected, criterion | COVERED | pipeline/roles/art-director.md:27-28; pipeline/roles/dev-lead.md:49 | required format (Findings block, Keep unchanged) |
| Producer charter:185d | Failed retries: diagnose brief, tool, requirements, split | COVERED | AGENTS.md:84-85; pipeline/roles/art-director.md:50 | doc only (cause classes) |
| Producer charter:185e | Stop at envelope; no claimed background work | COVERED | AGENTS.md:76,88 | check_card.py --overrun |
| Producer charter:189a | Separate activity, output, acceptance, closure | COVERED | pipeline/roles/producer.md:21; .github/PULL_REQUEST_TEMPLATE.md:24 | check_card.py --status |
| Producer charter:189b | Useful metrics (blocker aging, rework); no vanity | ADAPTED | pipeline/roles/producer.md:21; pipeline/agent-ops/README.md:119-121 | --status, prompt_log.py; no rework or forecast-variance metric |
| Producer charter:191a | Status: accepted, incomplete, blockers, forecast, risks, decisions | STRENGTHENED | pipeline/roles/producer.md:21 | check_card.py --status |
| Producer charter:191b | Correct mistaken claims promptly | COVERED | AGENTS.md:80 | doc only |
| Producer charter:191c | Never imply doc read, test run, agent contacted falsely | ADAPTED | AGENTS.md:66,75; .github/PULL_REQUEST_TEMPLATE.md:20 | check_pr.py; commands and posts covered, "document read" not (see RM:109-111) |
| Producer charter:197a | Find README/authorities, versions; verified baseline | COVERED | AGENTS.md:5-14; docs/gdd/README.md:7 | manifest_check.py (CURRENT) |
| Producer charter:197b | Missing/contradictory sources: gap, owner, safe interim | STRENGTHENED | AGENTS.md:30-31 | pipeline_check.py (row exists, owner seat); default built |
| Producer charter:197c | Newest does not mean approved | STRENGTHENED | docs/gdd/README.md:17 | manifest_check.py authorized; check_card.py |
| Producer charter:197d | Don't reread unchanged documents | ADAPTED | AGENTS.md:5,19 | doc only; DISPUTABLE: ours re-reads card at resume on purpose; limits reads instead |
| Producer charter:199a | Keep decisions and rejected alternatives in existing records | COVERED | docs/decisions.md:12,16 | doc only |
| Producer charter:199b | Decision record fields and status vocabulary | ADAPTED | docs/decisions.md:21,58 | pipeline_check.py; open / DECIDED / SUPERSEDED only |
| Producer charter:199c | No redundant registers | COVERED | pipeline/agent-ops/components.csv:1 | doc only |
| Producer charter:201a | Session end: completion, pending, next owner | STRENGTHENED | AGENTS.md:86 | journal.py; check_pr.py (Journal section) |
| Producer charter:201b | Resume: verify last real state; memory not authoritative | COVERED | AGENTS.md:18-19 | journal.py resume |
| Producer charter:205 | Governance text stays out of reader-facing deliverables | STRENGTHENED | pipeline/checklists/submission.md:60; pipeline/checklists/file-hygiene.md:19 | pipeline_check.py (`ROLE:` in Source/Config fails) |
| Producer charter:207a | Each doc type has its audience; cross-refs only if useful | ADAPTED | AGENTS.md:23-28; docs/jam-brief.md:38-40 | doc only |
| Producer charter:207b | Audit deliverables for audience fit and clarity | ADAPTED | pipeline/submission/itch-page.md; pipeline/checklists/submission.md | submission_check.py page; only shipped page/README |
| Producer charter:207c | Never drop requirements during editorial cleanup | ADAPTED | AGENTS.md:98-99; docs/decisions.md:16 | doc only; shared docs not edited by agents, rows never deleted |
| Producer charter:213a | Curated reference register with verification status | ADAPTED | docs/references.md | doc only; one register for the audit, not per role |
| Producer charter:213b | Unverified items labelled; never imply reviewed | ADAPTED | pipeline/art/style.json:223; pipeline/agent-ops/README.md:105-109 | [VERIFY] tags; tests/test_sprite_check.py |
| Producer charter:213c | External practices advisory unless adopted | COVERED | AGENTS.md:21,27 | doc only |
| Producer charter:215 | Learn to solve observed problems, not trends | ADAPTED | pipeline/templates/gate-record.md:31 | check_card.py --status; What slowed us questions |
| Producer charter:219a | Propose rule changes from repeated problems with evidence | ADAPTED | AGENTS.md:99; docs/decisions.md:15 | doc only; no proposal format, changes go via card + PR |
| Producer charter:219b | No charter edit without approval | COVERED | AGENTS.md:98 | doc only |
| Producer charter:221 | Self-evaluation on 13 criteria, 1-5 scores | DROPPED | - | (b) self-ratings rejected (port-log:42) |
| Producer charter:225 | Producer rules don't bind other departments | ADAPTED | AGENTS.md:1-3 | pipeline_check.py; one shared AGENTS.md is the shared protocol |
| Producer charter:229 | Four response levels; no report for small question | PORTED | pipeline/templates/tracker-table.md:13 | doc only |
| Producer charter:231a | Activation: project, README, owners, limits | STRENGTHENED | AGENTS.md:5-19 | agent hook (no JAM_ROLE = writes blocked) |
| Producer charter:231b | Role labels in one chat aren't independent agents | COVERED | AGENTS.md:52 | doc only |
| Producer charter:231c | No capability: give a truthful portable handoff | COVERED | AGENTS.md:66 | doc only |
| Producer charter:231d | Recommendation format; answer simple questions directly | ADAPTED | AGENTS.md:133 | doc only; Unknowns format replaces Purpose → Next Decision |
| Producer charter:233-237 | Compact restatement; full charter controls | DROPPED | - | no rule content (restates above) |
| Producer charter:239-241 | Closing commitment slogans | DROPPED | - | no rule content |
| Producer charter:243-256 | Document control block | DROPPED | - | no rule content |

### inherited: Technical Development Pipeline

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Technical Development Pipeline:1-12 | Title, owner, status, purpose, acceptance stamps | DROPPED | - | (b) no rule content; version and sign-off stamps |
| Technical Development Pipeline:13 | Label unproven choices; resolve by fixture before relying | STRENGTHENED | pipeline/unreal-rules.md:10-11; pipeline/roles/technical-director.md:41,50; tools/ue/daily-checklist.md:6-10 | `ue_run.py verify-tags`; [VERIFY] tag cleared before dependent card starts |
| Technical Development Pipeline:14-19 | Build one real architecture in slices, no rewrite | ADAPTED | pipeline/day0-cards.md:76-87; pipeline/templates/spike-card.md:21; pipeline/day0-cards.md:69 | doc only; cards build on main in GDD 1.3 §12 order, spikes are thrown away and rebuilt by a normal card, workbench ported in (0.27) |
| Technical Development Pipeline:20-21 | Golden path requirement to accepted milestone; owners approve | COVERED | AGENTS.md:56-68; pipeline/roles/producer.md:40-47 | gate; card, branch, PR, separate reviewer, human merge, scope decision-maker closes gate |
| Technical Development Pipeline:22-33 | Stage table: bootstrap, risk, first playable, MVP, release | ADAPTED | pipeline/roles/producer.md:42-47; pipeline/day0-cards.md:28-69 | gate; stages became Day-0 cards plus G1-G4 with `check_card.py --gate-record` |
| Technical Development Pipeline:34-37 | Stage names are proposals; full scope stays intended | ADAPTED | docs/jam-brief.md:60-71; pipeline/roles/producer.md:62-64 | `check_card.py --clock` CUT FIRES; DISPUTABLE: we cut scope by trigger, scope moves not the deadline |
| Technical Development Pipeline:38 | One authoritative clock; UI never advances state | COVERED | pipeline/unreal/gameplay-code.md:39-40,51-52 | doc only + reviewer (dev-lead.md:38); Encounter Director owns one state UENUM |
| Technical Development Pipeline:39 | One owner per fact; visuals and audio are projections | COVERED | pipeline/unreal/gameplay-code.md:47,51,64; pipeline/roles/dev-lead.md:39 | reviewer checklist #12; module_check rule z for state enums |
| Technical Development Pipeline:40 | All-or-none commands, stable IDs, safe to retry | ADAPTED | pipeline/qa/test-map.md:34,38,40,103 | tests `ProjectileHitsOnce`, `BottomExitBroadcastsOnce`, `RestartTwiceSameState`; no transactions in this game, kept the once-only and retry intent |
| Technical Development Pipeline:41 | Verified hard saves, checkpoints, newest-valid recovery | DROPPED | - | (a) game has no save system; only settings persist (see TDP:462-469) |
| Technical Development Pipeline:42 | Design defines behavior, not engineering heuristics | COVERED | pipeline/roles/gameplay-dev.md:35,50; pipeline/roles/dev-lead.md:38 | reviewer checklist #11; decision row required for new numbers or behavior |
| Technical Development Pipeline:43-44 | Invariant breach is not merge-ready despite tests | COVERED | pipeline/roles/dev-lead.md:46,53; pipeline/unreal/gameplay-code.md:56 | reviewer blocker "broken GDD rule"; numbered INV-n each with a test |
| Technical Development Pipeline:45-57 | Governing references list and their authority | ADAPTED | AGENTS.md:5-13,23-30 | doc only; read order and "which source wins" replace his file list |
| Technical Development Pipeline:58 | Record source revision in work item and build | STRENGTHENED | pipeline/templates/task-card.md:12; pipeline/checklists/card-ready.md:17; pipeline/day0-cards.md:68 | required field `GDD revision:`; `check_card.py` fails a card whose features changed since; RUN line logs `manifest=VER` |
| Technical Development Pipeline:59-71 | Responsibility matrix by discipline | ADAPTED | AGENTS.md:33-54 | doc only; roles table plus tie-break owners (D34, scope decision-maker) |
| Technical Development Pipeline:72 | Who decides what; one chat is not independent review | COVERED | AGENTS.md:52,63; pipeline/roles/gameplay-dev.md:35 | doc only; reviewer must be a different role in a fresh session |
| Technical Development Pipeline:73-76 | Hard scope: single-player, one platform first | ADAPTED | docs/jam-brief.md:6-8 | doc only; Windows Development package, single-screen encounter |
| Technical Development Pipeline:77 | Explicit list of things never built in v1 | ADAPTED | docs/feature-manifest.json:77; docs/jam-brief.md:60-71; pipeline/templates/task-card.md:27 | `manifest_check.py` (REJECTED status); required field `Out of scope` |
| Technical Development Pipeline:78 | Projection, renderer, pixel scale are evidence decisions | COVERED | docs/decisions.md:27-28,92; pipeline/day0-cards.md:50 | spike cards D4, D13; card 0.10 confirms Pixels Per Unreal Unit |
| Technical Development Pipeline:79 | Sequencing is not scope removal | ADAPTED | docs/jam-brief.md:60-71 | DISPUTABLE: stretch items are cut first by a fixed cut list |
| Technical Development Pipeline:80-85 | Separate "default" from "locked" choices | COVERED | docs/decisions.md:6,11-18 | doc only; "Default until decided", DECIDED only after posted test result |
| Technical Development Pipeline:86-89 | Pin exact engine patch; no upgrade for preference | STRENGTHENED | AGENTS.md:102; pipeline/roles/technical-director.md:42; tools/secrets_check.py:19-23 | `secrets_check.py --rules components --build-version`; every machine posts `Build.version` (card 0.9) |
| Technical Development Pipeline:90-91 | Game rules in engine-free testable code | ADAPTED | pipeline/unreal/gameplay-code.md:27-28; pipeline/unreal/cpp-rules.md:18 | rule tests without a world; plain rule functions instead of separate assemblies |
| Technical Development Pipeline:92 | Semantic input actions with KBM and controller maps | ADAPTED | pipeline/unreal/cpp-rules.md:23 | module_check rule u (no raw key polling); Enhanced Input instead of Unity Input System |
| Technical Development Pipeline:93 | Unit, editor and in-game tests plus headless runner | ADAPTED | pipeline/unreal/gameplay-code.md:69-77; pipeline/roles/qa-build.md:37 | `check_automation_report.py`; rule tests, `.World.` tests, packaged client test |
| Technical Development Pipeline:94 | One UI framework and one focus coordinator | COVERED | docs/decisions.md:158; pipeline/unreal/cpp-rules.md:23 | test `MenuBlocksGameplayInput`; D-new-umg plain UMG only |
| Technical Development Pipeline:95 | Rendering choice is an evidence gate shared with Art | COVERED | docs/decisions.md:27-28; pipeline/day0-cards.md:48-50 | spike cards D4, D13; style frame card 0.10 with `art_check.py` |
| Technical Development Pipeline:96 | Navigation graph and replaceable pathfinder | DROPPED | - | (a) single-screen arena, no pathfinding |
| Technical Development Pipeline:97 | Authored data validated into stable-ID runtime registry | ADAPTED | pipeline/day0-cards.md:38,45-46; pipeline/unreal-rules.md:47-60 | `encounter_check.py --data`, `manifest_check.py`; owl data assets and feature IDs |
| Technical Development Pipeline:98 | Versioned save snapshots; not the prefs store | DROPPED | - | (a) no save game |
| Technical Development Pipeline:99 | Git, LFS for binaries, short-lived PR branches | COVERED | AGENTS.md:60-61; .gitattributes:1-25 | `pipeline_check.py` lfs rule |
| Technical Development Pipeline:100 | CI: fast checks apart from engine jobs; local fallback | ADAPTED | AGENTS.md:107-130 | CI runs Python checks; Unreal checks run locally with logs in the PR |
| Technical Development Pipeline:101 | No package without need and source/licence review | STRENGTHENED | AGENTS.md:100; pipeline/roles/technical-director.md:38,61; pipeline/agent-ops/components.csv:2 | `secrets_check.py --rules components` (plugin with no vetted row fails) |
| Technical Development Pipeline:102 | Native audio; middleware only with proven value | COVERED | pipeline/day0-cards.md:34; pipeline/roles/technical-director.md:61 | card 0.4c; no third-party plugin without DECIDED row |
| Technical Development Pipeline:103 | Stable text keys, formatting, pseudolocalization | ADAPTED | pipeline/day0-cards.md:61; tools/ui_check.py:15,75 | `ui_check.py strings`; string table kept, pseudolocale and plurals dropped (one language) |
| Technical Development Pipeline:104 | Trace, inspectors, validation; dev trace never player-facing | ADAPTED | pipeline/unreal/gameplay-code.md:34-35,66; pipeline/checklists/submission.md:60; pipeline/day0-cards.md:67 | module_check rule s (debug cvar dev-only); event log lines with frame/source/target |
| Technical Development Pipeline:105 | Windows x64 smoke first; store behind narrow port | ADAPTED | pipeline/day0-cards.md:33; pipeline/checklists/submission.md:75 | `submission_check.py butler`; itch upload by G1 instead of a store port |
| Technical Development Pipeline:106-107 | No mid-milestone upgrade without evidence and rollback | COVERED | AGENTS.md:102 | doc only; engine never changes during the jam |
| Technical Development Pipeline:108-115 | Use supported CLI; read real help before scripting | COVERED | pipeline/unreal/commands-and-packaging.md:5-8; pipeline/day0-cards.md:31 | card 0.3 pastes which `RunTests` spelling found the tests |
| Technical Development Pipeline:116-118 | Explicit engine version, project, target, output | COVERED | pipeline/unreal/commands-and-packaging.md:5; tools/ue/test.sh:18-21 | wrappers take UE_ROOT and PROJECT; `tests/test_ue_scripts.py` |
| Technical Development Pipeline:119-120 | Noninteractive; no implicit install, upgrade, project swap | COVERED | tools/ue/test.sh:21; AGENTS.md:102 | `-unattended -nopause`; never accept "convert project" prompt |
| Technical Development Pipeline:121 | Verify exit code, result files, artifacts, logs | STRENGTHENED | tools/check_automation_report.py:4-19; pipeline/unreal/commands-and-packaging.md:7,13 | `check_automation_report.py`; `smoke.ps1` contract; test `test_check_automation_report.py` |
| Technical Development Pipeline:122 | Timeouts and cleanup of stalled processes | COVERED | tools/ue_run.py:6,163-202; pipeline/agent-ops/README.md:82 | `ue_run.py run --timeout` kills process group, exit 124; `tests/test_ue_scripts.py` |
| Technical Development Pipeline:123 | Commands live in version-controlled wrappers | COVERED | AGENTS.md:121-123; pipeline/day0-cards.md:15-17 | `tools/ue/*` are gate files |
| Technical Development Pipeline:124 | Validate each run path on same fixtures first | ADAPTED | pipeline/day0-cards.md:31 | card 0.3: Mac and Windows give same `PASS tests=1` on one commit |
| Technical Development Pipeline:125-126 | Tool integrity check is not a build or test pass | COVERED | pipeline/unreal/commands-and-packaging.md:7; AGENTS.md:72-77 | doc only; "exit code of the editor alone proves nothing" |
| Technical Development Pipeline:127-128 | Policy does not authorize creation or install | DROPPED | - | (b) authorization ritual; our cards are the authorization |
| Technical Development Pipeline:129-134 | Record engine patch, IDE, modules, packages | COVERED | pipeline/day0-cards.md:31,47; pipeline/roles/technical-director.md:42 | card 0.9 posts `Build.version` per machine; card 0.3 build logs both OSes |
| Technical Development Pipeline:135 | Git host, permissions, LFS, branch protection, size cost | COVERED | pipeline/day0-cards.md:58; AGENTS.md:103; tools/pipeline_check.py:8,104 | card 0.17 `gh api` paste; `pipeline_check.py` size rule and LFS byte total |
| Technical Development Pipeline:136 | CI runner, commands, retention, security permissions | ADAPTED | .github/workflows/pipeline-checks.yml:84-85; pipeline/day0-cards.md:58 | CI job `checks`; GitHub-hosted runner, no engine in CI |
| Technical Development Pipeline:137 | Qualify commands and failure detection before CI use | STRENGTHENED | pipeline/day0-cards.md:36,39; tools/ue/daily-checklist.md:9-15 | card 0.5 MustFail must print FAIL; `SMOKE_FORCE_CRASH=1` must FAIL; `crash-check` exits 2 with no crash folder |
| Technical Development Pipeline:138 | Build modules, licence, packaging machine configured | COVERED | pipeline/day0-cards.md:28,33 | `check_card.py --people` names packaging machine; card 0.4b packaging [VERIFY] items |
| Technical Development Pipeline:139 | Repeatable project creation, fresh import, init isolation | ADAPTED | pipeline/day0-cards.md:67; pipeline/unreal/gameplay-code.md:77 | card 0.25 README holds repeatable commands; each test passes alone |
| Technical Development Pipeline:140 | Save serializer and write protocol decision | DROPPED | - | (a) no save game |
| Technical Development Pipeline:141 | Spatial graph and pathfinder decision | DROPPED | - | (a) no navigation |
| Technical Development Pipeline:142 | Camera, renderer, pixel scale, sorting, lighting record | COVERED | docs/decisions.md:27-28,92,157; pipeline/unreal/gameplay-code.md:65 | D4, D13, D-new-port-10, D-new-art-light; draw order in one header |
| Technical Development Pipeline:143 | UI framework and input/focus decision | COVERED | docs/decisions.md:35,158 | DEC-01, D-new-umg; test `MenuBlocksGameplayInput` |
| Technical Development Pipeline:144 | Performance budgets set after measured workloads | ADAPTED | docs/decisions.md:137-138,150; pipeline/roles/qa-build.md:32 | smoke contract fps 55 / 33 ms on REF_HOST; DISPUTABLE: numbers fixed up front, changed only by measurement (AGENTS.md:99) |
| Technical Development Pipeline:145-146 | Record candidate, alternatives, fixture, result, disposition | COVERED | pipeline/templates/spike-card.md:9-26 | `check_card.py` spike fields (`Decides it`, `Time box`) |
| Technical Development Pipeline:146 | Do not invent versions, metrics or camera spec | ADAPTED | docs/decisions.md:137-138; AGENTS.md:99 | DISPUTABLE: we state thresholds now and require measured numbers to change them |
| Technical Development Pipeline:147-180 | Proposed repository layout | ADAPTED | pipeline/unreal-rules.md:21-45 | `pipeline_check.py` consistency (paths must exist); Unreal layout and content path table |
| Technical Development Pipeline:181 | Code boundaries enforced by definitions, not folders | STRENGTHENED | pipeline/unreal/cpp-rules.md:5-15 | `module_check.py` rules a-g (no include into another Private/, Build.cs deps) |
| Technical Development Pipeline:181 | Engine caches and local files never committed | STRENGTHENED | .gitignore:1-23; AGENTS.md:97 | `pipeline_check.py` forbidden rule |
| Technical Development Pipeline:181 | Keep stable IDs; no regenerated IDs on move | ADAPTED | pipeline/unreal/cpp-rules.md:39; pipeline/unreal-rules.md:92,95 | CoreRedirects on reflected renames; Fix Up Redirectors, main has zero redirectors |
| Technical Development Pipeline:182-185 | Protected trunk, short-lived named branches, one scene | COVERED | AGENTS.md:60; pipeline/roles/producer.md:19; docs/decisions.md:79 | `check_card.py --lanes` (one open card per `.umap`) |
| Technical Development Pipeline:186 | One coherent change per PR, linked, squash, tagged | STRENGTHENED | .github/PULL_REQUEST_TEMPLATE.md:1-39; AGENTS.md:136-137; pipeline/templates/gate-record.md:30 | `check_pr.py` (task link, evidence header, risks with links) |
| Technical Development Pipeline:187 | Engineering plus TD review; label self-review honestly | COVERED | pipeline/roles/dev-lead.md:10; pipeline/roles/technical-director.md:32; AGENTS.md:52,93 | CODEOWNERS seat (D26); never approve own work |
| Technical Development Pipeline:188 | Minimize hand edits of shared scenes; verify merges | ADAPTED | pipeline/unreal-rules.md:19,91-99,106 | `git lfs lock`; one map owner; asset-change JSON sidecar for review; binary maps cannot merge |
| Technical Development Pipeline:189 | LFS for source art/audio; no builds or logs in git | STRENGTHENED | .gitattributes:1-25; pipeline/unreal-rules.md:43,45 | `pipeline_check.py` lfs, size, forbidden rules |
| Technical Development Pipeline:190 | No secrets in commits; least-privilege CI secrets | STRENGTHENED | tools/secrets_check.py:4-8; .github/workflows/pipeline-checks.yml:84-85; AGENTS.md:103 | `secrets_check.py --rules secret,secretfile` in CI |
| Technical Development Pipeline:190 | No secrets in PR text, comments, artifacts; rotate if exposed | PORTED | pipeline/agent-ops/README.md:114-115; tools/secrets_check.py | `secrets_check.py --text` (TextModeTests); rotate same hour |
| Technical Development Pipeline:191 | Tag each milestone; restore from tag, not by hand | COVERED | pipeline/templates/gate-record.md:30; pipeline/roles/qa-build.md:22; pipeline/roles/integrator.md:18 | gate tag `gate-G<n>`; kept zips `G<n>-<sha>`; revert-first |
| Technical Development Pipeline:192-195 | Asset handoff fields: ID, source, pivot, states, provenance | STRENGTHENED | pipeline/templates/asset-brief.md:6-36; pipeline/art/art-bible.md:89-95 | `sprite_check.py --scan/--import-report`; provenance row hard gate (`tests/test_provenance.py`) |
| Technical Development Pipeline:196-197 | Intake order; bad refs block; placeholders labeled, tracked | STRENGTHENED | pipeline/roles/technical-director.md:30; docs/decisions.md:90; pipeline/checklists/submission.md:52 | editor data validator (unset required ref = error); `pipeline_check.py --release` fails on `_PH` |
| Technical Development Pipeline:198-201 | Content flow: validate, test, fixture smoke, build | ADAPTED | tools/ue/daily-checklist.md:17-30; pipeline/qa/test-map.md:46,106 | daily steps validate, test, package, smoke; test `AllMapsLoad` |
| Technical Development Pipeline:202-203 | Errors block, warnings recorded; reuse semantics across variants | COVERED | tools/ue/daily-checklist.md:25; pipeline/roles/technical-director.md:43; pipeline/roles/gameplay-dev.md:38 | validate step zero `Error:`, warnings recorded; tuning units required; same class, new data asset |
| Technical Development Pipeline:204-213 | Ready needs authorization, tools, capacity, spend limit | STRENGTHENED | pipeline/templates/task-card.md:13-15,30,42; pipeline/checklists/card-ready.md:9,18 | `check_card.py` (features authorized, Budget caps, `--hours`) |
| Technical Development Pipeline:214 | Requirement reference and intended outcome | STRENGTHENED | pipeline/templates/task-card.md:10-16 | required fields `GDD ref`, `Player outcome` (`check_card.py`) |
| Technical Development Pipeline:215 | Owning area, touched interfaces, downstream effects | STRENGTHENED | pipeline/templates/task-card.md:23-29; pipeline/checklists/card-ready.md:20 | required fields `File lane`, `Used by` with follow-up card (`check_card.py`) |
| Technical Development Pipeline:216 | Acceptance with negative paths, tests, evidence owner | STRENGTHENED | pipeline/checklists/card-ready.md:19; pipeline/templates/task-card.md:33-40 | `check_card.py` measurable Done-when; negative case line |
| Technical Development Pipeline:217 | Dependencies in hand; no gameplay guess left to devs | COVERED | pipeline/checklists/card-ready.md:6; pipeline/roles/producer.md:77 | doc only; Inputs exist on main; open design question becomes a decision row |
| Technical Development Pipeline:218 | Spike needs hypothesis, variants, fixture, budget, stop | STRENGTHENED | pipeline/templates/spike-card.md:9-22 | `check_card.py` spike fields, time box at most 60 min |
| Technical Development Pipeline:219-220 | Blocked: return specific question and impact | COVERED | AGENTS.md:30-31,82-83,131 | doc only; decision row with default, blocked cause class |
| Technical Development Pipeline:221-224 | Work loop; tickets small enough to review and revert | COVERED | pipeline/templates/task-card.md:42; AGENTS.md:137 | `check_card.py` budget caps force a split; squash commit reverts alone |
| Technical Development Pipeline:225-250 | PR template: outcome, impact, verification run, not run | STRENGTHENED | .github/PULL_REQUEST_TEMPLATE.md:1-39 | `check_pr.py` fails empty sections, missing evidence header, unlinked risks |
| Technical Development Pipeline:251-254 | Done: no covert scope; ownership direction respected | COVERED | pipeline/roles/dev-lead.md:29,38-39 | reviewer checklist #2, #11, #12; `module_check.py` |
| Technical Development Pipeline:255 | Deterministic tests plus cross-owner, failure, retry cases | STRENGTHENED | pipeline/roles/dev-lead.md:33,41; tools/ue/daily-checklist.md:23-24 | daily `alone` and seeded `shuffle` steps; reviewer #6, #14 |
| Technical Development Pipeline:256 | Update save/migration fixtures on schema or ID change | ADAPTED | pipeline/unreal/cpp-rules.md:39; tools/ue/daily-checklist.md:29 | CoreRedirects on renames; daily `settings` step boots old ini |
| Technical Development Pipeline:257 | Engine integration proven, not only unit tests | COVERED | pipeline/roles/dev-lead.md:33,36; pipeline/roles/integrator.md:35 | reviewer #6 world test, #9 package + `SMOKE_OK` |
| Technical Development Pipeline:258 | Gates pass on integrated branch, not local branch | STRENGTHENED | pipeline/roles/qa-build.md:27; tools/ue/daily-checklist.md:93-98 | `ue_run.py merge-check` (every main commit packaged and smoked) |
| Technical Development Pipeline:259 | Reviewed; no new undisclosed critical warning | STRENGTHENED | pipeline/roles/dev-lead.md:36; tools/ue/daily-checklist.md:26 | daily cook-warning rise fails without `COOK_WARN_DECISION`; new compiler warning = med |
| Technical Development Pipeline:260 | Hand off evidence; verified only for what ran | COVERED | AGENTS.md:72-80; pipeline/roles/qa-build.md:47-48 | evidence labels; `check_pr.py` evidence header |
| Technical Development Pipeline:261-262 | Done, QA-validated, accepted, closed stay separate states | COVERED | pipeline/roles/qa-build.md:48; pipeline/templates/task-card.md:57-58 | evidence labels; gate records count only QA-verified |
| Technical Development Pipeline:263-266 | Change control by owner; failed test yields proposal | COVERED | AGENTS.md:98,99; pipeline/templates/spike-card.md:24-26 | doc only; decision row, never edit GDD snapshot |
| Technical Development Pipeline:267-272 | Local and CI run same commands; reproduce red locally | COVERED | AGENTS.md:107-123 | same `python3 tools/...` commands local and CI |
| Technical Development Pipeline:273-278 | Static gate: scope, secrets, caches, provenance, naming | STRENGTHENED | tools/pipeline_check.py:4-21; tools/secrets_check.py:4-8 | `pipeline_check.py`, `secrets_check.py`, `check_pr.py` lane globs |
| Technical Development Pipeline:279 | Content gate: IDs, references, string keys, units | STRENGTHENED | AGENTS.md:119,123; pipeline/roles/technical-director.md:43 | `manifest_check.py`, `encounter_check.py`, `ui_check.py strings` |
| Technical Development Pipeline:280 | Pure logic compile plus deterministic tests | COVERED | pipeline/unreal/gameplay-code.md:70 | `check_automation_report.py --max-rule-seconds` |
| Technical Development Pipeline:281 | Editor import/compile and editor-side tests | ADAPTED | AGENTS.md:121-122; tools/ue/daily-checklist.md:21,25 | build + DataValidation step |
| Technical Development Pipeline:282 | In-game boot, input, UI smoke tests | ADAPTED | pipeline/unreal/gameplay-code.md:71-73; pipeline/roles/qa-build.md:37 | `.World.` tests; packaged `CLIENT_TESTS=1` |
| Technical Development Pipeline:283 | Build smoke on main and milestones; boot and quit | STRENGTHENED | pipeline/checklists/card-ready.md:22; pipeline/roles/qa-build.md:30 | `smoke.ps1` contract; `check_pr.py` path rule for package evidence |
| Technical Development Pipeline:284 | Machine-readable report; skipped stage never success | STRENGTHENED | tools/ue/daily-checklist.md:75-78; pipeline/roles/qa-build.md:53 | DAILY line `Not checked`; off switch past its gate is a P1 |
| Technical Development Pipeline:285-286 | Fast subset per PR, heavy suites at merge or gate | COVERED | AGENTS.md:107-130; tools/ue/daily-checklist.md:75-104 | daily switches by gate; `check_automation_report.py` fails NotRun |
| Technical Development Pipeline:287-290 | Build carries commit, engine, config, inputs, run steps | ADAPTED | tools/ue_run.py:18; pipeline/unreal/commands-and-packaging.md:11; pipeline/unreal-rules.md:105 | BUILD_INFO.txt (commit, date, config, dirty); no engine version or test-report reference in it |
| Technical Development Pipeline:291-292 | Read installed tool help; flags may change | COVERED | pipeline/unreal/commands-and-packaging.md:8; pipeline/day0-cards.md:33 | card 0.4b clears packaging-flag [VERIFY] tags |
| Technical Development Pipeline:293-315 | Batch-mode test and build command templates | ADAPTED | tools/ue/test.sh:18-21; tools/ue/package.sh:28-31 | `tests/test_ue_scripts.py`; Unreal commands in wrappers |
| Technical Development Pipeline:316-317 | Parse results; missing result fails; prove runner fails | STRENGTHENED | tools/check_automation_report.py:4-19; pipeline/day0-cards.md:36,39 | `check_automation_report.py`; MustFail and forced-crash runs |
| Technical Development Pipeline:318-324 | PR logs; milestone artifact, defects, hash kept | COVERED | pipeline/roles/qa-build.md:22; pipeline/templates/gate-record.md:7-23 | `check_card.py --gate-record`; `submission_check.py zip --gate` |
| Technical Development Pipeline:325 | Release candidate bundle: build, perf, QA, notes | ADAPTED | pipeline/checklists/submission.md:41-48 | `submission_check.py`; record line on tracker |
| Technical Development Pipeline:326 | Producer approves storage cost and term | DROPPED | - | (b) approval step; zips kept outside repo, never overwritten (qa-build.md:21) |
| Technical Development Pipeline:327-330 | Vet external package: source, licence, version, compat | STRENGTHENED | tools/secrets_check.py:19-23; pipeline/agent-ops/components.csv:2 | `secrets_check.py --rules components` |
| Technical Development Pipeline:330 | No ad hoc network downloads | ADAPTED | tools/secrets_check.py:15,71 | `secrets_check.py --rules settings` (curl, wget, web tools denied to agents); build scripts not covered |
| Technical Development Pipeline:330 | AI-written code gets same review, tests, provenance | COVERED | AGENTS.md:63-64,71-79; pipeline/art/art-bible.md:89-95 | reviewer eval `run_reviewer_eval.py`; provenance rows for assets |
| Technical Development Pipeline:331-339 | Workstream table intro; bootstrap added as prerequisite | DROPPED | - | (b) no rule content |
| Technical Development Pipeline:340 | Bootstrap: pinned engine, tests, failing test, fresh clone | COVERED | pipeline/day0-cards.md:31,36,39; pipeline/roles/qa-build.md:36 | cards 0.3, 0.5, 0.6; fresh clone before each gate |
| Technical Development Pipeline:341 | Foundation: one tick source, seeded RNG, typed facts | ADAPTED | pipeline/day0-cards.md:67-69; pipeline/qa/test-map.md:42 | `Workbench.Seed.SameSeedSameOrder`, `SameSeedSameEventOrder` |
| Technical Development Pipeline:342-347 | Transactions, inventory, owner ops, service, recovery, extensions | DROPPED | - | (a) other game's setting and systems |
| Technical Development Pipeline:348 | Presentation work starts parallel once interfaces settle | ADAPTED | pipeline/day0-cards.md:48-50; pipeline/roles/producer.md:54 | style frame card 0.10 before bulk art |
| Technical Development Pipeline:349 | Continuous evidence and stabilization work | COVERED | pipeline/roles/qa-build.md:25-39 | daily build record; gate checks |
| Technical Development Pipeline:350-351 | Visible playable loop early; safe state from start | COVERED | pipeline/roles/producer.md:44; AGENTS.md:76 | G1 = MVP 1-6 in a packaged graybox build |
| Technical Development Pipeline:352-364 | First playable fixture and end-to-end demo steps | ADAPTED | docs/jam-brief.md:42-57 | gate; MVP 1-8 replace his loop steps |
| Technical Development Pipeline:365-366 | First playable: real build, no debug skips, controller | ADAPTED | tools/ue/daily-checklist.md:108-109,123; pipeline/roles/qa-build.md:31 | `ue_run.py playthrough-check`; no debug jump; gamepad only if its stretch merged |
| Technical Development Pipeline:367-370 | MVP gate; test longevity early, not at launch | ADAPTED | pipeline/roles/qa-build.md:34; pipeline/roles/producer.md:45-46 | `SMOKE_RESTART_CYCLES=5`, `ue_run.py stress-check` from G3 |
| Technical Development Pipeline:371-374 | Each new feature shows authority, negative paths, fixtures | ADAPTED | pipeline/unreal-rules.md:47-60; pipeline/qa/test-map.md:20-22 | module_check rule M (flag); flag-off baseline test `FlagsOffBaselineUnchanged` |
| Technical Development Pipeline:375-378 | Release gate; consoles only on authorized milestone | ADAPTED | pipeline/checklists/submission.md:24-39 | `submission_check.py`; consoles dropped (a) |
| Technical Development Pipeline:379-387 | Spikes wait for owner; result is not authority | COVERED | pipeline/templates/spike-card.md:24-26; pipeline/checklists/card-ready.md:8 | doc only; spike never marks a row DECIDED |
| Technical Development Pipeline:388 | Transaction and durability spike | DROPPED | - | (a) no saves or economy |
| Technical Development Pipeline:389 | Layout serviceability spike | DROPPED | - | (a) no player-built layout |
| Technical Development Pipeline:390 | Readability under crowding, camera, sorting spike | ADAPTED | docs/decisions.md:28; pipeline/roles/qa-build.md:32; pipeline/roles/integrator.md:30 | spike D13; `CAM_Eval_Stress` capture at densest cluster |
| Technical Development Pipeline:391 | Input/focus spike across screens | ADAPTED | docs/decisions.md:35; pipeline/unreal/cpp-rules.md:23 | DEC-01 spike; test `MenuBlocksGameplayInput` |
| Technical Development Pipeline:392 | Headless and performance spike | ADAPTED | pipeline/day0-cards.md:67-68; pipeline/roles/qa-build.md:32 | headless rule tests; workbench seed test; `stat unit` on REF_HOST |
| Technical Development Pipeline:393-394 | Spike evidence fields; stop at decisive result | COVERED | pipeline/templates/spike-card.md:9-25 | `check_card.py` spike fields; result line on decision row |
| Technical Development Pipeline:395-398 | Inject interruption at every boundary; assert no duplication | ADAPTED | tools/ue/daily-checklist.md:29,113-125; pipeline/day0-cards.md:39 | `stress-check` (pause, alt-tab, audio device), garbage ini boot, forced crash |
| Technical Development Pipeline:399-400 | Checkpoint cadence only after measurement | DROPPED | - | (a) no checkpoints |
| Technical Development Pipeline:401-406 | Stable test ID per executable requirement | STRENGTHENED | pipeline/qa/test-map.md:1-26 | `check_automation_report.py --test-map` (merged row test missing fails) |
| Technical Development Pipeline:407-410 | Single scheduler, pause no-op, idempotent restart | ADAPTED | pipeline/qa/test-map.md:40,42,103 | `RestartTwiceSameState`, `SameSeedSameEventOrder` |
| Technical Development Pipeline:411 | Save recovery and schema upgrade tests | ADAPTED | pipeline/qa/test-map.md:88; tools/ue/daily-checklist.md:29 | `BadIniFallsBackToDefaults`, `WindowModePersists`; daily `settings` step |
| Technical Development Pipeline:412-413 | Payment and stock conservation tests | DROPPED | - | (a) other game's economy |
| Technical Development Pipeline:414 | Layout validity fixture matrix | DROPPED | - | (a) no player-built layout |
| Technical Development Pipeline:415-419 | Service, guest, market, economy, event tests | DROPPED | - | (a) other game's systems |
| Technical Development Pipeline:420 | KBM/controller parity, focus, UI scale, glyphs | ADAPTED | pipeline/roles/qa-build.md:35; pipeline/qa/test-map.md:71 | display smoke `textpx` at 5 modes; `MenuBlocksGameplayInput`; no pseudolocale |
| Technical Development Pipeline:421 | Visual fixtures, crowd stress, muted audio | COVERED | pipeline/roles/qa-build.md:32,39; pipeline/day0-cards.md:50 | `art_check.py`; `audio_check.py --muted`; `CAM_Eval_Stress` |
| Technical Development Pipeline:422 | Clean clone build, pin, smoke, old-data upgrade | COVERED | pipeline/roles/qa-build.md:30,36 | fresh clone before gate; `SETTINGS_OLD_INI` boot |
| Technical Development Pipeline:423-424 | Invariants over test counts; no coverage percent | COVERED | pipeline/unreal/gameplay-code.md:56; pipeline/roles/dev-lead.md:41 | INV-n tests; getter-only test is a med finding |
| Technical Development Pipeline:425-428 | P0: unlaunchable build, data loss; stop the line | COVERED | pipeline/roles/qa-build.md:18 | priority label; feature merges stop |
| Technical Development Pipeline:429 | P1: core loop broken, essential action fails | COVERED | pipeline/roles/qa-build.md:19; pipeline/checklists/submission.md:39 | zero open P0/P1 at submission; gate needs named exceptions |
| Technical Development Pipeline:430-431 | P2 workaround exists; P3 low impact | COVERED | pipeline/roles/qa-build.md:20 | priority label |
| Technical Development Pipeline:432-433 | Severity by player impact; Not Run never Pass | STRENGTHENED | pipeline/checklists/submission.md:5; tools/check_automation_report.py:8 | `check_automation_report.py` fails any not-run test |
| Technical Development Pipeline:434-437 | Budgets on real hardware; record conditions; no editor FPS | COVERED | pipeline/roles/qa-build.md:32; tools/ue/daily-checklist.md:56-57 | smoke fps contract; REF_HOST; record commit, host, CPU/GPU, length |
| Technical Development Pipeline:438-445 | Design says what; tuning is data; no unreviewed mechanic | COVERED | pipeline/roles/gameplay-dev.md:35-36; docs/decisions.md:76 | D20; `pipeline/checklists/tuning.md`; decision row for new behavior |
| Technical Development Pipeline:446-449 | Agree one golden scene before scaling assets | COVERED | pipeline/day0-cards.md:50; pipeline/roles/producer.md:54; pipeline/roles/art-director.md:45 | card 0.10 style frame with `art_check.py`; D-new-port-9 |
| Technical Development Pipeline:450-453 | Production gives milestones; docs never authorize work | COVERED | AGENTS.md:57-58; pipeline/roles/producer.md:7-23 | "No card, no work"; `check_card.py` |
| Technical Development Pipeline:454-457 | QA matrix; seeding, traces, build ID; QA re-runs fix | COVERED | pipeline/roles/qa-build.md:43-45; pipeline/day0-cards.md:65,68 | bug closes only on rerun on packaged merge commit; harness seed and run log |
| Technical Development Pipeline:458-461 | Escalation packet; no staged multi-agent consensus | COVERED | AGENTS.md:52,63,131 | doc only; unknowns format; separate verdicts per reviewer role |
| Technical Development Pipeline:462-469 | Save version, aliases, upgrade fixture, compatibility set early | ADAPTED | tools/ue/daily-checklist.md:29; pipeline/qa/test-map.md:88; pipeline/unreal/cpp-rules.md:39 | daily `settings` step with last gate's ini; game state not saved |
| Technical Development Pipeline:470-473 | Every change: static checks and impacted tests | COVERED | AGENTS.md:107-119 | CI `checks` job |
| Technical Development Pipeline:474 | Every mainline merge: compile, fast suite, smoke, provenance | STRENGTHENED | pipeline/roles/qa-build.md:27; tools/ue/daily-checklist.md:93-98 | `ue_run.py merge-check` |
| Technical Development Pipeline:475 | Each milestone: demo artifact, summary, dispositions | COVERED | pipeline/templates/gate-record.md:7-34 | `check_card.py --gate-record` |
| Technical Development Pipeline:476 | Release: freeze, rerun all; any change invalidates artifact | COVERED | pipeline/checklists/submission.md:24-39,72; pipeline/roles/producer.md:56 | `submission_check.py zip`; new record for any later commit |
| Technical Development Pipeline:477-480 | Dev inspectors, seed replay; exports hold no secrets | ADAPTED | pipeline/unreal/gameplay-code.md:66; pipeline/day0-cards.md:65,68; docs/decisions.md:34 | `ue.Debug` dev-only (module_check rule s); run log; prompt export redacts secrets |
| Technical Development Pipeline:481-484 | Log debt only when it hurts; owner schedules it | ADAPTED | pipeline/roles/gameplay-dev.md:37 | doc only; debt becomes a linked issue, no debt register |
| Technical Development Pipeline:484 | Upgrades only on purpose with baseline and rollback | COVERED | AGENTS.md:100,101 | doc only; no engine or plugin change during jam without TD decision row |
| Technical Development Pipeline:485-490 | Environment not "ready" until setup is proven | COVERED | AGENTS.md:15-17; tools/ue/daily-checklist.md:7-8 | `CAN RUN` line; DAILY lists `real-engine pipeline` in Not checked |
| Technical Development Pipeline:491-494 | Design and tech docs accepted before milestone | COVERED | docs/decisions.md:45; pipeline/day0-cards.md:28 | D-new-p0-signoff (answered by GDD 1.3 §2); `check_card.py` fails a card whose feature is not implementation_authorized |
| Technical Development Pipeline:495 | Role charters approved for use | DROPPED | - | (b) approval bureaucracy |
| Technical Development Pipeline:496 | Repo access tested: clone, push, PR, restore | COVERED | pipeline/day0-cards.md:47 | card 0.9: each teammate opens a PR, `check_pr.py` passes |
| Technical Development Pipeline:497 | Editor, build support, licence verified on target | COVERED | pipeline/day0-cards.md:31,33,47 | cards 0.3, 0.4b, 0.9 |
| Technical Development Pipeline:498 | Dependency policy, ignore rules, LFS, settings committed | COVERED | .gitignore:1-36; .gitattributes:1-37; pipeline/day0-cards.md:58 | `secrets_check.py --rules gitignore,settings` |
| Technical Development Pipeline:499 | CI runner, credentials, first green run | COVERED | pipeline/day0-cards.md:58; .github/workflows/pipeline-checks.yml:84-85 | card 0.17 branch protection with required `checks` |
| Technical Development Pipeline:500 | First passing deterministic test harness | COVERED | pipeline/day0-cards.md:36 | card 0.5 |
| Technical Development Pipeline:501 | Spikes authorized and assigned with stop conditions | COVERED | pipeline/day0-cards.md:51 | card 0.11; `check_card.py` spike fields |
| Technical Development Pipeline:502 | Shared review fixtures and named acceptance owners | COVERED | pipeline/day0-cards.md:50; docs/jam-brief.md:83-100 | card 0.10; `check_card.py --people` |
| Technical Development Pipeline:503 | Store and console access when scheduled | ADAPTED | pipeline/checklists/submission.md:18 | `submission_check.py butler` by G1; consoles dropped |
| Technical Development Pipeline:504-505 | First action: bootstrap plus foundation spikes; art parallel | ADAPTED | pipeline/day0-cards.md:8-24 | `pipeline_check.py` Day-0 After order |
| Technical Development Pipeline:506-513 | Technical Director disposition statement | DROPPED | - | (b) no rule content; status stamp |
| Technical Development Pipeline:514-515 | Do not stall on unknowns; never present untested as verified | COVERED | docs/decisions.md:6; pipeline/unreal-rules.md:10-11; AGENTS.md:72-80 | build the default; [VERIFY] tags; measured evidence |
| Technical Development Pipeline:516-517 | Owners of exceptions; verification apart from doc acceptance | COVERED | docs/decisions.md:11-18; AGENTS.md:73-74 | doc only; "Done" needs re-runnable output |
| Technical Development Pipeline:518-529 | Cite verified external docs as starting points | ADAPTED | docs/unreal-sources.md; pipeline/unreal-rules.md:11 | `[src: Uxx]` tags; Unity links replaced by Unreal sources |
| Technical Development Pipeline:530-531 | State what was not reproduced or verified | COVERED | AGENTS.md:19,76 | doc only; re-run any check a handoff claimed |

### inherited: Technical Director charter

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Technical Director charter:1-16 | Title, version, approval stamps | DROPPED | - | no rule content |
| Technical Director charter:18-26 | TD is a practicing engineer, not just an approver | ADAPTED | pipeline/roles/technical-director.md:3-15 | doc only; abstract authority became concrete owned files (modules, Config, core headers, tools/ue) |
| Technical Director charter:28-42 | List of expected TD duties | ADAPTED | pipeline/roles/technical-director.md:8-43 | doc only; duties are file ownership plus enforced rules, not a list of virtues |
| Technical Director charter:43 | TD enables execution, does not approve everything | COVERED | .github/CODEOWNERS.example:7; AGENTS.md:67-68 | doc only; CODEOWNERS not live until D26 |
| Technical Director charter:45 | Bounded autonomy, no scope expansion by expertise | COVERED | AGENTS.md:67-68; pipeline/roles/producer.md:76 | check_card --lanes (no stretch while MVP is open) |
| Technical Director charter:51-59 | Success measured by delivered software, not documents | COVERED | AGENTS.md:76; tools/pipeline_check.py:106-116 | pipeline_check word budgets; packaged build is the measure |
| Technical Director charter:61-83 | Areas of expertise list | DROPPED | - | no rule content |
| Technical Director charter:84 | Not every project needs every system | COVERED | pipeline/roles/dev-lead.md:37 | review item 10 (no speculative code) |
| Technical Director charter:86-99 | TD may build spikes, reference code, tools | ADAPTED | pipeline/roles/technical-director.md:22-31; pipeline/templates/spike-card.md:1-26 | doc only; TD hands-on work is skeleton, tools/ue, validator; spikes open to any role |
| Technical Director charter:101 | Own coding must not displace leadership | ADAPTED | pipeline/roles/technical-director.md:59 | doc only; hard rule: TD never writes gameplay features |
| Technical Director charter:103-111 | Charter project-agnostic; read project docs | ADAPTED | AGENTS.md:5-13; pipeline/unreal-rules.md:1 | doc only; ours is project-specific by design, read order names sources |
| Technical Director charter:117-121 | Player experience before technical novelty | STRENGTHENED | pipeline/templates/task-card.md:16 | check_card (Player outcome is a required field) |
| Technical Director charter:123-125 | Prototype uncertain decisions before permanent commitment | STRENGTHENED | pipeline/templates/spike-card.md:1-26; pipeline/checklists/card-ready.md:8 | check_card spike rule (Decision row, Decides it, Time box) |
| Technical Director charter:127-131 | Abstractions only for demonstrated problems | COVERED | pipeline/roles/dev-lead.md:37; pipeline/roles/gameplay-dev.md:30 | review item 10; doc only, no eval case for a speculative interface yet |
| Technical Director charter:133-135 | Account for debugging, testing, maintenance costs | COVERED | pipeline/roles/dev-lead.md:31; pipeline/unreal/gameplay-code.md:50-67 | module_check rules h-L; review item 4 |
| Technical Director charter:137-141 | Design states ownership, interfaces, transitions, errors | COVERED | pipeline/unreal/gameplay-code.md:5-40 | doc only; module_check rule z for state enums |
| Technical Director charter:143 | Examples not mandatory without approval | COVERED | pipeline/templates/task-card.md:11; pipeline/checklists/design-review.md:12 | required field (GDD ref tag ILLUSTRATIVE adds no rule) |
| Technical Director charter:145-147 | Lead decides routine implementation without re-approval | COVERED | AGENTS.md:67-68 | doc only |
| Technical Director charter:149-151 | Challenge unsound assumptions, without obstructing | ADAPTED | AGENTS.md:30-31; AGENTS.md:133 | doc only; challenge is a decision row with a lean, default built meanwhile |
| Technical Director charter:153-155 | Never present untested as validated | STRENGTHENED | AGENTS.md:72-80; docs/decisions.md:6 | check_pr (evidence header, stale SHA); check_automation_report |
| Technical Director charter:157-161 | Least complicated architecture that meets requirements | COVERED | pipeline/roles/dev-lead.md:37; pipeline/roles/gameplay-dev.md:30 | review item 10 |
| Technical Director charter:169-175 | Executives hold final authority; TD still challenges | ADAPTED | AGENTS.md:67-68; docs/decisions.md:17 | doc only; executive is the scope decision-maker and Creative director |
| Technical Director charter:177-187 | Recommend / decide / initiate / commit distinction | ADAPTED | AGENTS.md:67-68; pipeline/roles/technical-director.md:5 | doc only; reduced to "agents draft, humans approve the listed items" |
| Technical Director charter:189 | Prototype or passing test is not authorization | COVERED | pipeline/templates/spike-card.md:21; pipeline/templates/spike-card.md:26; AGENTS.md:63 | doc only; spike branch never merged, human merges |
| Technical Director charter:191-206 | TD ownership list incl. debt strategy | ADAPTED | pipeline/roles/technical-director.md:8-15; .github/CODEOWNERS.example:4-12 | doc only; areas became file paths; debt register rejected (port-log), debt is a linked issue |
| Technical Director charter:208-210 | TD must not absorb lead's implementation work | COVERED | pipeline/roles/technical-director.md:59; .github/CODEOWNERS.example:7 | doc only |
| Technical Director charter:214-233 | Decision-rights table (feasibility, interfaces, debt, QA) | ADAPTED | AGENTS.md:33-54; AGENTS.md:67-68; AGENTS.md:100 | doc only; matrix replaced by role Owns/Never lists and the human-approval list (port-log rejected matrices) |
| Technical Director charter:234 | Release go/no-go: TD recommends, authority decides | COVERED | pipeline/roles/producer.md:40; pipeline/templates/gate-record.md:3; pipeline/templates/gate-record.md:23 | check_card --gate-record |
| Technical Director charter:236-248 | Materiality test for escalation | ADAPTED | AGENTS.md:67-68; AGENTS.md:100; pipeline/roles/dev-lead.md:38 | review item 11; fixed list (new player-facing number, module, plugin, setting, others' work) instead of a judgment test |
| Technical Director charter:250-259 | Exception steps; record material exceptions with owners | COVERED | AGENTS.md:99; AGENTS.md:105; pipeline/templates/gate-record.md:29 | pipeline_check (pragma needs decision row); check_card --gate-record (named exceptions with owner) |
| Technical Director charter:261 | Exception cannot override non-waivable requirement | COVERED | pipeline/roles/technical-director.md:35; pipeline/roles/art-director.md:48 | doc only; tool rule fixed with a test, never waived in a PR |
| Technical Director charter:263-274 | Seven-part dissent format | ADAPTED | AGENTS.md:133; docs/decisions.md:21 | doc only; five fields (decision, why, options with lean, test, choice); authority is the Owner column |
| Technical Director charter:277 | Support final decision; reopen only on new evidence | COVERED | docs/decisions.md:15 | doc only |
| Technical Director charter:281-287 | TD and lead both active, both challenge | ADAPTED | pipeline/roles/dev-lead.md:3-10; pipeline/roles/technical-director.md:3-5 | doc only; lead split into Dev Lead (review) and Gameplay Dev (build) |
| Technical Director charter:289-295 | TD sets constraints, lead decides how | ADAPTED | pipeline/unreal/gameplay-code.md:5-28; pipeline/roles/technical-director.md:11 | doc only; TD writes skeleton and core shell, components filled by Gameplay Dev |
| Technical Director charter:297 | Evidence beats seniority in disputes | COVERED | pipeline/roles/dev-lead.md:50; pipeline/roles/technical-director.md:35 | doc only; dispute by pasted output, answered keep/withdraw |
| Technical Director charter:299-312 | TD review only for boundary-changing PRs | COVERED | .github/CODEOWNERS.example:4-12; pipeline/roles/technical-director.md:32 | doc only; CODEOWNERS not live until D26 |
| Technical Director charter:314-324 | Disagreement steps: evidence, prototype, owner decides, record | COVERED | AGENTS.md:30-31; pipeline/templates/spike-card.md:1-26; docs/decisions.md:11-18 | check_card spike rule; pipeline_check (row exists) |
| Technical Director charter:326 | No role silently ignores a binding decision | COVERED | docs/decisions.md:6; AGENTS.md:98 | doc only |
| Technical Director charter:332-336 | Producer vs TD ownership split | COVERED | pipeline/roles/producer.md:6-11; pipeline/roles/technical-director.md:8-15 | doc only |
| Technical Director charter:338 | Schedule cannot dictate architecture | ADAPTED | AGENTS.md:99; pipeline/roles/producer.md:64 | doc only; schedule pressure cannot weaken a check, scope is cut instead |
| Technical Director charter:340 | TD cannot enlarge scope for nicer architecture | COVERED | AGENTS.md:67-68; pipeline/roles/producer.md:76 | check_card --lanes |
| Technical Director charter:342 | Schedule vs feasibility: reduce scope, resequence | STRENGTHENED | pipeline/roles/producer.md:62-64 | check_card --clock (CUT FIRES), --status (Cut proposed) |
| Technical Director charter:344-359 | Art and TD split; import, sprite, memory budgets | COVERED | pipeline/art/import-rules.md; pipeline/roles/technical-director.md:30; docs/jam-brief.md:11 | sprite_check --import-report; art_check; check_card content caps |
| Technical Director charter:361 | Art-accepted asset may still fail technical acceptance | COVERED | pipeline/roles/art-director.md:48 | sprite_check --import-report --gate; "Art approval never waives them" |
| Technical Director charter:363 | Neither department silently overrides the other | COVERED | pipeline/roles/art-director.md:48; pipeline/roles/gameplay-dev.md:39 | doc only |
| Technical Director charter:365-379 | Design contract vs architecture vs code vs evidence | ADAPTED | pipeline/templates/task-card.md:10-15; docs/feature-manifest.json | manifest_check; check_card (Features authorized); GDD tags replace the four-way split |
| Technical Director charter:381 | Do not invent gameplay formulas or behavior | COVERED | pipeline/roles/gameplay-dev.md:35; pipeline/roles/gameplay-dev.md:50; pipeline/roles/dev-lead.md:38 | review item 11 (decision row in same PR) |
| Technical Director charter:383-391 | QA owns validation; engineering tests are not QA | COVERED | pipeline/roles/qa-build.md:43-48; pipeline/roles/qa-build.md:59 | doc only; evidence labels, gates count QA-verified only |
| Technical Director charter:393-397 | Consult other disciplines; no ceremonial gates | COVERED | AGENTS.md:43-48 | doc only; Audio, UI and UX, Level role cards |
| Technical Director charter:401-409 | Eleven-stage technical lifecycle | ADAPTED | AGENTS.md:56-70 | doc only; card flow todo, doing, review, done |
| Technical Director charter:411-417 | Define problem, requirement, constraints before work | STRENGTHENED | pipeline/templates/task-card.md:8-31 | check_card (empty field fails) |
| Technical Director charter:418 | Record existing system behavior before design | PORTED | pipeline/templates/task-card.md:22; .github/ISSUE_TEMPLATE/task.yml; tools/check_card.py | required card field `Context` (check_card; form test) |
| Technical Director charter:419-422 | Dependencies, quality attributes, owner, evidence needed | STRENGTHENED | pipeline/templates/task-card.md:21-40 | check_card (Inputs, Used by, Human, measurable Done-when) |
| Technical Director charter:424-439 | Compare alternatives on criteria; recommend with tradeoffs | ADAPTED | AGENTS.md:133 | doc only; 2-3 options with a lean; criteria list (reversibility, cost) not kept |
| Technical Director charter:441-445 | Spike: hypothesis, owner, workload, criteria, stop | STRENGTHENED | pipeline/templates/spike-card.md:9-18 | check_card spike (Decides it if/then, Time box at most 60 min) |
| Technical Director charter:447 | Successful prototype does not authorize adoption | COVERED | pipeline/templates/spike-card.md:21; pipeline/templates/spike-card.md:26 | doc only |
| Technical Director charter:449-453 | Lead implements; TD clarifies architecture | ADAPTED | pipeline/roles/gameplay-dev.md:47; pipeline/roles/technical-director.md:59 | doc only; Gameplay Dev asks TD for core changes |
| Technical Director charter:455-457 | Distinguish done, verified, accepted, validated, closed | ADAPTED | AGENTS.md:70; pipeline/roles/qa-build.md:48; pipeline/roles/producer.md:40 | check_pr (evidence label last line); fewer states |
| Technical Director charter:459-461 | Learn from real defects to improve methods | ADAPTED | pipeline/templates/gate-record.md:18; pipeline/templates/gate-record.md:31 | check_card --gate-record (line required); per gate only |
| Technical Director charter:463 | Do not grow docs for transient observations | STRENGTHENED | tools/pipeline_check.py:106-116 | pipeline_check word budgets |
| Technical Director charter:467-471 | TD sets project-appropriate standards | COVERED | pipeline/unreal-rules.md:1-11; pipeline/roles/technical-director.md:14 | module_check |
| Technical Director charter:473-474 | Ownership, dependency direction, interface contracts | STRENGTHENED | pipeline/roles/technical-director.md:35-39 | module_check rules a-g |
| Technical Director charter:475 | State consistency and lifecycle | STRENGTHENED | pipeline/unreal/gameplay-code.md:51-61 | module_check rules z, F, v; eval cases 39, 45, 47 |
| Technical Director charter:476 | Persistence and migration | ADAPTED | pipeline/ui/accessibility.md:54; pipeline/qa/test-map.md:107 | ue_run.py settings step; no save games, only settings persist |
| Technical Director charter:477 | Error handling and failure recovery | COVERED | pipeline/unreal/gameplay-code.md:36; pipeline/unreal/gameplay-code.md:61; pipeline/unreal-rules.md:60 | doc only; review |
| Technical Director charter:478 | Performance budgets and profiling | STRENGTHENED | pipeline/roles/qa-build.md:30; pipeline/roles/qa-build.md:32 | ue_run.py smoke contract (fps, worst_ms) |
| Technical Director charter:479 | Logging and diagnostics | COVERED | pipeline/unreal/gameplay-code.md:62; pipeline/unreal/gameplay-code.md:66 | review; module_check rule s (debug cvar) |
| Technical Director charter:480 | Security and dependency management | STRENGTHENED | tools/secrets_check.py:4-12; AGENTS.md:100-101 | secrets_check; pipeline_check |
| Technical Director charter:481 | Build reproducibility | STRENGTHENED | AGENTS.md:102; pipeline/unreal/commands-and-packaging.md:11; pipeline/roles/qa-build.md:36 | package scripts (dirty tree refusal, BUILD_INFO); fresh-clone package |
| Technical Director charter:482 | Testability and integration | STRENGTHENED | pipeline/unreal/gameplay-code.md:69-78 | check_automation_report (--baseline, --require); test-map |
| Technical Director charter:483 | Platform constraints | COVERED | pipeline/roles/technical-director.md:13; pipeline/roles/technical-director.md:55; pipeline/roles/qa-build.md:35 | daily display step |
| Technical Director charter:484 | Data authoring and asset pipelines | COVERED | pipeline/art/import-rules.md; pipeline/unreal-rules.md:47-60 | sprite_check; art_check; encounter_check |
| Technical Director charter:486 | No universal architecture across projects | ADAPTED | pipeline/unreal-rules.md:13-19 | doc only; one project, one architecture |
| Technical Director charter:488-502 | Technical design document contents | ADAPTED | pipeline/unreal-rules.md:1-109; pipeline/unreal/gameplay-code.md:5-79; docs/decisions.md:20-47 | doc only; no separate design doc; rule files hold ownership, data, events, failure, tests; open questions are decision rows |
| Technical Director charter:503 | Mark approved decisions vs exploratory hypotheses | COVERED | pipeline/unreal-rules.md:10-11; pipeline/roles/technical-director.md:50 | doc only; [VERIFY] tags cleared with a header path or log line |
| Technical Director charter:505-507 | Code example is not a binding requirement | COVERED | pipeline/templates/task-card.md:11; pipeline/checklists/design-review.md:12 | required field (ILLUSTRATIVE tag) |
| Technical Director charter:509-524 | Decision record fields | ADAPTED | docs/decisions.md:11-21 | pipeline_check (cited ID has a row, owner is a People seat); no confidence or affected-systems field |
| Technical Director charter:526 | Routine choices need no decision record | COVERED | AGENTS.md:67-68 | doc only |
| Technical Director charter:528-534 | Classify debt by consequence; coordinate remediation | ADAPTED | pipeline/roles/gameplay-dev.md:37; pipeline/roles/qa-build.md:17-20 | doc only; debt is a linked issue, P0-P3 for bugs; no debt register (port-log) |
| Technical Director charter:536 | Debt work never displaces milestone work | COVERED | pipeline/roles/gameplay-dev.md:37; pipeline/roles/producer.md:56 | doc only; freeze after G3 |
| Technical Director charter:540-542 | Measurable quality attributes | STRENGTHENED | pipeline/roles/qa-build.md:30-35 | ue_run.py smoke contract |
| Technical Director charter:544-546 | Performance: workload, platform, conditions, thresholds | STRENGTHENED | pipeline/roles/qa-build.md:32 | CAM_Eval_Stress, REF_HOST, 16.7 ms in gate record |
| Technical Director charter:548 | No invented universal frame or memory budgets | ADAPTED | pipeline/roles/qa-build.md:30; pipeline/roles/qa-build.md:32 | ue_run.py; budgets are this project's, read on REF_HOST |
| Technical Director charter:550 | Profile before prescribing optimization | COVERED | pipeline/roles/dev-lead.md:42 | review item 15 (before/after stat unit) |
| Technical Director charter:552-554 | Reliability: failure states, recovery, determinism | STRENGTHENED | pipeline/roles/qa-build.md:29; pipeline/roles/qa-build.md:34; pipeline/roles/qa-build.md:36; pipeline/unreal/gameplay-code.md:73 | daily (seeded shuffle, restart cycles, repeat 5/5); fixed-delta sweep |
| Technical Director charter:556 | Critical failures diagnosable, recovery documented | COVERED | pipeline/unreal/gameplay-code.md:36; pipeline/unreal/gameplay-code.md:61; pipeline/roles/qa-build.md:30 | smoke crash folder and SMOKE_BAD counts |
| Technical Director charter:558-562 | Security and privacy, even single-player | STRENGTHENED | tools/secrets_check.py:4-12; tools/prompt_log.py:21; docs/decisions.md:34; pipeline/roles/qa-build.md:30 | secrets_check; boot with garbage settings ini |
| Technical Director charter:564-568 | Build and toolchain integrity | STRENGTHENED | AGENTS.md:102; AGENTS.md:110; pipeline/unreal/commands-and-packaging.md:11 | pipeline_check; CI; package script refusals |
| Technical Director charter:572-574 | AI work held to same standards | COVERED | AGENTS.md:1-140 | all gates |
| Technical Director charter:576-597 | TD vs lead delegation split; no long chains | ADAPTED | pipeline/roles/producer.md:6-11; AGENTS.md:52; AGENTS.md:66 | doc only; Producer files all cards, humans start sessions, one session one role |
| Technical Director charter:599-612 | Check authorization, access, paths, criteria before work | STRENGTHENED | AGENTS.md:15-17; pipeline/templates/task-card.md:21-47 | check_card; CAN RUN line |
| Technical Director charter:614 | No assumed agent-to-agent comms or persistence | COVERED | AGENTS.md:65-66 | doc only |
| Technical Director charter:616-634 | Technical assignment brief template | STRENGTHENED | pipeline/templates/task-card.md:6-47; .github/ISSUE_TEMPLATE/task.yml | check_card |
| Technical Director charter:636 | Small tasks get concise instructions | ADAPTED | pipeline/templates/task-card.md:4; pipeline/checklists/card-ready.md:5 | check_card; DISPUTABLE: every card fills every field ("none" allowed); only later-gate items may be one-line placeholders |
| Technical Director charter:638-651 | Patch is not accepted software; evidence list | STRENGTHENED | AGENTS.md:73-79; .github/PULL_REQUEST_TEMPLATE.md:14-29 | check_pr (evidence header, stale SHA, Not run reason) |
| Technical Director charter:653 | No claimed execution, commits, acceptance without proof | STRENGTHENED | AGENTS.md:76; AGENTS.md:86 | check_pr; journal export |
| Technical Director charter:655-664 | Delegated failure: stop, preserve, diagnose, re-authorize | COVERED | AGENTS.md:83-89 | check_card --overrun; journal checkpoint |
| Technical Director charter:666 | Unlimited retries are not a strategy | STRENGTHENED | AGENTS.md:83; AGENTS.md:90; pipeline/templates/task-card.md:44 | check_card --overrun; stop after same failure twice |
| Technical Director charter:670-688 | Seven acceptance states | ADAPTED | AGENTS.md:70; pipeline/roles/qa-build.md:48; pipeline/templates/gate-record.md:23 | check_pr evidence label; four card states, three evidence labels, gate outcome |
| Technical Director charter:690-703 | Technical acceptance criteria list | COVERED | pipeline/roles/dev-lead.md:27-45 | reviewer eval (run_reviewer_eval) |
| Technical Director charter:705 | TD may reject on unmet technical requirements | COVERED | pipeline/roles/technical-director.md:32 | doc only |
| Technical Director charter:709 | Keep one discipline's evidence when another rejects | COVERED | AGENTS.md:64 | doc only; only the failed reviewer re-reviews |
| Technical Director charter:711 | Conditional acceptance explicit, owned, traceable | STRENGTHENED | pipeline/templates/gate-record.md:23; pipeline/templates/gate-record.md:29 | check_card --gate-record |
| Technical Director charter:713 | Technical exception cannot waive another's requirement | COVERED | pipeline/roles/art-director.md:48 | doc only |
| Technical Director charter:717-730 | Focused consultation fields | ADAPTED | AGENTS.md:31; docs/decisions.md:18-21 | pipeline_check (ID, owner); row fields Why, Default, Owner, Blocks |
| Technical Director charter:732 | Prepared / submitted / response / resolved states | ADAPTED | AGENTS.md:66 | doc only; two states ("prepared, not posted" vs posted); rows open or DECIDED |
| Technical Director charter:734 | Portable handoff when no direct channel | COVERED | AGENTS.md:66 | doc only |
| Technical Director charter:736 | Never fabricate consultation or approval | COVERED | docs/decisions.md:12; AGENTS.md:64 | doc only; owner edits row from own account |
| Technical Director charter:742-750 | Session start: project, authority, decisions, repo state | COVERED | AGENTS.md:5-19 | journal resume; first-output lines |
| Technical Director charter:751-752 | Open defects and last verified baseline | ADAPTED | pipeline/roles/gameplay-dev.md:28; pipeline/roles/qa-build.md:18 | doc only; baseline is the card's build run before first edit; no explicit read of open P0/P1 at start |
| Technical Director charter:754 | Latest file is not necessarily approved | COVERED | AGENTS.md:7 | doc only; docs/gdd/CURRENT names the snapshot |
| Technical Director charter:756 | Missing or contradictory material: find owner, don't invent | COVERED | AGENTS.md:30-31 | pipeline_check (cited decision has a row) |
| Technical Director charter:758 | Conversation memory is not authority | COVERED | AGENTS.md:19 | doc only |
| Technical Director charter:762-780 | Keep records in existing systems; no extra registers | COVERED | AGENTS.md:65; tools/pipeline_check.py:106-116 | pipeline_check budgets |
| Technical Director charter:782-793 | Session handoff fields | STRENGTHENED | AGENTS.md:86; tools/journal.py:258 | check_pr (Journal section required) |
| Technical Director charter:795 | Don't claim records persisted unless stored | STRENGTHENED | AGENTS.md:86 | check_pr; `git log origin/<branch> -1` proof |
| Technical Director charter:799-815 | Prefer official sources; verified vs unverified | STRENGTHENED | docs/unreal-sources.md:3-5; pipeline/unreal-rules.md:10-11; pipeline/roles/dev-lead.md:32 | review item 5 (header citation); [VERIFY] clearing in TD Done when |
| Technical Director charter:817-826 | Reference: concise decision records | COVERED | docs/decisions.md:1-18 | doc only |
| Technical Director charter:828-835 | Reference: Unity module-boundary files | ADAPTED | pipeline/roles/technical-director.md:10 | module_check; became UE modules and Build.cs |
| Technical Director charter:837-844 | Reference: keep decision history, no rewriting | COVERED | docs/decisions.md:16 | doc only |
| Technical Director charter:846 | References not binding | DROPPED | - | no rule content |
| Technical Director charter:850-867 | Judge on outcomes; correct errors when found | ADAPTED | AGENTS.md:80; pipeline/templates/gate-record.md:18 | doc only; correction by new linked comment |
| Technical Director charter:869 | Structured review after milestones and major failures | PORTED | pipeline/templates/gate-record.md:20; tools/check_card.py | `--gate-record`: Incidents entry needs #n, cause=, follow-up= |
| Technical Director charter:871-880 | One-to-five self-ratings | DROPPED | - | (b) self-rating bureaucracy, rejected in port-log |
| Technical Director charter:882-892 | Charter-weakness proposal format | ADAPTED | AGENTS.md:30-31; pipeline/templates/gate-record.md:18 | doc only; a gap becomes a decision row or the gate "change for next gate" line |
| Technical Director charter:894 | Don't change role instructions without approval | STRENGTHENED | pipeline/agent-ops/gates.json; AGENTS.md:98 | hook.py blocks edits to pipeline/roles/** and AGENTS.md |
| Technical Director charter:896 | Isolated mistakes don't become permanent bureaucracy | ADAPTED | AGENTS.md:99; tools/pipeline_check.py:106-116 | pipeline_check budgets; a rule change needs a measurement |
| Technical Director charter:900-915 | Shared protocol; don't impose policy on others | COVERED | AGENTS.md:3; AGENTS.md:53; AGENTS.md:98 | doc only; AGENTS.md is the shared protocol |
| Technical Director charter:919-935 | Four proportional response levels | ADAPTED | AGENTS.md:139-140; pipeline/roles/dev-lead.md:18-24 | doc only; fixed output format per role, effort raised on evidence; no levels |
| Technical Director charter:937-939 | Recommendation structure purpose to next decision | ADAPTED | AGENTS.md:133 | doc only; unknowns format |
| Technical Director charter:943-947 | Compact activation directive | COVERED | pipeline/roles/technical-director.md:3-5 | doc only |
| Technical Director charter:951-957 | Know when to stop; no routine dependence on TD | COVERED | AGENTS.md:82-91; .github/CODEOWNERS.example:7 | doc only |
| Technical Director charter:959-965 | Closing slogans | DROPPED | - | no rule content; restates TD:117-131 |
| Technical Director charter:969-980 | Document control block | DROPPED | - | no rule content |

### inherited: Development Pipeline

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Development Pipeline:1-13 | Header: version, status, owners, approval | DROPPED | - | (b) no rule content; document metadata and approval stamps |
| Development Pipeline:14-16 | Write least complicated correct, changeable code | COVERED | pipeline/roles/gameplay-dev.md:30; pipeline/roles/dev-lead.md:37 | doc only + reviewer checklist |
| Development Pipeline:17-20 | Scope; other docs own architecture and gameplay | ADAPTED | AGENTS.md:23-31 | doc only; source precedence list instead of named owning documents |
| Development Pipeline:21-22 | MUST / PREFER / EXCEPTION rule strengths | ADAPTED | pipeline/roles/dev-lead.md:46-47 | doc only; finding severity (blocker..low, style always low) replaces rule strengths |
| Development Pipeline:23-24 | Reuse general rules on other projects | DROPPED | - | (a) about other studio projects; no rule for this jam |
| Development Pipeline:25-41 | Governing docs, latest approved version, not drafts | ADAPTED | AGENTS.md:5-14; AGENTS.md:23-28 | doc only; GDD `CURRENT` snapshot and "never archive" replace version discovery |
| Development Pipeline:42-45 | Layers: engine-free core, domain owns facts | ADAPTED | pipeline/unreal/cpp-rules.md:18; pipeline/unreal/gameplay-code.md:27-28,47 | doc only; rule cores are plain functions, Feedback Adapter only projects state |
| Development Pipeline:46-47 | One owner advances authoritative time; UI never ticks | ADAPTED | pipeline/unreal/gameplay-code.md:39-40,64; pipeline/unreal/cpp-rules.md:31 | doc only; Encounter Director owns states and PAUSED, timing from C++ timers; no single named clock owner |
| Development Pipeline:48-49 | Command/transaction identity, all-or-none publication, retry dedupe | DROPPED | - | (a) other game's transaction architecture; no commands or transactions in a 2D arcade loop |
| Development Pipeline:50-51 | Durable commits, hard-save boundaries, recovery lineage | DROPPED | - | (a) saves out of scope (port-log rejected TDP:41) |
| Development Pipeline:52-53 | Design supplies behavior; ambiguity becomes named question | COVERED | pipeline/roles/gameplay-dev.md:35,50; pipeline/roles/dev-lead.md:38; AGENTS.md:30-31 | reviewer checklist; decision row required |
| Development Pipeline:54-56 | Mentorship note on stable boundaries | DROPPED | - | (b) no rule content |
| Development Pipeline:57-59 | Target the pinned compiler/API, not host | ADAPTED | AGENTS.md:78,101; pipeline/roles/dev-lead.md:32 | reviewer blocker; engine pinned to 5.8.4, every new API cites its header |
| Development Pipeline:60-61 | Permitted language features for the pinned profile | ADAPTED | pipeline/unreal/cpp-rules.md:41-51 | module_check.py rules h-L; Epic C++ standard replaces C# feature list |
| Development Pipeline:62-63 | Banned language features; no shims to compile | STRENGTHENED | pipeline/unreal/cpp-rules.md:43,48; tools/module_check.py:22-24,64 | module_check.py rules j, l, y (no std::, exceptions, dynamic_cast, auto) |
| Development Pipeline:64-65 | Syntax, API, serialization, backend are separate checks | ADAPTED | pipeline/unreal/cpp-rules.md:12-13; AGENTS.md:76-77 | check_pr.py nonunity + package; PIE is not a build, only a package proves it links |
| Development Pipeline:66-67 | Nullable reference annotations per assembly | DROPPED | - | (a) C# nullable analysis; null safety covered by IsValid/TObjectPtr rows |
| Development Pipeline:68-72 | TD disposition on record-struct syntax in TDD | DROPPED | - | (a) C# language-version issue in the other game's TDD |
| Development Pipeline:73-77 | Editor-only code and tests kept separate | COVERED | pipeline/unreal-rules.md:18,27 | doc only; editor module + Private/Tests per lane |
| Development Pipeline:77 | One principal type per file, file named after it | PORTED | pipeline/unreal/cpp-rules.md:36 | reviewer; module_check rule e for the generated header |
| Development Pipeline:78-79 | No Types/Helpers dumping-ground files; nested-type exceptions | COVERED | pipeline/checklists/file-hygiene.md:17; pipeline/roles/dev-lead.md:37 | checklist + reviewer checklist |
| Development Pipeline:80-81 | Namespace per file; folders mirror ownership | ADAPTED | pipeline/unreal/gameplay-code.md:6 | doc only; UE has no namespaces for reflected types, folder per GDD module instead |
| Development Pipeline:82-83 | Using order; no global usings; no generated project edits | ADAPTED | tools/module_check.py:26; AGENTS.md:97 | module_check.py rule l (no using namespace); never commit generated files |
| Development Pipeline:84-98 | Naming table incl. underscore-camel private fields | ADAPTED | pipeline/unreal/cpp-rules.md:44,47; pipeline/unreal/gameplay-code.md:70-71 | module_check.py rules n, o, w; DISPUTABLE: Epic PascalCase/b-prefix replaces underscore fields (port-log rejected) |
| Development Pipeline:99-100 | Names carry meaning/units; bools read as conditions; no Manager | STRENGTHENED | pipeline/unreal/cpp-rules.md:44; pipeline/roles/dev-lead.md:37; pipeline/roles/technical-director.md:43 | module_check.py rules n, o; tuning UPROPERTY units required |
| Development Pipeline:101-102 | Serialized renames are compatibility ops; no public-for-Inspector | STRENGTHENED | pipeline/unreal/cpp-rules.md:39; tools/module_check.py:76-80 | module_check.py rule C; CoreRedirects on reflected renames |
| Development Pipeline:103-106 | Encoding, indentation, braces; no repo-wide reformat | ADAPTED | .editorconfig:3-6; pipeline/unreal/cpp-rules.md:44,46; pipeline/roles/dev-lead.md:38 | module_check.py rules p, t; tabs per Epic; LF/trailing-space/region bans not checked |
| Development Pipeline:107-108 | Explicit narrow access, sealed default, readonly fields | STRENGTHENED | pipeline/unreal/cpp-rules.md:35; tools/module_check.py:76-80,93-95 | module_check.py rules A, C, K (K off by default until UHT final verified) |
| Development Pipeline:108,118 | Never expose mutable backing collections via getters | PORTED | pipeline/unreal/cpp-rules.md:52; tools/module_check.py | module_check rule P (test: STANDARD_CASES P + correct forms) |
| Development Pipeline:109-110 | Fixed member declaration order | ADAPTED | pipeline/roles/dev-lead.md:38 | reviewer checklist; no order mandated, reorder-only hunks rejected |
| Development Pipeline:111-112 | Expression bodies, var, shallow flow, no nested ternary | ADAPTED | pipeline/unreal/cpp-rules.md:48 | module_check.py rule y (auto); nested ternary and line width not covered |
| Development Pipeline:113-116 | Value vs entity; meaningful struct defaults | ADAPTED | pipeline/unreal/gameplay-code.md:44-45 | doc only; F<Comp>Tuning structs hold defaults, units and clamps |
| Development Pipeline:117-118 | Mutations behind owned, intention-revealing operations | STRENGTHENED | pipeline/unreal/gameplay-code.md:51-52,57; pipeline/roles/dev-lead.md:39 | module_check.py rule C + one-writer reviewer item |
| Development Pipeline:119-120 | Composition over inheritance; no generic base classes | COVERED | pipeline/roles/dev-lead.md:37; pipeline/roles/gameplay-dev.md:38 | reviewer checklist |
| Development Pipeline:121-122 | Interfaces only at meaningful boundaries | COVERED | pipeline/roles/dev-lead.md:37; pipeline/roles/gameplay-dev.md:30 | reviewer checklist |
| Development Pipeline:123-124 | Explicit dependencies; no per-use scene searches | ADAPTED | pipeline/unreal/gameplay-code.md:59,61 | reviewer checklist; cache in BeginPlay, no GetAllActorsOfClass per frame |
| Development Pipeline:125-126 | Explicit state enum, not contradictory booleans; no FSM framework | STRENGTHENED | pipeline/unreal/gameplay-code.md:57 | module_check.py rule z + forbidden-combination test per enum; no GAS/GameplayTags |
| Development Pipeline:127-128 | No generic repos/event buses; small extension methods | ADAPTED | pipeline/unreal/gameplay-code.md:31-34; pipeline/roles/dev-lead.md:37 | doc only; fixed GDD event vocabulary, no new subsystem |
| Development Pipeline:129-132 | One responsibility per method; parameter order; options types | ADAPTED | pipeline/unreal/cpp-rules.md:35; tools/module_check.py:108-111 | module_check.py rule J (no behavior-picking bool); parameter order not covered |
| Development Pipeline:133-134 | Validate at owning boundary, not in every helper | ADAPTED | pipeline/unreal/gameplay-code.md:61; pipeline/unreal-rules.md:60 | doc only; BeginPlay logs missing refs, flags refused at reset |
| Development Pipeline:135-136 | Exceptions for contract breaks; Try for expected refusal | ADAPTED | pipeline/unreal/gameplay-code.md:63 | module_check.py rule j; UE uses return codes, no exceptions |
| Development Pipeline:137-138 | Catch only to recover; no broad fallback defaults | ADAPTED | pipeline/unreal/gameplay-code.md:36; pipeline/unreal/cpp-rules.md:32 | doc only; DISPUTABLE: ours requires warn-and-fall-back on unknown event or missing asset |
| Development Pipeline:139-140 | Every resource, subscription, task has owner and end | STRENGTHENED | pipeline/unreal/gameplay-code.md:58; pipeline/unreal/cpp-rules.md:33 | module_check.py rules F, v, x |
| Development Pipeline:141-146 | Remove no-behavior code; record kept complexity in PR | COVERED | pipeline/roles/gameplay-dev.md:30; pipeline/roles/dev-lead.md:37 | doc only; "removed from first draft" line not checked by check_pr |
| Development Pipeline:147-148 | Meaningful locals; no compressed side-effect expressions | PORTED | pipeline/unreal/cpp-rules.md:37 | reviewer (dev-lead #4 reads every cpp rule) |
| Development Pipeline:149-150 | Extract shared rules only; no boolean-heavy DRY helpers | ADAPTED | tools/module_check.py:108-111; pipeline/roles/gameplay-dev.md:38 | module_check.py rule J; "same reason to change" test not stated |
| Development Pipeline:151-152 | No arbitrary length/coverage quotas; perf budgets owned | ADAPTED | pipeline/roles/dev-lead.md:47; AGENTS.md:99; pipeline/roles/technical-director.md:9 | doc only; TD owns frame-time numbers, style is low severity |
| Development Pipeline:153-156 | Document public API contracts and invariants | ADAPTED | pipeline/unreal/gameplay-code.md:56; pipeline/roles/technical-director.md:43 | doc only; numbered INV-n header block + tuning units; no general API doc rule |
| Development Pipeline:157-158 | XML doc tag usage | DROPPED | - | (a) C# XML documentation syntax |
| Development Pipeline:159-160 | Comments explain why; no stale comments; tracked TODOs | STRENGTHENED | pipeline/roles/dev-lead.md:37,43; tools/pipeline_check.py:122,212 | pipeline_check.py hygiene (bare TODO); eval case 38 |
| Development Pipeline:161-162 | Doc diagnostics (CS1591) do not prove good docs | DROPPED | - | (a) C# compiler diagnostic |
| Development Pipeline:163-168 | Engine callbacks bridge lifecycle; policy in plain code | ADAPTED | pipeline/unreal/gameplay-code.md:53,61; pipeline/unreal/cpp-rules.md:18 | doc only; ctor/BeginPlay/EndPlay split, explicit tick prerequisite |
| Development Pipeline:169 | Paired subscriptions; test repeated enable/disable | STRENGTHENED | pipeline/unreal/gameplay-code.md:58; tools/ue_run.py:31 | module_check.py rules F, x; smoke `--restart-cycles` |
| Development Pipeline:169,179 | Static events/state need explicit reset; avoid static mutable | PORTED | pipeline/unreal/cpp-rules.md:52; tools/module_check.py | module_check rule O (test: STANDARD_CASES O + correct forms) |
| Development Pipeline:170 | Lifetime-aware null checks; validate references at enable | STRENGTHENED | pipeline/unreal/cpp-rules.md:27; pipeline/unreal/gameplay-code.md:61,67 | module_check.py rule f (TObjectPtr); BP_* reference test |
| Development Pipeline:171 | Semantic input; UI sends commands, never mutates state | STRENGTHENED | pipeline/unreal/cpp-rules.md:21,23; pipeline/unreal/gameplay-code.md:47 | module_check.py rule u; MenuBlocksGameplayInput world test |
| Development Pipeline:172 | Event-driven presentation; no hot-path searches/allocations | ADAPTED | pipeline/unreal/gameplay-code.md:59; pipeline/roles/dev-lead.md:39 | reviewer checklist; per-frame allocation and formatted logging not covered |
| Development Pipeline:173 | Profile before optimizing; record context before/after | ADAPTED | pipeline/roles/dev-lead.md:42 | reviewer checklist; stat unit same machine/map/config, fewer fields than his |
| Development Pipeline:174 | Config assets read-only at runtime; persist stable IDs | COVERED | pipeline/unreal/gameplay-code.md:60; pipeline/roles/dev-lead.md:39 | reviewer checklist |
| Development Pipeline:175 | Timed routines lifecycle-bound; scaled vs unscaled explicit | ADAPTED | pipeline/unreal/gameplay-code.md:58,64; pipeline/ui/accessibility.md:52 | module_check.py rule v; GameSpeedScalesTimer test |
| Development Pipeline:176 | Async: thread handoff, cancellation, stale completion | ADAPTED | pipeline/unreal/cpp-rules.md:33 | module_check.py rule x; no async IO in this game |
| Development Pipeline:177 | Determinism: no wall clock, seeded random, stable order | PORTED | pipeline/unreal/cpp-rules.md:38,52; tools/module_check.py | module_check rule N (test: STANDARD_CASES N + harness exempt); TMap order by reviewer |
| Development Pipeline:178 | Diagnostics carry causal identity; one log category | ADAPTED | pipeline/unreal/gameplay-code.md:34,62 | module_check.py rule k; event payload IDs |
| Development Pipeline:178,247 | Log once, rate-limit repeats; no secrets/personal data | PORTED | pipeline/unreal/gameplay-code.md:62 | reviewer |
| Development Pipeline:179 | Keep asset references valid before moves/renames | ADAPTED | pipeline/unreal-rules.md:92-95; pipeline/checklists/file-hygiene.md:9 | checklist; redirectors and LFS locks replace .meta/GUID care |
| Development Pipeline:180-183 | Behavioral tests with boundary/failure cases; no getter tests | COVERED | pipeline/roles/gameplay-dev.md:32,42; pipeline/roles/dev-lead.md:41 | reviewer checklist (med finding) |
| Development Pipeline:184-185 | Fast pure tests vs engine integration tests | STRENGTHENED | pipeline/unreal/gameplay-code.md:70-76 | check_automation_report.py `--max-rule-seconds`; public-for-tests ban not stated |
| Development Pipeline:186-187 | Recovery changes need interruption and retry tests | ADAPTED | pipeline/unreal/gameplay-code.md:40; tools/ue_run.py:31 | smoke `--restart-cycles`; restart replaces transaction recovery |
| Development Pipeline:188-192 | Report commands, revision, counts; Not Run distinct; label self-review | STRENGTHENED | AGENTS.md:73-79; pipeline/roles/qa-build.md:48 | check_pr.py header/proof/tests; check_automation_report.py notRun |
| Development Pipeline:193 | Inspect existing code and contracts before editing | COVERED | pipeline/roles/gameplay-dev.md:24; AGENTS.md:19 | doc only |
| Development Pipeline:194-195 | Smallest change; no parallel systems; no drive-by cleanup | COVERED | pipeline/roles/gameplay-dev.md:30-31,37; pipeline/roles/dev-lead.md:38-39; AGENTS.md:100 | reviewer checklist |
| Development Pipeline:196-205 | Six-question AI simplicity review in the PR | ADAPTED | pipeline/roles/gameplay-dev.md:30; pipeline/roles/dev-lead.md:37,39 | doc only; only question 6 kept as a PR line, rest moved to reviewer |
| Development Pipeline:206 | Strip scaffolding, placeholders, commented-out code before review | STRENGTHENED | pipeline/roles/dev-lead.md:37; pipeline/checklists/file-hygiene.md:18 | pipeline_check.py hygiene (bare TODO) |
| Development Pipeline:207-208 | Mark assumptions and unrun checks; stop at access boundary | STRENGTHENED | AGENTS.md:17,75,131; pipeline/agent-ops/hook.py:12 | check_pr.py proof; hook.py gates |
| Development Pipeline:209-212 | Qualify gate on planted violation; missing runner = Not Run | STRENGTHENED | AGENTS.md:17,125; pipeline/roles/dev-lead.md:4-5 | tests/test_module_check.py fixtures; run_reviewer_eval.py |
| Development Pipeline:213-222 | Gate table Q1-Q7 | ADAPTED | AGENTS.md:107-127 | checks table; Q4 API-doc gate dropped, others map to module_check/check_pr/review |
| Development Pipeline:223-224 | Mechanical checks vs reviewer judgment split | COVERED | pipeline/roles/dev-lead.md:31 | reviewer checklist |
| Development Pipeline:225-228 | Gates only on owned source; never rewrite generated/vendor | COVERED | AGENTS.md:97; pipeline/unreal/cpp-rules.md:41 | module_check.py scope (Source/ modules) |
| Development Pipeline:229-230 | Treat tools as executable; pin version, provenance, licence | STRENGTHENED | pipeline/agent-ops/components.csv:2-3 | secrets_check.py rule components; checksum not recorded |
| Development Pipeline:231-232 | Verify IDE/engine/CI parity independently | ADAPTED | AGENTS.md:129; pipeline/day0-cards.md:31 | doc only; CI cannot run Unreal, Win/Mac same totals on Day 0 |
| Development Pipeline:233-234 | No blanket warnings-as-errors; scoped time-boxed exclusions | ADAPTED | AGENTS.md:105; tools/pipeline_check.py:123 | pipeline_check.py pragma; greenfield, no legacy baseline |
| Development Pipeline:235-238 | Reviewer reads code; findings cite rule and consequence | COVERED | pipeline/roles/dev-lead.md:27,53 | required field (JSON findings) |
| Development Pipeline:239-242 | Reject: breaks requirement, ownership or contract | COVERED | pipeline/roles/dev-lead.md:30,39 | reviewer checklist |
| Development Pipeline:243 | Reject: unsupported API or unqualified dependency | STRENGTHENED | pipeline/roles/dev-lead.md:32,46 | blocker; reviewer eval |
| Development Pipeline:244 | Reject: unrelated churn, duplicate systems, speculative infra | COVERED | pipeline/roles/dev-lead.md:37-38 | reviewer checklist |
| Development Pipeline:245 | Reject: exposed mutable state | STRENGTHENED | tools/module_check.py:76-80 | module_check.py rule C |
| Development Pipeline:246 | Reject: avoidable wrappers, duplicate logic, obscured behavior | ADAPTED | pipeline/roles/dev-lead.md:37 | reviewer checklist; duplicate logic not named |
| Development Pipeline:247 | Reject: hidden failures, hot-path waste, missing cleanup | ADAPTED | pipeline/roles/dev-lead.md:39-40 | reviewer checklist; secrets-in-logs part is the MISSING row above |
| Development Pipeline:248 | Reject: missing docs, falsified evidence, missing tests | COVERED | pipeline/roles/dev-lead.md:41,46 | blocker (missing evidence) |
| Development Pipeline:249 | Reject: failed activated mechanical gate | STRENGTHENED | AGENTS.md:118; pipeline/roles/dev-lead.md:31 | CI module_check.py, exit 0 required |
| Development Pipeline:250-251 | Style disputes settled locally; escalation owners | ADAPTED | pipeline/roles/dev-lead.md:47,50; AGENTS.md:54 | doc only; keep/withdraw disputes with evidence |
| Development Pipeline:252-255 | Exception record: rule, scope, reason, approver, expiry | ADAPTED | AGENTS.md:105; docs/decisions.md; pipeline/templates/gate-record.md:23 | pipeline_check.py pragma; decision row has owner, no expiry or removal owner |
| Development Pipeline:256-257 | Debt cleanup in its own work item; migrate data | COVERED | pipeline/roles/gameplay-dev.md:37; pipeline/unreal/cpp-rules.md:39 | doc only |
| Development Pipeline:258-259 | Standard owned by lead; tool false positives trigger update | COVERED | pipeline/roles/dev-lead.md:9; pipeline/roles/technical-director.md:35 | doc only; tool fixed with a test, never waived |
| Development Pipeline:260-269 | Adoption proposal and rollout authorizations | DROPPED | - | (b) publication and rollout approvals |
| Development Pipeline:270-279 | Acceptance lineage, hashes, publication, canonical location | DROPPED | - | (b) record of his document's own approval |
| Development Pipeline:280-298 | One-page coding conventions quick reference | ADAPTED | pipeline/unreal-rules.md:3-8; pipeline/roles/dev-lead.md:27-47 | doc only; core file + reviewer checklist serve as the quick reference |
| Development Pipeline:299-302 | Reference construction patterns, one type per file | ADAPTED | pipeline/day0-cards.md:36 | Day-0 card 0.5 builds the real test pattern; no worked component example |
| Development Pipeline:303-333 | Example: immutable identity value type | DROPPED | - | (a) C# identity type for the other game's save model |
| Development Pipeline:334-369 | Example: validation before mutation preserves state | ADAPTED | pipeline/unreal/gameplay-code.md:57; pipeline/roles/gameplay-dev.md:32 | forbidden-combination and negative-case tests |
| Development Pipeline:370-414 | Example: small port and adapter, no catch/log duplication | ADAPTED | pipeline/roles/dev-lead.md:37 | reviewer checklist; no worked example |
| Development Pipeline:415-442 | Example: constructor injection; cold-path allocation note | ADAPTED | pipeline/unreal/gameplay-code.md:61 | doc only; BeginPlay caching |
| Development Pipeline:443-469 | Example: Try parse without redundant branch | ADAPTED | pipeline/roles/gameplay-dev.md:30 | doc only |
| Development Pipeline:470-500 | Example: composition; non-atomic loop warning | ADAPTED | pipeline/roles/dev-lead.md:37; pipeline/unreal/gameplay-code.md:40 | doc only |
| Development Pipeline:501-524 | Example: justified framework inheritance in editor code | ADAPTED | pipeline/unreal-rules.md:18; pipeline/roles/technical-director.md:30 | doc only; editor module holds validators |
| Development Pipeline:525-560 | Example: engine adapter with paired subscribe/unsubscribe | STRENGTHENED | pipeline/unreal/gameplay-code.md:58 | module_check.py rule F |
| Development Pipeline:561-589 | Example: XML-documented public API | DROPPED | - | (a) C# XML docs |
| Development Pipeline:590-612 | Example: behavioral test asserting state preserved | COVERED | pipeline/roles/gameplay-dev.md:32; pipeline/roles/dev-lead.md:41 | reviewer checklist |
| Development Pipeline:613-644 | Example: refactor generated code, behavior unchanged | COVERED | pipeline/roles/dev-lead.md:42; pipeline/roles/gameplay-dev.md:30 | reviewer checklist |
| Development Pipeline:645-648 | Enforcement appendix is candidate only | DROPPED | - | (b) no rule content |
| Development Pipeline:649-734 | Candidate editor style config and naming precedence | ADAPTED | .editorconfig:3-6; pipeline/unreal/cpp-rules.md:41-51 | module_check.py replaces analyzer naming rules |
| Development Pipeline:735-758 | Compiler XML-doc options; broken-reference fixture | DROPPED | - | (a) C# compiler/doc-output settings |
| Development Pipeline:759-777 | Analyzer inventory fields; narrow rule scope | ADAPTED | pipeline/agent-ops/components.csv:2-3 | secrets_check.py rule components; rule-set scoping is Unity-only |
| Development Pipeline:778-789 | Formatter command; CI job order; Not Run on missing | ADAPTED | AGENTS.md:107-129; .github/workflows/pipeline-checks.yml:52 | CI runs text checks; Unreal logs pasted into PR |
| Development Pipeline:790-804 | Minimal review record fields in PR body | ADAPTED | .github/PULL_REQUEST_TEMPLATE.md:2-39 | check_pr.py sections; no contract-change, lifetime-risk or exception-expiry lines |
| Development Pipeline:805-826 | Historical source paths and hashes | DROPPED | - | (b) no rule content |
| Development Pipeline:827-840 | Cite official technical references for engine facts | COVERED | pipeline/unreal-rules.md:10-11; docs/unreal-sources.md | doc only; `[src: Uxx]` tags |
| Development Pipeline:841-865 | Release history, review identities, publication admin | DROPPED | - | (b) no rule content |

### inherited: Lead Developer charter

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Lead Developer charter:1-16 | Title, version, approval stamps | DROPPED | - | no rule content |
| Lead Developer charter:18-26 | Lead is hands-on builder, not a code generator | ADAPTED | pipeline/roles/gameplay-dev.md:3-4; pipeline/roles/dev-lead.md:3-5 | doc only; lead split into builder (Gameplay Dev) and reviewer (Dev Lead) |
| Lead Developer charter:28-38 | List of expected lead duties | ADAPTED | pipeline/roles/gameplay-dev.md:23-39; pipeline/roles/dev-lead.md:27-45 | doc only; duties became numbered how-to-work and review items |
| Lead Developer charter:39 | Verify behavior, not tool success messages | STRENGTHENED | AGENTS.md:73-77 | check_pr (evidence header); check_automation_report |
| Lead Developer charter:40-42 | Coordinate, keep state, improve methods | ADAPTED | AGENTS.md:65; pipeline/templates/gate-record.md:18 | doc only; GitHub is the record, method changes per gate |
| Lead Developer charter:44 | Deliver working software, not task reports | COVERED | AGENTS.md:76; pipeline/roles/qa-build.md:56 | packaged build and smoke |
| Lead Developer charter:46 | Work inside architecture, scope, resources | COVERED | AGENTS.md:61 | check_pr lane globs |
| Lead Developer charter:52-62 | Success is accepted outcomes, not volume | COVERED | AGENTS.md:76; pipeline/roles/producer.md:23 | check_card --tracker (gate counts only passed items) |
| Lead Developer charter:64-119 | Areas of expertise list | DROPPED | - | no rule content |
| Lead Developer charter:121-127 | Personally code, debug, test; own delegated results | ADAPTED | pipeline/roles/gameplay-dev.md:23-34; pipeline/roles/dev-lead.md:27 | doc only; builder writes and proves, reviewer answers for the merge verdict |
| Lead Developer charter:129 | Don't delegate all meaningful work | ADAPTED | AGENTS.md:52; AGENTS.md:66 | doc only; one card one role, no delegation chain to guard against |
| Lead Developer charter:131-149 | Charter project-agnostic; verify project first | ADAPTED | AGENTS.md:5-17 | doc only; ours is project-specific, read order and CAN RUN line |
| Lead Developer charter:155-157 | Patch or isolated test is not integrated | STRENGTHENED | AGENTS.md:75-76; pipeline/roles/qa-build.md:44 | check_pr (package + SMOKE_OK for maps, Config, Build.cs) |
| Lead Developer charter:159-161 | Correctness before cleverness | COVERED | pipeline/roles/dev-lead.md:37 | review item 10 |
| Lead Developer charter:163-167 | Simplest solution, no speculative extensibility | COVERED | pipeline/roles/gameplay-dev.md:30; pipeline/roles/dev-lead.md:37 | review item 10; no eval case for a speculative interface yet |
| Lead Developer charter:169-171 | Evidence before completion claims | STRENGTHENED | AGENTS.md:72-80 | check_pr |
| Lead Developer charter:173-175 | Maintainability before expedience | COVERED | pipeline/roles/dev-lead.md:31 | module_check rules h-L |
| Lead Developer charter:177-179 | Routine decisions alone, within binding constraints | COVERED | AGENTS.md:67-68; pipeline/roles/gameplay-dev.md:47 | module_check (boundaries) |
| Lead Developer charter:181-183 | Challenge TD, Producer, leads on evidence | COVERED | AGENTS.md:30-31; pipeline/roles/dev-lead.md:50 | doc only |
| Lead Developer charter:185-187 | Automation cuts repetitive work, keeps accountability | STRENGTHENED | AGENTS.md:107-127 | every check in AGENTS §8 |
| Lead Developer charter:189-191 | Never fabricate execution, tests, reviews, commits | STRENGTHENED | AGENTS.md:76; AGENTS.md:79 | check_pr (evidence header, stale SHA) |
| Lead Developer charter:199-209 | No TD sign-off for routine; never ignore binding | COVERED | .github/CODEOWNERS.example:7; AGENTS.md:100 | module_check; CODEOWNERS not live until D26 |
| Lead Developer charter:211-221 | Recommend / decide / initiate / commit distinction | ADAPTED | AGENTS.md:67-68 | doc only; reduced to the human-approval list |
| Lead Developer charter:223 | Writing a brief does not authorize execution | COVERED | pipeline/roles/producer.md:19; pipeline/checklists/card-ready.md:3 | check_card 0 problems before label todo |
| Lead Developer charter:225-244 | Engineering ownership list | ADAPTED | pipeline/roles/gameplay-dev.md:7-21; pipeline/roles/dev-lead.md:8-11; pipeline/roles/integrator.md:18 | doc only; split across Gameplay Dev, Dev Lead, Integrator (main green) |
| Lead Developer charter:248-270 | Delegated decision matrix | ADAPTED | AGENTS.md:33-54; AGENTS.md:67-68 | doc only; matrix rejected (port-log LD:211), file lanes instead |
| Lead Developer charter:272-280 | Routine autonomy: features, fixes, refactors, tests | COVERED | AGENTS.md:67-68 | doc only |
| Lead Developer charter:281 | Lead reviews and merges changes | ADAPTED | AGENTS.md:63; AGENTS.md:94 | doc only; DISPUTABLE: he lets the lead merge; ours: agents never merge; kickoff merges once CI, the reviewer agent and check_pr pass |
| Lead Developer charter:282-285 | Diagnostics, docs; stay within standards | COVERED | AGENTS.md:67-68; pipeline/unreal-rules.md:1-11 | module_check |
| Lead Developer charter:287-297 | Escalate material changes (gameplay, interfaces, data) | COVERED | pipeline/roles/dev-lead.md:38; pipeline/roles/gameplay-dev.md:35; pipeline/roles/gameplay-dev.md:47; AGENTS.md:85 | review item 11 |
| Lead Developer charter:299 | No approval requests for minor refactors | COVERED | AGENTS.md:67-68 | doc only |
| Lead Developer charter:303-317 | TD sets direction; lead implements; both contribute | ADAPTED | pipeline/roles/technical-director.md:11; pipeline/roles/gameplay-dev.md:47 | doc only; TD writes core shell, Gameplay Dev the components |
| Lead Developer charter:319-329 | Architecture challenge: evidence, smallest fix, keep working | COVERED | pipeline/roles/gameplay-dev.md:47; pipeline/roles/gameplay-dev.md:50; AGENTS.md:30-31; AGENTS.md:85; AGENTS.md:88 | doc only; decision row or split proposal; other lanes continue |
| Lead Developer charter:331 | Never silently implement a conflicting architecture | STRENGTHENED | pipeline/roles/dev-lead.md:34; pipeline/roles/technical-director.md:35 | module_check (boundaries, shell rule L) |
| Lead Developer charter:333-345 | When to request TD consultation | COVERED | pipeline/roles/gameplay-dev.md:47; pipeline/roles/technical-director.md:32; .github/CODEOWNERS.example:4-12 | doc only |
| Lead Developer charter:347-355 | Disagreement by evidence; support final decision | COVERED | pipeline/roles/dev-lead.md:50; docs/decisions.md:15; pipeline/templates/spike-card.md:1-26 | check_card spike rule |
| Lead Developer charter:361-365 | Production vs engineering ownership | COVERED | pipeline/roles/producer.md:6-11 | doc only |
| Lead Developer charter:367 | Credible estimates, dependencies, progress, risks | STRENGTHENED | pipeline/templates/task-card.md:42; pipeline/roles/producer.md:21 | check_card (Budget format, --status) |
| Lead Developer charter:369 | Don't hide uncertainty to save the schedule | STRENGTHENED | pipeline/roles/producer.md:21; pipeline/roles/producer.md:64; AGENTS.md:89 | check_card --status (will miss needs Cut proposed), --overrun |
| Lead Developer charter:371 | Don't expand approved scope | COVERED | pipeline/roles/gameplay-dev.md:30; pipeline/roles/dev-lead.md:38 | review items 10-11 |
| Lead Developer charter:373-388 | Art and engineering collaboration topics | COVERED | pipeline/art/import-rules.md; pipeline/roles/asset-specialist.md | sprite_check; art_check |
| Lead Developer charter:390 | Art acceptance survives technical remediation | COVERED | pipeline/roles/art-director.md:48 | sprite_check --import-report |
| Lead Developer charter:392 | Don't change artistic intent for convenience | COVERED | pipeline/roles/gameplay-dev.md:39; pipeline/roles/integrator.md:44 | doc only |
| Lead Developer charter:394-403 | Separate design intent, contract, interpretation, question | COVERED | pipeline/templates/task-card.md:10-11; pipeline/checklists/design-review.md:12 | required field (GDD ref tag) |
| Lead Developer charter:405 | Don't invent values because code needs one | COVERED | pipeline/roles/gameplay-dev.md:35; pipeline/roles/dev-lead.md:38 | review item 11 (decision row in same PR) |
| Lead Developer charter:407 | Focused question or bounded hypothesis | COVERED | AGENTS.md:133; pipeline/templates/spike-card.md:9-18 | check_card spike rule |
| Lead Developer charter:409-415 | QA independent; reproducible defect reports | COVERED | pipeline/roles/qa-build.md:17 | doc only (bug fields) |
| Lead Developer charter:417 | Don't dismiss QA failures because unit tests pass | COVERED | pipeline/roles/qa-build.md:44; pipeline/roles/qa-build.md:59 | doc only |
| Lead Developer charter:419-423 | Other disciplines; no approval ceremonies | COVERED | AGENTS.md:43-48 | doc only |
| Lead Developer charter:429-435 | Ten-stage execution loop | ADAPTED | AGENTS.md:56-70 | doc only; card flow todo, doing, review, done |
| Lead Developer charter:437-449 | Understand objective, code, access, limits first | STRENGTHENED | pipeline/templates/task-card.md:6-47; pipeline/roles/gameplay-dev.md:24; AGENTS.md:17 | check_card; CAN RUN line |
| Lead Developer charter:451 | No substantial work from speculative understanding | COVERED | pipeline/checklists/card-ready.md:6; AGENTS.md:58 | check_card (empty field fails) |
| Lead Developer charter:453-465 | Decompose into verifiable increments, few files | STRENGTHENED | pipeline/templates/task-card.md:33-42 | check_card (checkable Done-when; agent over 120 min or human over 60 min splits) |
| Lead Developer charter:466 | Avoid over-fragmenting into tiny admin tasks | PORTED | pipeline/checklists/card-ready.md:10 | card-ready line (Producer) |
| Lead Developer charter:468-474 | Work covered by package; irreversible needs approval | COVERED | AGENTS.md:57-58; AGENTS.md:67-68; AGENTS.md:95 | check_card |
| Lead Developer charter:476-482 | Preserve behavior; no unrelated cleanup | STRENGTHENED | pipeline/roles/gameplay-dev.md:31; pipeline/roles/dev-lead.md:38; pipeline/roles/dev-lead.md:49 | review item 11; Keep unchanged; eval case 21 |
| Lead Developer charter:484-497 | Review criteria list | COVERED | pipeline/roles/dev-lead.md:27-45 | reviewer eval (run_reviewer_eval); secrets_check for security |
| Lead Developer charter:499-505 | Report real results; not run is not run | STRENGTHENED | AGENTS.md:77; tools/check_automation_report.py:133; tools/check_pr.py:674 | check_automation_report (NotRun fails); check_pr |
| Lead Developer charter:507-509 | Verify with systems, assets, configs | STRENGTHENED | pipeline/roles/dev-lead.md:36; pipeline/templates/task-card.md:28 | check_pr package rule; check_card Used by |
| Lead Developer charter:511-513 | Handoff: status, evidence, files, defects, next | STRENGTHENED | .github/PULL_REQUEST_TEMPLATE.md:7-29 | check_pr (sections, linked risks, Next:) |
| Lead Developer charter:517-536 | Code quality list | COVERED | pipeline/unreal/cpp-rules.md; pipeline/roles/dev-lead.md:31 | module_check rules h-L |
| Lead Developer charter:538-552 | Conform to boundaries; propose change, don't violate | STRENGTHENED | pipeline/roles/dev-lead.md:39; pipeline/unreal/gameplay-code.md:51 | module_check; review item 12 |
| Lead Developer charter:554-572 | Tests by risk, behavior and failure states | STRENGTHENED | pipeline/roles/dev-lead.md:33; pipeline/roles/dev-lead.md:41; pipeline/roles/gameplay-dev.md:32; pipeline/checklists/card-ready.md:19 | review items 6, 14; eval case 22; no coverage percentage (same as his) |
| Lead Developer charter:574-579 | Reproduce, isolate, hypothesize, instrument, fix, regress | ADAPTED | pipeline/roles/gameplay-dev.md:34; pipeline/roles/dev-lead.md:41 | review item 14 (fail before fix); only reproduce and regression test are written; middle steps not |
| Lead Developer charter:580 | Evidence proportional to severity | ADAPTED | pipeline/roles/qa-build.md:17-20 | doc only; P0-P3 labels, same bug fields for all |
| Lead Developer charter:582 | Unreproduced defect: report uncertainty, not fixed | COVERED | pipeline/roles/gameplay-dev.md:34; pipeline/roles/dev-lead.md:41 | review item 14 ("not reproduced", bug stays open) |
| Lead Developer charter:584-590 | Profile first; record environment and workload | STRENGTHENED | pipeline/roles/dev-lead.md:42; pipeline/roles/qa-build.md:32 | review item 15; smoke fps contract |
| Lead Developer charter:592-600 | Debt: bounded remediation, no new milestone | COVERED | pipeline/roles/gameplay-dev.md:37 | doc only; debt becomes a linked issue |
| Lead Developer charter:604-606 | Follow project source-control strategy | COVERED | AGENTS.md:60; AGENTS.md:136-137 | doc only |
| Lead Developer charter:608-618 | Repo hygiene: boundaries, isolation, generated files | STRENGTHENED | AGENTS.md:60; AGENTS.md:95-97 | pipeline_check (junk, LFS); check_pr lane globs |
| Lead Developer charter:620 | No universal branching model | ADAPTED | AGENTS.md:60 | doc only; one fixed model for the jam |
| Lead Developer charter:622-633 | Merge readiness checklist | STRENGTHENED | .github/PULL_REQUEST_TEMPLATE.md:1-39 | check_pr; Dev Lead review |
| Lead Developer charter:635 | Don't merge or overwrite outside authority | COVERED | AGENTS.md:63; AGENTS.md:94-95 | doc only; branch protection pending |
| Lead Developer charter:637-643 | Build failures: real logs, classify, next owner | COVERED | AGENTS.md:83-84; pipeline/roles/qa-build.md:52 | doc only (cause class required in blocked note) |
| Lead Developer charter:649 | Agents are resources, not accountability substitutes | COVERED | AGENTS.md:63; AGENTS.md:94 | doc only |
| Lead Developer charter:651-668 | Lead directs coding agents; TD directs prototypes | ADAPTED | pipeline/roles/producer.md:7; pipeline/templates/spike-card.md:1-7 | doc only; Producer files all cards, spikes are cards |
| Lead Developer charter:670-682 | Verify agent tools, access, permissions, limits | STRENGTHENED | AGENTS.md:9; AGENTS.md:15-17; pipeline/roles/gameplay-dev.md:28-29 | CAN RUN line; hook blocks writes without JAM_ROLE |
| Lead Developer charter:684 | Agent may lack access, comms, continuation | COVERED | AGENTS.md:65-66; AGENTS.md:86 | doc only |
| Lead Developer charter:686-704 | Implementation brief fields | STRENGTHENED | pipeline/templates/task-card.md:6-47; .github/ISSUE_TEMPLATE/task.yml | check_card |
| Lead Developer charter:706 | Brief works without prior conversation | COVERED | pipeline/checklists/card-ready.md:6 | check_card (empty field fails); no "as discussed" |
| Lead Developer charter:708 | Don't overspecify implementation in the brief | PORTED | pipeline/checklists/card-ready.md:11 | card-ready line (Producer) |
| Lead Developer charter:710-725 | Ten execution states; never infer later state | ADAPTED | AGENTS.md:70; AGENTS.md:77; pipeline/roles/qa-build.md:48 | check_pr (stale SHA, evidence label); fewer states |
| Lead Developer charter:727-742 | Inspect actual diff, not agent summary | STRENGTHENED | pipeline/roles/dev-lead.md:27; pipeline/roles/integrator.md:32 | check_pr lane globs; reviewer eval |
| Lead Developer charter:744-753 | Failed work: find cause, protect, choose, limit | COVERED | AGENTS.md:83-85; pipeline/roles/dev-lead.md:49; pipeline/roles/producer.md:55 | doc only; cause classes, Keep unchanged |
| Lead Developer charter:755 | No indefinite retries without new approach | STRENGTHENED | AGENTS.md:83; AGENTS.md:89-90 | check_card --overrun |
| Lead Developer charter:759-775 | Six acceptance states | ADAPTED | AGENTS.md:70; pipeline/roles/qa-build.md:48 | check_pr evidence label; fewer states |
| Lead Developer charter:777-793 | Engineering verification criteria; no claim if absent | STRENGTHENED | pipeline/roles/dev-lead.md:22-25; pipeline/roles/dev-lead.md:57 | reviewer eval; checks_seen "missing" blocks approve |
| Lead Developer charter:795-799 | Engineering verified is not technical acceptance | ADAPTED | pipeline/roles/qa-build.md:48; pipeline/roles/technical-director.md:32 | check_pr label line; developer-tested vs QA-verified |
| Lead Developer charter:801-815 | Defect disposition states | ADAPTED | pipeline/roles/qa-build.md:17-20; pipeline/roles/qa-build.md:43-45; AGENTS.md:70 | doc only; issue labels P0-P3 and card states |
| Lead Developer charter:817 | Don't close defects just because code changed | COVERED | pipeline/roles/qa-build.md:44; pipeline/roles/qa-build.md:59 | doc only |
| Lead Developer charter:821-833 | Emergency: impact, logs, mitigate, notify, verify | STRENGTHENED | AGENTS.md:87; pipeline/roles/qa-build.md:18; pipeline/roles/qa-build.md:52 | .github/workflows/main-red.yml (opens revert PR) |
| Lead Developer charter:834-836 | No ceremony for diagnosis; no irreversible under urgency | COVERED | AGENTS.md:87; AGENTS.md:95 | doc only |
| Lead Developer charter:842-853 | Session start: project, requirements, repo, tools | COVERED | AGENTS.md:5-19 | journal resume; CAN RUN line |
| Lead Developer charter:855 | Newer file is not necessarily approved | COVERED | AGENTS.md:7 | doc only |
| Lead Developer charter:857 | Don't invent requirements when material missing | COVERED | AGENTS.md:30-31 | pipeline_check (decision row exists) |
| Lead Developer charter:859 | Memory is not project documentation | COVERED | AGENTS.md:19 | doc only |
| Lead Developer charter:863-880 | Records in existing systems; nothing redundant | COVERED | AGENTS.md:65; tools/pipeline_check.py:106-116 | pipeline_check budgets |
| Lead Developer charter:882-895 | End-of-session handoff fields | STRENGTHENED | AGENTS.md:86; tools/journal.py:258 | check_pr (Journal section required) |
| Lead Developer charter:897 | Don't claim commit, merge, save unless verified | STRENGTHENED | AGENTS.md:86; pipeline/roles/integrator.md:32 | check_pr; `git log origin/<branch> -1` proof |
| Lead Developer charter:899-908 | Recovery: verify tree, reconcile handoff claims | COVERED | AGENTS.md:16-19 | journal resume; gdd_impact for current requirements |
| Lead Developer charter:910 | Never infer completion from prior summary | COVERED | AGENTS.md:19 | doc only (re-run any check a handoff claimed) |
| Lead Developer charter:914-922 | Prefer official sources; verified vs unverified | STRENGTHENED | docs/unreal-sources.md:3-5; pipeline/roles/dev-lead.md:32 | review item 5 (header citation); [VERIFY] tags |
| Lead Developer charter:926-933 | Reference: review for system health, not style | COVERED | pipeline/roles/dev-lead.md:47 | doc only (pure style is always low) |
| Lead Developer charter:935-942 | Reference: the other engine's test runner | ADAPTED | pipeline/unreal/gameplay-code.md:69-78 | check_automation_report; became UE automation tests |
| Lead Developer charter:944-951 | Reference: Unity module-boundary files | ADAPTED | pipeline/roles/technical-director.md:10 | module_check; became UE modules and Build.cs |
| Lead Developer charter:953 | References not binding | DROPPED | - | no rule content |
| Lead Developer charter:957-976 | Judge lead on outcomes incl. review quality | STRENGTHENED | pipeline/roles/dev-lead.md:3-5; tools/run_reviewer_eval.py | reviewer eval on seeded-defect cases |
| Lead Developer charter:978 | Self-assessment at milestones and major failures | PORTED | pipeline/templates/gate-record.md:20; tools/check_card.py | `--gate-record`: Incidents entry needs #n, cause=, follow-up= |
| Lead Developer charter:980-989 | One-to-five self-ratings | DROPPED | - | (b) self-rating bureaucracy, rejected in port-log |
| Lead Developer charter:991-1001 | Charter-weakness proposal format | ADAPTED | AGENTS.md:30-31; pipeline/templates/gate-record.md:18 | doc only; gap goes to a decision row or the gate line |
| Lead Developer charter:1003 | Don't alter role instructions without approval | STRENGTHENED | pipeline/agent-ops/gates.json; AGENTS.md:98 | hook.py blocks edits to pipeline/roles/** and AGENTS.md |
| Lead Developer charter:1005 | Avoid unnecessary process expansion | STRENGTHENED | tools/pipeline_check.py:106-116 | pipeline_check word budgets |
| Lead Developer charter:1009-1015 | Shared protocol; no competing studio policy | COVERED | AGENTS.md:3; AGENTS.md:98 | doc only |
| Lead Developer charter:1019-1039 | Four proportional response levels | ADAPTED | AGENTS.md:139-140; pipeline/roles/dev-lead.md:18-24 | doc only; fixed output formats, effort raised on evidence; no levels |
| Lead Developer charter:1043-1047 | Compact activation directive | COVERED | pipeline/roles/gameplay-dev.md:3-4; pipeline/roles/dev-lead.md:3-5 | doc only |
| Lead Developer charter:1051-1057 | Know when to stop and recover | COVERED | AGENTS.md:82-91 | doc only |
| Lead Developer charter:1059-1067 | Closing slogans | DROPPED | - | no rule content; restates LD:155-179 |
| Lead Developer charter:1071-1081 | Document control block | DROPPED | - | no rule content |
| Lead Developer charter:1083 | Adoption clause names the wrong role | DROPPED | - | no rule content; copy error in his file |

### inherited: Art Pipeline

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Art Pipeline:1-13 | Title, version, approval status, owners, scope stamp | DROPPED | - | (b) no rule content; executive approval stamp |
| Art Pipeline:14-17 | Every asset must work in the game | COVERED | pipeline/roles/art-director.md:4; AGENTS.md:75 | doc only; art review judges in-engine captures |
| Art Pipeline:18-21 | Purpose and "supplements other docs" boilerplate | DROPPED | - | (b) no rule content |
| Art Pipeline:22 | Ownership split across art, design, tech, production, QA | ADAPTED | AGENTS.md:33-54; pipeline/roles/*.md | doc only; one role card per lane, ties to Creative director / Scope decision-maker |
| Art Pipeline:23-25 | No unauthorized production; routine work needs no re-approval | COVERED | AGENTS.md:58,66-67 | doc only; no card, no work |
| Art Pipeline:26-27 | Out of scope: no invented numbers, sizes, rates | ADAPTED | pipeline/art/art-bible.md:52-70; docs/port-log.md:42 | doc only; DISPUTABLE: ours states proposed numbers and changes them on measurement |
| Art Pipeline:28-31 | Dynamic doc discovery; only approved version binds | ADAPTED | AGENTS.md:7,23-27 | doc only; fixed source order plus `docs/gdd/CURRENT` snapshot |
| Art Pipeline:32-40 | Table of other project's inspected documents | DROPPED | - | (a) other game's documents |
| Art Pipeline:41-42 | Unconfirmed status: record dependency, no locking | COVERED | AGENTS.md:30-31 | doc only; decision row plus build the default |
| Art Pipeline:43-45 | Other game's customer cues, currency, staff, kitchen | DROPPED | - | (a) other game's setting |
| Art Pipeline:45 | Critical audio cues need visual redundancy | COVERED | pipeline/checklists/animation-review.md:26; pipeline/qa/playtests.md (P10) | doc only plus playtest P10 (playable muted) |
| Art Pipeline:45 | Controller, keyboard, text accessibility | COVERED | pipeline/ui/accessibility.md:13,25,85 | ui_check.py contrast / layout; UIFLOW menu-nav |
| Art Pipeline:46-47 | Fixed camera first; mockups do not bind final art | COVERED | pipeline/unreal-rules.md:16; pipeline/art/art-bible.md:7-9 | doc only; D0 key art sets look, not composition |
| Art Pipeline:48-52 | Presentation one-way; no geometry from sprites; animation never commits | COVERED | pipeline/unreal/gameplay-code.md:47,64; pipeline/art/import-rules.md:59 | sprite_check --import-report rule `collision`; doc only for the rest |
| Art Pipeline:53-55 | Every asset traces to a documented need | COVERED | pipeline/templates/asset-brief.md:8; AGENTS.md:58 | required field (Purpose); card GDD revision / Features |
| Art Pipeline:56 | Visual north star; not a low-res filter | ADAPTED | pipeline/art/art-bible.md:28-33; pipeline/roles/art-director.md:64 | art_check.py; was pixel art and neon, now ink on paper, pixel look is auto-fail |
| Art Pipeline:57 | Judge in representative scene at gameplay scale | STRENGTHENED | pipeline/roles/art-director.md:40,47 | source PNG alone = auto request_changes; art_check.py on CAM_Eval captures |
| Art Pipeline:58 | Keep layered editable source and export derivation | COVERED | pipeline/roles/asset-specialist.md:20,42; pipeline/art/art-bible.md:90-92 | doc only for source; provenance row required |
| Art Pipeline:59 | Stable identity; filenames are not gameplay IDs | ADAPTED | pipeline/templates/asset-brief.md:30; pipeline/roles/asset-specialist.md:40 | doc only; FB_ asset maps to a C++ state, reimport in place keeps references |
| Art Pipeline:60 | Repeatable export, validated before integration | ADAPTED | pipeline/art/import-rules.md:99-106; pipeline/roles/asset-specialist.md:37,42 | sprite_check --scan in CI; AI generation is recorded, not claimed reproducible |
| Art Pipeline:61 | Art specifies look; tech owns methods; design owns behavior | COVERED | pipeline/roles/art-director.md:76-78; pipeline/roles/asset-specialist.md:53 | doc only |
| Art Pipeline:62 | Modular families approved only after assembled test | STRENGTHENED | pipeline/checklists/animation-review.md:20-22 | sprite_check tile seam ΔE check; 3 copies side by side |
| Art Pipeline:63 | Light review low-risk, deep review for animation and UI | COVERED | pipeline/checklists/animation-review.md:3; pipeline/ui/accessibility.md:13-25 | doc only; checklists loaded only for flipbook, tiling, UI cards |
| Art Pipeline:64-67 | Limit variants, frames, revisions, compute to authorization | STRENGTHENED | pipeline/templates/asset-brief.md:21-22; pipeline/art/import-rules.md:65 | sprite_check 60 unique sprite cap; generation budget required field; check_card authorized features |
| Art Pipeline:68-73 | Eleven-stage asset progression chain | DROPPED | - | (b) multi-stage approval chain; ours todo/doing/review/done |
| Art Pipeline:74 | Art acceptance is not release readiness | COVERED | pipeline/roles/art-director.md:48 | doc only; import checks still required |
| Art Pipeline:75-92 | Fourteen-state table with advancing authority | DROPPED | - | (b) state bureaucracy; AGENTS.md:70 labels instead |
| Art Pipeline:93-94 | Accept-with-limitation needs owner, risk, trigger; no cross-waiver | COVERED | pipeline/roles/art-director.md:30,35,48; pipeline/templates/gate-record.md:29 | required field (Known limitations with issue link) |
| Art Pipeline:95-106 | Definition of Ready brief fields | COVERED | pipeline/templates/asset-brief.md:3-24; pipeline/checklists/card-ready.md:7 | doc only; "a brief with an empty field is not ready" |
| Art Pipeline:107-108 | Unknown specs labeled, no guessed numbers | ADAPTED | pipeline/art/import-rules.md:5-6; AGENTS.md:30-31 | [VERIFY] and "proposed" labels; `--gate` fails until status verified |
| Art Pipeline:109-113 | Definition of Done ten items for art package | COVERED | pipeline/roles/asset-specialist.md:27-50 | sprite_check --scan / --names / --import-report; AD approve; kickoff merges |
| Art Pipeline:114-118 | No bulk art before foundation profile accepted | COVERED | pipeline/day0-cards.md:50; docs/decisions.md (D-new-port-9) | gate; no other asset cards before card 0.10 |
| Art Pipeline:119-125 | Profile: camera, density, PPU, pivots, direction scheme | ADAPTED | pipeline/art/art-bible.md:52-66; pipeline/unreal-rules.md:16; docs/decisions.md:28 | sprite_check --config / pivot / ppu rules; side-on fixed camera, no directions |
| Art Pipeline:126-127 | Alpha edges, filtering, compression, mips, atlas | STRENGTHENED | pipeline/art/import-rules.md:50-60; pipeline/roles/asset-specialist.md:37-38 | sprite_check --scan halo/alpha; --import-report filter/compression/mips/atlas |
| Art Pipeline:128 | Sorting and depth order | COVERED | pipeline/unreal/gameplay-code.md:65; pipeline/art/art-bible.md:40 | doc only; one draw-order header, capture shows layer |
| Art Pipeline:129 | Lighting path and color treatment | ADAPTED | pipeline/art/art-bible.md:81-87 | art_check --swatch; unlit sprites, one assumed light, locked post-process |
| Art Pipeline:130 | Animation state binding and events | COVERED | pipeline/templates/asset-brief.md:10-11; pipeline/checklists/animation-review.md:17 | required field |
| Art Pipeline:131 | Footprint and anchors are semantic, not visual | COVERED | pipeline/art/import-rules.md:59,64; pipeline/templates/asset-brief.md:34 | --import-report `collision`, `socket` |
| Art Pipeline:132 | UI font, scaling, localization test profile | ADAPTED | pipeline/ui/accessibility.md:13,25 | ui_check.py text-floor / layout --scale 2; DISPUTABLE: no localization |
| Art Pipeline:133 | Target display and performance budget | COVERED | pipeline/roles/qa-build.md:32; pipeline/roles/art-director.md:51 | stat unit on REF_HOST before each gate |
| Art Pipeline:134-135 | Camera investigation order: fixed first | ADAPTED | pipeline/unreal-rules.md:16 | doc only; fixed orthographic chosen (D9) |
| Art Pipeline:136-138 | Point filtering candidate; validate in engine first | ADAPTED | pipeline/art/art-bible.md:77-78; pipeline/art/import-rules.md:5-6 | --import-report `filter`; opposite filter (bilinear) for painted art, [VERIFY] until 0.4a |
| Art Pipeline:139-141 | One representative proof scene, placeholders allowed | ADAPTED | pipeline/day0-cards.md:48-50 | gate; L_StyleFrame with 5 anchors |
| Art Pipeline:142-145 | Pixel integrity at camera scale during movement | ADAPTED | pipeline/checklists/animation-review.md:6-7 | doc only; motion clip required per flipbook, not in the proof scene |
| Art Pipeline:146 | Consistent physical scale | COVERED | pipeline/day0-cards.md:50 | gate; Ella 80-100 px at 1080p |
| Art Pipeline:147 | Modular joins without visible failure | COVERED | pipeline/checklists/animation-review.md:21-22 | sprite_check tile seam check |
| Art Pipeline:148 | Anchors via metadata, not painted bounds | COVERED | pipeline/art/import-rules.md:64; pipeline/templates/asset-brief.md:14 | --import-report `socket` |
| Art Pipeline:149 | Sorting with moving characters behind objects | ADAPTED | pipeline/roles/asset-specialist.md:45; pipeline/art/art-bible.md:39-40 | doc only; side-on game, draw order not occlusion |
| Art Pipeline:150 | Cue readability at low, typical, stress density | STRENGTHENED | pipeline/roles/art-director.md:47; pipeline/ui/accessibility.md:17,107 | ui_check.py grayscale on CAM_Eval_Stress; art_check |
| Art Pipeline:151 | Proof: source edit re-exports, reimports, binding survives | PORTED | pipeline/day0-cards.md:49 | card 0.10b Done-when: round trip pasted (`--import-report`, `--sources`) |
| Art Pipeline:152 | Profile render cost separate from simulation | ADAPTED | pipeline/roles/art-director.md:51; pipeline/roles/qa-build.md:32 | stat unit GPU ms; not split per subsystem |
| Art Pipeline:153-155 | Exit sign-offs; never claim QA that did not run | ADAPTED | pipeline/day0-cards.md:50; AGENTS.md:77 | gate; Rick plus AD instead of four departments |
| Art Pipeline:156-172 | Asset family taxonomy codes | ADAPTED | pipeline/unreal-rules.md:40; pipeline/art/import-rules.md:58,99-101 | sprite_check --names; family = per-asset folder and sidecar `kind` |
| Art Pipeline:173-180 | Art ID vs gameplay definition ID; no ID from PNG name | ADAPTED | pipeline/templates/asset-brief.md:30; pipeline/unreal/gameplay-code.md:67 | BP_* reference test; state map in handoff |
| Art Pipeline:181-188 | Registry minimum fields per art package | ADAPTED | pipeline/art/art-bible.md:89-92; pipeline/art/provenance.csv | submission_check credits; git holds revision and hash |
| Art Pipeline:189-203 | Dependency links; parent change re-evaluates children | COVERED | pipeline/roles/art-director.md:49 | doc only; re-run art_check on every CAM_Eval capture |
| Art Pipeline:204-235 | Logical repository layout | ADAPTED | pipeline/unreal-rules.md:40; pipeline/roles/asset-specialist.md:10,20,42 | lane_guard file lanes; Art/Source and Content/UmbrellaElla/Art |
| Art Pipeline:236-239 | Version history and backups; cloud sync is not VCS | ADAPTED | .gitattributes:1-5; AGENTS.md:61 | pipeline_check LFS bytes; git plus LFS |
| Art Pipeline:240 | Checkpoint at review boundaries, no overwrite | ADAPTED | AGENTS.md:136-137 | doc only; git commits, squash per card |
| Art Pipeline:241 | Keep engine asset identities stable; no delete-recreate | COVERED | pipeline/roles/asset-specialist.md:34,40,54 | doc only; reimport in place, Fix Up Redirectors |
| Art Pipeline:242 | Experiments, caches, logs isolated from sources | ADAPTED | pipeline/roles/asset-specialist.md:42; AGENTS.md:97 | doc only; Raw/ folder, rejected outside Content |
| Art Pipeline:243 | No secrets, machine profiles, caches, binaries committed | STRENGTHENED | AGENTS.md:97,102,108 | pipeline_check / secrets_check |
| Art Pipeline:244 | Binary locking for concurrent editors | STRENGTHENED | AGENTS.md:16,60; .gitattributes:3-4; pipeline/roles/asset-specialist.md:32 | `lockable` LFS attribute; locks shown at session start |
| Art Pipeline:245-246 | Prove backups restore source plus bindings | ADAPTED | pipeline/roles/qa-build.md:36; pipeline/checklists/submission.md:26 | gate; package from a fresh clone |
| Art Pipeline:247-250 | One stable ID across revisions; no rename per edit | STRENGTHENED | pipeline/roles/asset-specialist.md:44 | sprite_check --names fails `_v2`/`_final`/`_new` |
| Art Pipeline:251-259 | Example filenames; no assumed suffix or canvas | DROPPED | - | (a) other tool's naming; ours has its own naming rule |
| Art Pipeline:260-262 | No flattened-only masters, no overwrite, no uncoordinated rename | COVERED | pipeline/roles/asset-specialist.md:20,34,42,54 | doc only |
| Art Pipeline:262 | Command success is not file-integrity evidence | COVERED | AGENTS.md:73-77; pipeline/roles/asset-specialist.md:37 | sprite_check --scan decodes files |
| Art Pipeline:262 | No auto-delete of inputs after conversion | ADAPTED | AGENTS.md:67-68; pipeline/roles/asset-specialist.md:42 | doc only; humans approve deleting others' work, raw kept |
| Art Pipeline:263-270 | Read brief and profile before starting | COVERED | AGENTS.md:10-13; pipeline/templates/asset-brief.md:3 | doc only |
| Art Pipeline:271 | Block silhouette and function first | COVERED | pipeline/roles/asset-specialist.md:36 | doc only; `_PH` silhouette flipbook first |
| Art Pipeline:272-274 | Coherent form, review at scale, selective detail | ADAPTED | pipeline/art/art-bible.md:28-33; pipeline/roles/art-director.md:40 | art_check; dark-on-dark interior detail rule |
| Art Pipeline:275 | Variants from a common base | COVERED | pipeline/roles/asset-specialist.md:35 | doc only; anchor first per family |
| Art Pipeline:276-277 | Save layered source; verify export independently | COVERED | pipeline/roles/asset-specialist.md:20,37 | sprite_check --scan |
| Art Pipeline:278-280 | Review request with evidence and limits; integrate | COVERED | pipeline/templates/asset-brief.md:27-37 | required field (handoff block, Known limits, Next) |
| Art Pipeline:281-283 | Family anchors set shared heights and joins | ADAPTED | pipeline/roles/asset-specialist.md:35; pipeline/art/art-bible.md:52-62 | doc only; size table instead of furniture heights |
| Art Pipeline:284-285 | Test modular assemblies under sorting and light | STRENGTHENED | pipeline/checklists/animation-review.md:20-22 | sprite_check tile seam ΔE76 |
| Art Pipeline:286-287 | Dressing stays below gameplay; art adds no playable areas | COVERED | pipeline/art/art-bible.md:7-9,32; pipeline/roles/art-director.md:25 | gate "atmosphere subordinate" |
| Art Pipeline:288-289 | Gameplay geometry not from opaque pixels | COVERED | pipeline/art/import-rules.md:59; pipeline/templates/asset-brief.md:34 | --import-report `collision` |
| Art Pipeline:290-293 | Character-scale anchor before multiplying | COVERED | pipeline/roles/asset-specialist.md:35; pipeline/day0-cards.md:50 | gate |
| Art Pipeline:294-295 | No unapproved staff personality signaling | DROPPED | - | (a) other game's staff system |
| Art Pipeline:296-298 | Each motion maps to a semantic state | COVERED | pipeline/templates/asset-brief.md:11; pipeline/checklists/animation-review.md:17 | required field |
| Art Pipeline:299-301 | Animation shows only approved states | ADAPTED | pipeline/roles/art-director.md:8 | doc only; owl and Ella state list (D38) |
| Art Pipeline:302-303 | Per-family animation documentation fields | STRENGTHENED | pipeline/templates/asset-brief.md:10-15; pipeline/art/import-rules.md:64-65 | --import-report fps/frames/socket |
| Art Pipeline:304-305 | No invented frame counts or rates before profile | ADAPTED | pipeline/art/art-bible.md:68-70 | sprite_check anims row; DISPUTABLE: ours fixes rates up front, changes on evidence |
| Art Pipeline:305-306 | No jitter, sliding, vanishing props, identical cues | STRENGTHENED | pipeline/checklists/animation-review.md:8-13 | sprite_check pivot drift ≤ 2 px; one pivot per asset |
| Art Pipeline:307-308 | Clip end never authorizes gameplay facts | COVERED | pipeline/unreal/gameplay-code.md:64; pipeline/checklists/animation-review.md:18 | doc only |
| Art Pipeline:309-311 | UI hierarchy from UX; never hue alone | STRENGTHENED | pipeline/roles/ui-ux.md:13; pipeline/ui/accessibility.md:17,67 | ui_check.py grayscale (U5) |
| Art Pipeline:311 | Text and prompts dynamic, not baked into images | COVERED | pipeline/ui/accessibility.md:50 | RemapUpdatesPrompt test (E2) |
| Art Pipeline:311 | Text scaling and controller focus | COVERED | pipeline/ui/accessibility.md:25,85,89 | ui_check layout --scale 2; UIFLOW |
| Art Pipeline:311 | Localization, text expansion, glyph fallback | ADAPTED | pipeline/ui/accessibility.md:25 | DISPUTABLE: no localization in a 4-day jam; 2.0 text scale stands in for expansion |
| Art Pipeline:312-314 | Fictional currency; pseudo-localization; no language choice | DROPPED | - | (a) other game's currency; localization out of jam scope |
| Art Pipeline:315-317 | Cue purpose, onset, priority; no needless flashing | STRENGTHENED | pipeline/templates/asset-brief.md:25; pipeline/ui/accessibility.md:18 | ui_check.py flashes (U6) |
| Art Pipeline:318-322 | Illustrations are not masters; label accepted traits | COVERED | pipeline/art/art-bible.md:7-9; pipeline/roles/asset-specialist.md:17; pipeline/roles/art-director.md:12 | doc only; never cut sprites from key art |
| Art Pipeline:323-333 | Historical image-tool trial findings | DROPPED | - | (a) other tool's trial history |
| Art Pipeline:334-337 | Approved tool chosen per work package | ADAPTED | pipeline/art/art-bible.md:92 | provenance row records tool, model, version |
| Art Pipeline:338-339 | Confirm real tool version; no banned substitutes | ADAPTED | pipeline/templates/asset-brief.md:18; pipeline/roles/asset-specialist.md:33 | required field (Banned); GIMP layer ops dropped (a) |
| Art Pipeline:340-343 | Confirm authorization, allowed paths, stop budget | STRENGTHENED | AGENTS.md:9,60; pipeline/templates/task-card.md:24; pipeline/templates/asset-brief.md:21-22 | lane_guard (JAM_ROLE), File lane |
| Art Pipeline:344 | Isolated work directory and tool state | ADAPTED | pipeline/roles/asset-specialist.md:42; AGENTS.md:60 | doc only; branch per card and Raw/ folder |
| Art Pipeline:345 | Read tool help; machine-readable argument files | DROPPED | - | (a) specific to that command-line tool |
| Art Pipeline:346 | Small anchor reviewed before batch expansion | COVERED | pipeline/roles/asset-specialist.md:35 | doc only |
| Art Pipeline:347 | Bounded batches; capture responses and failures | ADAPTED | pipeline/roles/asset-specialist.md:46; AGENTS.md:83; tools/prompt_log.py | generation budget count in PR; prompt log |
| Art Pipeline:348 | Independently decode and check outputs | STRENGTHENED | pipeline/roles/asset-specialist.md:37; AGENTS.md:120 | sprite_check --scan Art in CI |
| Art Pipeline:349 | Contact sheets never replace in-engine inspection | STRENGTHENED | pipeline/roles/art-director.md:40 | source PNG alone = auto request_changes |
| Art Pipeline:350 | End cleanly; keep logs, scripts, tool versions | COVERED | AGENTS.md:86; pipeline/art/art-bible.md:92 | journal.py checkpoint; provenance row |
| Art Pipeline:351-352 | Never auto-delete sources or checkpoints | COVERED | pipeline/roles/asset-specialist.md:42; AGENTS.md:67-68 | doc only |
| Art Pipeline:353-354 | Recipes and handles are not reproduction evidence | ADAPTED | pipeline/roles/asset-specialist.md:42 | doc only; "a seed is a record, not proof" |
| Art Pipeline:355-357 | Self-contained agent brief; no inherited context | COVERED | pipeline/templates/asset-brief.md:3-4 | doc only; card alone must suffice |
| Art Pipeline:358-359 | Report real states; tool success is not acceptance | COVERED | pipeline/roles/art-director.md:40,75; AGENTS.md:77,93 | doc only |
| Art Pipeline:360-363 | Partial failure: stop, capture error, classify, bounded retry | ADAPTED | AGENTS.md:83-84 | doc only; stop at second same failure, cause class, no changed-file list |
| Art Pipeline:364-369 | Versioned export profiles; asset declares its profile | STRENGTHENED | pipeline/art/style.json; pipeline/roles/asset-specialist.md:37 | sidecar required; PNG without one fails --scan |
| Art Pipeline:370-373 | Hard-fail list for source and export | STRENGTHENED | pipeline/art/import-rules.md:50-68; pipeline/roles/asset-specialist.md:30,37 | sprite_check --scan / --import-report / --names; missing source is doc only |
| Art Pipeline:374-377 | Taste issues warn only; no hard pixel rules | ADAPTED | pipeline/roles/art-director.md:34,38; tools/art_check.py:171-187 | DISPUTABLE: ours hard-fails palette and texture numbers; taste alone never fails |
| Art Pipeline:378-381 | Tier 1 file check on every export | STRENGTHENED | AGENTS.md:120 | sprite_check --scan in CI |
| Art Pipeline:382 | Tier 2: reopen source, confirm still editable | PORTED | pipeline/roles/asset-specialist.md:39; tools/sprite_check.py | `sprite_check.py --sources` (SourcesTests) |
| Art Pipeline:383 | Tier 3 family check: order, seams, anchors | STRENGTHENED | pipeline/checklists/animation-review.md:5-22 | --import-report keyframe order, pivot, tile seam |
| Art Pipeline:384 | Tier 4 engine check: import, binding, sorting, scale | STRENGTHENED | pipeline/roles/asset-specialist.md:29,40,45; pipeline/unreal/gameplay-code.md:67 | --import-report; BP_* reference test |
| Art Pipeline:385-386 | Tier 5 regression on shared profile change | COVERED | pipeline/roles/art-director.md:49 | doc only; re-run art_check on all captures |
| Art Pipeline:387-388 | Validator owners; failed hard check blocks promotion | STRENGTHENED | pipeline/roles/art-director.md:38; pipeline/roles/technical-director.md | "Any FAIL is request_changes. You cannot override" |
| Art Pipeline:389-405 | Illustrative manifest shape | ADAPTED | pipeline/roles/asset-specialist.md:37; pipeline/art/provenance.csv | .sprite.json sidecar plus provenance row |
| Art Pipeline:406-412 | Imports implementation-owned; art supplies metadata | ADAPTED | pipeline/roles/asset-specialist.md:4,29; pipeline/art/import-rules.md:1-6 | Asset Specialist imports; TD owns the rules |
| Art Pipeline:413 | Semantic truth outside presentation | COVERED | pipeline/unreal/gameplay-code.md:21,47 | doc only |
| Art Pipeline:414 | Art variants change without recreating definitions | ADAPTED | pipeline/roles/asset-specialist.md:40; pipeline/unreal/gameplay-code.md:67 | BP_* reference test |
| Art Pipeline:415 | One-way sim-to-render transform | COVERED | pipeline/unreal/gameplay-code.md:47 | doc only |
| Art Pipeline:416 | Spatial metadata explicit, not from image bounds | STRENGTHENED | pipeline/art/import-rules.md:59,64 | --import-report `collision`, `socket` |
| Art Pipeline:417 | Sorting testable via overlays and congested layouts | ADAPTED | pipeline/unreal/gameplay-code.md:65; pipeline/roles/integrator.md:30 | CAM_Eval_Stress capture; no debug overlay |
| Art Pipeline:418 | Animation is presentation only | COVERED | pipeline/unreal/gameplay-code.md:64 | doc only |
| Art Pipeline:419 | Localization and formatting data-driven | ADAPTED | pipeline/ui/accessibility.md:50 | E2 test for prompts; DISPUTABLE: localization dropped |
| Art Pipeline:420-421 | Measure render cost; no budget without profiling | ADAPTED | pipeline/roles/qa-build.md:32; pipeline/roles/art-director.md:51 | stat unit; DISPUTABLE: ours proposes budgets (16.7 ms, GPU ≤ 8 ms) before profiling |
| Art Pipeline:422-425 | Engine acceptance fixture per family incl. failure cases | STRENGTHENED | pipeline/art/import-rules.md:46-48; pipeline/unreal/gameplay-code.md:67; AGENTS.md:79 | tests/test_sprite_check.py fixtures; evidence header |
| Art Pipeline:426-429 | Import values locked only after tech evidence | STRENGTHENED | pipeline/art/import-rules.md:5-6,68 | `--gate` fails until `unreal_import.status` verified |
| Art Pipeline:430-435 | One-step replace, validate, reimport, preview loop | PORTED | pipeline/day0-cards.md:49 | card 0.10b times the round trip; over 10 min the TD files a one-command loop card |
| Art Pipeline:436-438 | Defects appear in context; review in scenarios | COVERED | pipeline/roles/art-director.md:40,47 | CAM_Eval_* captures |
| Art Pipeline:439-448 | Other game's scenario matrix | ADAPTED | pipeline/art/art-bible.md:43-44 | Arena, Stress, StyleFrame, Swatch cameras |
| Art Pipeline:449 | Controller, accessibility review context | COVERED | pipeline/ui/accessibility.md:13-25,85-89 | ui_check; UIFLOW |
| Art Pipeline:450 | Stress-density performance context | COVERED | pipeline/roles/qa-build.md:32 | stat unit at CAM_Eval_Stress |
| Art Pipeline:451-453 | No invented crowd-readability success percentage | ADAPTED | pipeline/ui/accessibility.md:17; pipeline/qa/playtests.md | DISPUTABLE: ours sets measured thresholds (L* gap ≥ 20) |
| Art Pipeline:454-460 | AD review rubric questions | COVERED | pipeline/roles/art-director.md:23-25 | required field (gates with location) |
| Art Pipeline:461-463 | Finding: defect, correction, protected parts, retest | COVERED | pipeline/roles/art-director.md:27-28,34 | required field; preference alone never fails |
| Art Pipeline:464-470 | Blocker, major, minor, enhancement classes | COVERED | pipeline/roles/art-director.md:27,35 | doc only; enhancement = preference |
| Art Pipeline:471-472 | Accepted exceptions need traceable disposition | COVERED | pipeline/roles/art-director.md:30,35 | required field (issue link) |
| Art Pipeline:473-475 | Revision loop; stop endless iteration; scoped fixes | COVERED | pipeline/roles/art-director.md:50; AGENTS.md:90; pipeline/roles/asset-specialist.md:41 | stuck rule (3 flat rounds, D-new-no-round-cap) with cause |
| Art Pipeline:476-480 | Escalate conflicts to owners with alternatives | COVERED | AGENTS.md:30-31,53,131; pipeline/roles/art-director.md:78 | decision row format |
| Art Pipeline:481-485 | Shared anchor or profile change needs impact check | COVERED | pipeline/roles/art-director.md:49 | doc only |
| Art Pipeline:486-487 | Significant change record with rollback | ADAPTED | AGENTS.md:31,135; docs/decisions.md | decision row; one squash commit per card is the rollback |
| Art Pipeline:488-489 | Rebuild only the dependent set | ADAPTED | pipeline/roles/asset-specialist.md:41 | doc only; diff shows no other art file |
| Art Pipeline:490-491 | No ID recycling; alias and migration policy | ADAPTED | pipeline/roles/asset-specialist.md:34 | doc only; redirectors; save compatibility dropped |
| Art Pipeline:492-493 | Rejected or historical art is not accepted content | COVERED | pipeline/roles/asset-specialist.md:42; docs/port-log.md:49 | doc only; trial specifics dropped (a) |
| Art Pipeline:494-508 | Sequence by family anchors; producer sets order | ADAPTED | pipeline/day0-cards.md:48-50; pipeline/roles/producer.md | gate; Day 0 card order |
| Art Pipeline:509-512 | Estimate whole family; validate multiplier first | ADAPTED | pipeline/roles/asset-specialist.md:36; pipeline/art/import-rules.md:65 | 60 sprite cap; frame count confirmed on `_PH` pass |
| Art Pipeline:513-516 | Bound active families; finish one vertically | ADAPTED | pipeline/roles/producer.md:53; pipeline/roles/asset-specialist.md:35 | check_card --queue; DISPUTABLE: ours sets a fixed cap of 3 |
| Art Pipeline:517-521 | Decision-useful metrics, not output counts | ADAPTED | pipeline/roles/producer.md:21 | check_card --status; no art rework metrics |
| Art Pipeline:522-528 | Qualification 0: document approval | DROPPED | - | (b) executive approval |
| Art Pipeline:529-530 | Qualification 1: foundational visual and tech proof | STRENGTHENED | pipeline/day0-cards.md:48-50 | art_check --swatch PASS, art_check on style frame |
| Art Pipeline:531-532 | Qualification 2: edit, reimport, identity survives | PORTED | pipeline/day0-cards.md:49 | card 0.10b Done-when: round trip pasted (`--import-report`, `--sources`) |
| Art Pipeline:533-534 | Qualification 3: vertical family proof in context | ADAPTED | pipeline/roles/asset-specialist.md:35-36; pipeline/checklists/animation-review.md | doc only; anchor and motion first per family |
| Art Pipeline:535-536 | Qualification 4: broad rollout after proofs | COVERED | pipeline/day0-cards.md:50 | gate; no other asset cards before 0.10 |
| Art Pipeline:537-541 | Stop conditions; report precise blocker | COVERED | AGENTS.md:83-89; pipeline/templates/asset-brief.md:22; pipeline/roles/art-director.md:39 | stop rules; no swatch PASS, no verdict |
| Art Pipeline:542-565 | Asset brief template | COVERED | pipeline/templates/asset-brief.md:6-24 | required field (card-ready) |
| Art Pipeline:566-580 | Art review record template | COVERED | pipeline/roles/art-director.md:20-32 | required field |
| Art Pipeline:581-596 | Integration handoff template | COVERED | pipeline/templates/asset-brief.md:27-37 | required field |
| Art Pipeline:597-613 | Experiment record template | STRENGTHENED | pipeline/templates/spike-card.md:9-26 | check_card spike fields, 60 min time box |
| Art Pipeline:614-631 | Open decisions with owners and triggers | ADAPTED | docs/decisions.md:28; pipeline/art/import-rules.md:18,72 | decision rows; doc-status verification dropped (b) |
| Art Pipeline:632-636 | No dependent bulk work before profile decisions | ADAPTED | AGENTS.md:30-31; pipeline/day0-cards.md:50 | gate; ours builds the default meanwhile |
| Art Pipeline:637-641 | Routine work without re-review; evidence-backed updates | ADAPTED | AGENTS.md:67-68,98 | doc only; threshold changes need a measurement |
| Art Pipeline:642-649 | Release integrity: say what was not produced | COVERED | AGENTS.md:77; pipeline/roles/asset-specialist.md:42 | doc only; "Not run" section |
| Art Pipeline:650 | End stamp | DROPPED | - | (b) no rule content |

### inherited: Art Director charter

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Art Director charter:1-17 | Title block, version stamps, approvals | DROPPED | - | no rule content |
| Art Director charter:18-27 | AD protects visual identity within gameplay and tech limits | COVERED | pipeline/roles/art-director.md:3-4; pipeline/art/art-bible.md:35 | doc only |
| Art Director charter:28-29 | Not an agreement machine or image service | ADAPTED | pipeline/roles/art-director.md:33-35 | doc only; independence expressed as a strict gate format, not persona |
| Art Director charter:30-38 | Duties: judge, direct, set standards, review deliverables, find problems | COVERED | pipeline/roles/art-director.md:7-12; pipeline/roles/art-director.md:37-55 | doc only; review procedure |
| Art Director charter:39 | Challenge unsound decisions, even from the heads | PORTED | pipeline/roles/art-director.md:57 | review step 15: §9 block + decision row; owner Creative director |
| Art Director charter:40-43 | Keep continuity, improve methods, stay accountable | ADAPTED | docs/decisions.md:11-16; pipeline/templates/gate-record.md:18,31 | check_card.py --gate-record; continuity moved to shared decisions log and gate retro |
| Art Director charter:44-49 | Bounded autonomy; no scope or resource expansion | COVERED | AGENTS.md:67-68; AGENTS.md:85 | doc only; stop rule |
| Art Director charter:50-73 | Layer heading, identity and seniority persona | DROPPED | - | no rule content |
| Art Director charter:74-86 | Priority order: vision first, readability third | ADAPTED | pipeline/art/art-bible.md:35 | doc only; DISPUTABLE: ours ranks readability above style ("these beat style") |
| Art Director charter:87-92 | Choose hands-on work vs delegation | ADAPTED | pipeline/roles/art-director.md:75; pipeline/roles/asset-specialist.md:3-4 | doc only; maker and judge split into two roles |
| Art Director charter:93-122 | Make anchor or prototype assets when language unset | ADAPTED | pipeline/day0-cards.md:49-50; pipeline/roles/asset-specialist.md:35 | gate (card 0.10 style frame); anchors made by Asset Specialist, judged by AD |
| Art Director charter:123-191 | Expertise discipline lists | DROPPED | - | no rule content |
| Art Director charter:192-197 | Craft before quantity | ADAPTED | pipeline/templates/asset-brief.md:21; pipeline/roles/producer.md:54 | required field (Generation budget); no bulk assets before style frame |
| Art Director charter:198-201 | Know what an asset communicates first | COVERED | pipeline/templates/asset-brief.md:8 | required field (Purpose) |
| Art Director charter:202-205 | Readability before ornament | STRENGTHENED | pipeline/art/art-bible.md:35-41; pipeline/roles/art-director.md:47,63 | art_check.py; sprite_check.py --width-ratio; grayscale read check |
| Art Director charter:206-211 | Coherence before novelty, protect identity | COVERED | pipeline/roles/art-director.md:25,59-66 | gate ("matches accepted assets"; auto-fails) |
| Art Director charter:212-215 | Prototype before permanent standards | COVERED | pipeline/art/art-bible.md:52; pipeline/roles/art-director.md:77; pipeline/day0-cards.md:50 | gate (style frame first); measured evidence to change |
| Art Director charter:216-219 | Weigh total cost of producing and animating art | ADAPTED | docs/decisions.md:23; docs/jam-brief.md:11; pipeline/checklists/card-ready.md:15 | check_card.py frame cap; cost expressed as 60-frame budget (D38) |
| Art Director charter:220-223 | Independent judgment over agreement | ADAPTED | pipeline/roles/art-director.md:33-35 | doc only; same as AD:28-29 |
| Art Director charter:224-227 | Separate fact, interpretation, preference, assumption | COVERED | pipeline/roles/art-director.md:27,34 | required field (measured/observed/preference tag) |
| Art Director charter:228-233 | Own outcomes, respect other departments | COVERED | pipeline/roles/art-director.md:76-78 | doc only |
| Art Director charter:234-262 | Project-agnostic; no aesthetic carry-over between projects | ADAPTED | AGENTS.md:21; pipeline/art/art-bible.md:3-5 | doc only; ours is project-specific by design, other package not loaded |
| Art Director charter:263-290 | Executive authority; titles must be set by governance | STRENGTHENED | AGENTS.md:53; docs/decisions.md:7-8,17 | pipeline_check.py (owner must be a People seat); D34 creative director |
| Art Director charter:291-311 | AD owns art dept, not scope/gameplay/architecture | COVERED | pipeline/roles/art-director.md:7-10,76,78 | doc only |
| Art Director charter:312-327 | Recommend / decide / initiate / commit distinction | ADAPTED | AGENTS.md:67-68 | doc only; collapsed to routine work vs human-approved list |
| Art Director charter:328-350 | Brief or need is not authorization; work needs a package | STRENGTHENED | AGENTS.md:57-58; pipeline/checklists/card-ready.md:3 | check_card.py (no card, no work; empty field = not ready) |
| Art Director charter:351-376 | Delegated decision matrix | ADAPTED | AGENTS.md:67-68; pipeline/agent-ops/gates.json:11,13 | agent-ops hook gates style.json and roles; matrix replaced by human-approve list |
| Art Director charter:377-390 | Independent approval threshold for routine decisions | ADAPTED | AGENTS.md:67-68; AGENTS.md:85 | doc only; same list plus split-proposal stop rule |
| Art Director charter:391-404 | Materiality test | ADAPTED | AGENTS.md:30-31; AGENTS.md:85 | doc only; material = conflict or out-of-card change → decision row or split |
| Art Director charter:405-422 | Recommendation, prototype, silence, done task are not approval | COVERED | docs/decisions.md:5,12-13; pipeline/templates/spike-card.md:26; AGENTS.md:63,93 | gate (human merges; spike never decides) |
| Art Director charter:423-437 | Challenge is an obligation when proposal breaks standards | PORTED | pipeline/roles/art-director.md:57 | review step 15: §9 block + decision row; owner Creative director |
| Art Director charter:438-446 | Challenge must state concern, consequence, alternative, decision | COVERED | AGENTS.md:132-133; pipeline/templates/task-card.md:46 | required field (Unknowns) |
| Art Director charter:447-450 | Don't pass preference off as objective | COVERED | pipeline/roles/art-director.md:34 | doc only (preference alone never request_changes) |
| Art Director charter:451-463 | After decision: record tradeoffs, don't reopen without evidence | COVERED | docs/decisions.md:12,15 | doc only (reopen only with new measurement) |
| Art Director charter:464-485 | Executive change requests; material ones go via Production | ADAPTED | AGENTS.md:67-68; pipeline/roles/art-director.md:45; AGENTS.md:85 | doc only; 7-step change flow becomes human sign-off plus split card |
| Art Director charter:486-507 | Respect other disciplines' decision rights | COVERED | AGENTS.md:37-51; pipeline/roles/art-director.md:76,78 | check_card.py --lanes; agent-ops hook |
| Art Director charter:508-533 | Art acceptance is not tech, production or exec acceptance | COVERED | pipeline/roles/art-director.md:48; AGENTS.md:64 | doc only; separate reviewer verdicts |
| Art Director charter:534-551 | Proactively spot inconsistencies, risks, accessibility | ADAPTED | pipeline/roles/art-director.md:10,47 | doc only; per-PR full-scene arena capture instead of free audits |
| Art Director charter:552-568 | Permitted autonomous activities without a package | ADAPTED | AGENTS.md:57-58,66-67 | check_card.py; DISPUTABLE: ours needs a card for any work, his allowed unprompted audits |
| Art Director charter:569-578 | Approval needed: scope, overwrite, compute, direction, standards | STRENGTHENED | AGENTS.md:67-68,92-98; pipeline/agent-ops/gates.json:11-13; pipeline/agent-ops/README.md:122-124 | agent-ops hook; prompt_log.py daily_token_cap |
| Art Director charter:579 | Approval before engaging paid vendors | PORTED | pipeline/roles/agent-ops.md:73; pipeline/templates/asset-brief.md:17 | doc only; `Spend OK:` link by a named human; brief `Tool:` field |
| Art Director charter:580-584 | No changing direction, standards, others' docs, irreversible acts | STRENGTHENED | AGENTS.md:95,97-98; pipeline/roles/art-director.md:77 | agent-ops hook (style.json gated); never force-push |
| Art Director charter:585-603 | Work inside an explicit resource envelope | STRENGTHENED | pipeline/templates/asset-brief.md:21-22; pipeline/checklists/card-ready.md:9; pipeline/roles/asset-specialist.md:46 | check_card.py Budget; required field (Generation budget, Stop if) |
| Art Director charter:604-609 | No arbitrary universal numeric limits | ADAPTED | pipeline/checklists/card-ready.md:9 | check_card.py; DISPUTABLE: ours sets universal caps (120 min agent, 60 min human) |
| Art Director charter:610-624 | No envelope: assess, propose package, ask | COVERED | AGENTS.md:57-58,84 | check_card.py; split proposal |
| Art Director charter:625-646 | Experiments: hypothesis, limits, success/fail, stop | STRENGTHENED | pipeline/templates/spike-card.md:9-26 | check_card.py (Decision row, Decides it, Time box ≤ 60) |
| Art Director charter:647-664 | Consult other owners, keep working, track, escalate | ADAPTED | AGENTS.md:30-31,64-65,87 | check_card.py --blocked-by; consultation becomes decision row or GitHub comment |
| Art Director charter:665-682 | Consultation brief template | ADAPTED | docs/decisions.md:21; AGENTS.md:132-133 | pipeline_check.py (owner); fields Decision/Why/Default/Test/Owner/Blocks, no consultation ID |
| Art Director charter:683-698 | Consultation states; never fabricate consensus | COVERED | AGENTS.md:66; docs/decisions.md:5 | doc only ("prepared, not posted") |
| Art Director charter:699-708 | Agents can't talk directly; portable handoff | COVERED | AGENTS.md:65-66 | doc only |
| Art Director charter:709-752 | Discover-to-handoff creative workflow | ADAPTED | pipeline/roles/art-director.md:12; pipeline/roles/producer.md:54; pipeline/templates/asset-brief.md:15,27-38 | gate (style frame, motion pass, handoff block); fixed sequence not named stages |
| Art Director charter:753-811 | Four response levels scaled to request | ADAPTED | pipeline/roles/art-director.md:20-35; AGENTS.md:132-133 | doc only; one fixed review format plus Unknowns format |
| Art Director charter:812-819 | Delegation keeps artistic accountability | ADAPTED | pipeline/roles/asset-specialist.md:49; pipeline/roles/art-director.md:10 | gate (AD review); AD reviews, Asset Specialist makes |
| Art Director charter:820-842 | Ten-state control sequence; don't claim started/accepted | ADAPTED | AGENTS.md:63,65,69; AGENTS.md:77 | doc only; collapsed to todo/doing/review/done/blocked |
| Art Director charter:843-860 | Delegation readiness: authorized, scoped, testable, capable | STRENGTHENED | pipeline/checklists/card-ready.md:3-22; AGENTS.md:17 | check_card.py; CAN RUN line |
| Art Director charter:861-889 | Production brief fields, context-free | ADAPTED | pipeline/templates/asset-brief.md:3-24; pipeline/checklists/card-ready.md:7; pipeline/roles/asset-specialist.md:20 | card-ready checklist; no Allowed tools or Output format field; editability is a role rule |
| Art Director charter:890-906 | Artistic review criteria list | STRENGTHENED | pipeline/roles/art-director.md:22-25,38 | art_check.py; gates need image location |
| Art Director charter:907-921 | Technical evidence: integrity, size, alpha, export | STRENGTHENED | pipeline/roles/asset-specialist.md:29,37; pipeline/roles/art-director.md:48 | sprite_check.py --scan, --import-report |
| Art Director charter:922-941 | Revision request fields, scoped, bounded iterations | COVERED | pipeline/roles/art-director.md:27-28; pipeline/roles/asset-specialist.md:41; AGENTS.md:90 | required field (finding block); stuck rule (D-new-no-round-cap) |
| Art Director charter:942-952 | Repeated failure: diagnose brief/tool/agent/criteria | COVERED | pipeline/roles/art-director.md:50 | required field (blocked cause) |
| Art Director charter:953-966 | Closure needs inspection, limits listed; output ≠ accepted | COVERED | pipeline/roles/art-director.md:30,35,40; pipeline/roles/asset-specialist.md:42,56; AGENTS.md:63 | gate (source PNG alone auto-fails; human merges) |
| Art Director charter:967-978 | Knowledge must not live only in chat | COVERED | AGENTS.md:19,64 | doc only (GitHub is the shared truth) |
| Art Director charter:979-1000 | Seven continuity registers; no redundant systems | ADAPTED | docs/decisions.md; pipeline/art/art-bible.md; docs/jam-brief.md:73; pipeline/templates/spike-card.md:24-25 | doc only; reference register dropped, review register = PR comments |
| Art Director charter:1001-1019 | Minimum decision record fields | ADAPTED | docs/decisions.md:11-21 | pipeline_check.py (cited IDs, owners); fewer fields (no alternatives column) |
| Art Director charter:1020-1039 | Status vocabulary; positive reaction is not approval | ADAPTED | docs/decisions.md:5,11-16 | doc only; open/DECIDED/SUPERSEDED plus default, no Deferred/Exploratory |
| Art Director charter:1040-1053 | Record depth scales with task size | ADAPTED | pipeline/roles/art-director.md:27-30; AGENTS.md:30-31 | doc only; findings in PR, only tradeoffs become rows |
| Art Director charter:1054-1066 | Start: find governing docs, hierarchy, baseline | STRENGTHENED | AGENTS.md:5-20,23-31 | agent.sh JAM_ROLE launch; first-output git status/CAN RUN |
| Art Director charter:1067-1076 | Missing documents: say so, don't invent | COVERED | AGENTS.md:30-31; pipeline/checklists/card-ready.md:6 | doc only (missing rule → decision row) |
| Art Director charter:1077-1086 | Stale documents: newest is not automatically authoritative | STRENGTHENED | AGENTS.md:7-8; pipeline/roles/producer.md:16; pipeline/checklists/card-ready.md:17 | gdd_impact.py; check_card.py fails changed Features |
| Art Director charter:1087-1097 | Conflicting sources: owner, recommend, hold disputed part | COVERED | AGENTS.md:30-31 | doc only (build default, name row) |
| Art Director charter:1098-1111 | Never claim unread files, unrun tools, unsent messages | COVERED | AGENTS.md:17,65,76 | check_pr.py evidence header; "Not run" lines |
| Art Director charter:1112-1133 | End-of-session summary, persist or copyable | STRENGTHENED | AGENTS.md:86; .github/PULL_REQUEST_TEMPLATE.md:26,28 | journal.py checkpoint/export; check_pr.py journal and Next: |
| Art Director charter:1134-1146 | Resume from records, not recollection | STRENGTHENED | AGENTS.md:18-19 | journal.py resume; re-run claimed checks |
| Art Director charter:1147-1161 | Supersession keeps IDs, links, history | STRENGTHENED | docs/decisions.md:3,16; pipeline/roles/producer.md:16; AGENTS.md:80 | pipeline_check.py (cited IDs must resolve) |
| Art Director charter:1162-1204 | Curated register of professional references | DROPPED | - | (b) reading-list upkeep, no rule; port-log rejects reference registers |
| Art Director charter:1205-1220 | Authority order; evidence proposes, doesn't override | COVERED | AGENTS.md:23-32,98; docs/decisions.md:15 | doc only |
| Art Director charter:1221-1241 | Reference record; don't present unverified as fact | ADAPTED | docs/references.md:1-26; pipeline/unreal-rules.md:10; AGENTS.md:78 | doc only; [VERIFY] tags and header citations instead of per-reference records |
| Art Director charter:1242-1359 | Specific external references and research targets | DROPPED | - | no rule content |
| Art Director charter:1360-1381 | Keep current on practices; don't silently adopt | DROPPED | - | (c) agent cannot stay current across sessions; adoption already gated (gates.json) |
| Art Director charter:1382-1414 | Propose role-instruction improvements; no self-edit | STRENGTHENED | pipeline/agent-ops/gates.json:2,11; pipeline/templates/gate-record.md:18,31 | agent-ops hook blocks role edits; check_card.py --gate-record retro line |
| Art Director charter:1415-1436 | Performance dimension table | DROPPED | - | (b) self-evaluation overhead with no checkable use |
| Art Director charter:1437-1448 | Correct mistakes, re-evaluate on evidence | COVERED | AGENTS.md:80; docs/decisions.md:15 | doc only |
| Art Director charter:1449-1467 | Milestone self-review with evidence | ADAPTED | pipeline/templates/gate-record.md:18,31 | check_card.py --gate-record; team retro per gate, not role self-review |
| Art Director charter:1468-1489 | 1-5 self-rating scale | DROPPED | - | (b) self-ratings rejected (port-log); no use in a 4-day jam |
| Art Director charter:1490-1511 | Integrity list: honest states, preference vs evidence | COVERED | AGENTS.md:72-80; pipeline/roles/art-director.md:34; docs/decisions.md:15 | doc only; "challenge" item is the AD:423 gap |
| Art Director charter:1512-1537 | Shared protocol later; no conflicting policies | STRENGTHENED | AGENTS.md:1-3,53 | pipeline_check.py cross-doc consistency |
| Art Director charter:1538-1560 | Activation: identify project, docs, authority, records | COVERED | AGENTS.md:5-20 | agent.sh launch; first-output lines |
| Art Director charter:1561-1568 | Simulated perspectives are not independent reviews | COVERED | AGENTS.md:52; pipeline/roles/art-director.md:75 | doc only |
| Art Director charter:1569-1582 | Confirm real capability; review outputs; evidence | COVERED | AGENTS.md:17,73-76 | CAN RUN line; check_pr.py evidence |
| Art Director charter:1583-1590 | Handoff via real channel; prepared vs submitted | COVERED | AGENTS.md:65-66 | doc only |
| Art Director charter:1591-1606 | Smallest set of governing docs per task | STRENGTHENED | AGENTS.md:5,13 | pipeline_check.py word cap |
| Art Director charter:1607-1632 | Purpose-to-next-decision communication; tone | ADAPTED | AGENTS.md:132-133; pipeline/roles/art-director.md:20-32 | required field (Unknowns); tone lines no rule content |
| Art Director charter:1633-1656 | Compact directive; companions must not compete | STRENGTHENED | CLAUDE.md:5; tools/secrets_check.py:344 | secrets_check.py (agent file is a pointer only) |
| Art Director charter:1657-1692 | Commitment slogans | DROPPED | - | no rule content; principles already rows AD:192-233 |
| Art Director charter:1693-1707 | Document control block | DROPPED | - | no rule content |

### inherited: Design Pipeline

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Design Pipeline:1-13 | Header, version, owner, scope boilerplate | DROPPED | - | (b) no rule content; approval metadata |
| Design Pipeline:14-15 | Operating principle: specify, prototype, test, hand off | COVERED | AGENTS.md:30-31; AGENTS.md:86; pipeline/templates/spike-card.md:4 | doc only; each part has its own row below |
| Design Pipeline:16-21 | Design stays active through production, not one sign-off | ADAPTED | pipeline/roles/game-designer.md:29; pipeline/roles/game-designer.md:46-49 | doc only; balance targets re-checked at each gate |
| Design Pipeline:22-31 | Other game's player outcomes and canonical loop | DROPPED | - | (a) other game's setting and loop |
| Design Pipeline:32-33 | One full loop proves the game, not a lone subsystem | ADAPTED | docs/jam-brief.md:42; docs/jam-brief.md:56; pipeline/qa/playtests.md:47 | gate; packaged build + P6 full cold run instead of other game's trace |
| Design Pipeline:34-47 | Defined vs implemented vs verified vs accepted | ADAPTED | AGENTS.md:63; AGENTS.md:70; docs/gdd/GDD-B1.0.md:296; pipeline/checklists/tuning.md:12-13 | doc only; card states + human marks done; automation is not fun |
| Design Pipeline:48 | Approved requirements beat preference or prototype discovery | COVERED | AGENTS.md:23-31; AGENTS.md:98; pipeline/roles/gameplay-dev.md:50 | doc only |
| Design Pipeline:49 | Complexity must earn its cost in player value | COVERED | pipeline/checklists/design-review.md:15 | gate (design review before card is ready) |
| Design Pipeline:50 | Causal integrity, no hidden rescue or punishment | ADAPTED | pipeline/checklists/design-review.md:21; pipeline/checklists/design-review.md:35; pipeline/qa/playtests.md:45 | doc only + P4; hidden behavior needs a decision row, every state change needs a cue |
| Design Pipeline:51 | Evidence proportional to risk | COVERED | pipeline/checklists/design-review.md:3-4 | doc only; only rule cards run the design checklist |
| Design Pipeline:52 | Small-team: focused artifacts, few meetings, few logs | COVERED | AGENTS.md:65-66; pipeline/roles/producer.md:26-38 | doc only |
| Design Pipeline:53 | Legible causes, not a recommendation engine | ADAPTED | pipeline/qa/playtests.md:43; pipeline/qa/playtests.md:49 | P2, P8; readability without a HUD |
| Design Pipeline:54-59 | No discipline confers another's acceptance on itself | COVERED | AGENTS.md:52; AGENTS.md:94 | doc only + JAM_ROLE launch gate |
| Design Pipeline:60-61 | Discover docs; working copy vs approved baseline; no manual register | STRENGTHENED | AGENTS.md:7-8; docs/gdd/README.md:5-10 | manifest_check, gdd_impact, check_card fails cards on stale GDD revision |
| Design Pipeline:62-73 | Source authority table by subject | COVERED | AGENTS.md:23-31 | doc only; pipeline_check cross-doc consistency |
| Design Pipeline:72 | Build evidence motivates change, never overrides requirements | COVERED | docs/gdd/GDD-B1.0.md:353; pipeline/templates/test-note.md:20; pipeline/roles/game-designer.md:17 | doc only |
| Design Pipeline:74-75 | Status mismatch note on other project's docs | DROPPED | - | (a) other project's document-control note |
| Design Pipeline:76-88 | Decision and acceptance owners per discipline | ADAPTED | AGENTS.md:33-54; docs/gdd/GDD-B1.0.md:342-353; docs/decisions.md:17 | doc only; roles table + People seats; pipeline_check fails unknown owners |
| Design Pipeline:89-90 | One person many hats; simulated view is advice only | COVERED | AGENTS.md:52; AGENTS.md:64 | doc only; reviewer must be a different role in a fresh session |
| Design Pipeline:91-103 | Authority labels (GDD RULE, HYPOTHESIS, ILLUSTRATIVE, etc.) | ADAPTED | pipeline/checklists/design-review.md:7-12; pipeline/templates/task-card.md:11 | required field (GDD ref tag, not machine-checked); dependency labels replaced by decision rows |
| Design Pipeline:104-107 | Precedence; conflicting approved docs stop that change | COVERED | AGENTS.md:23-31; AGENTS.md:84 | doc only; `requirements conflict` blocked cause → decision row |
| Design Pipeline:108-122 | Lifecycle phases for a long production | DROPPED | - | (a)/(b) other game's milestone ladder; replaced by G1-G4 (pipeline/roles/producer.md:40-47) |
| Design Pipeline:123-126 | Feature priority classes guide, producer decides order | ADAPTED | docs/jam-brief.md:60-61; docs/gdd/GDD-B1.0.md:31-40 | check_card (features must be implementation_authorized) |
| Design Pipeline:127-134 | Task flow; no extra sign-off states | COVERED | AGENTS.md:56-68 | doc only; routine card work needs no approval |
| Design Pipeline:135-147 | Intake fields: problem, source, type, owner, next action | STRENGTHENED | pipeline/templates/task-card.md:6-46 | required field; check_card fails empty fields |
| Design Pipeline:148-149 | Triage: build vs spec vs disappointing experience | COVERED | pipeline/qa/playtests.md:35 | required field (class bug/cue/design/invalid test) |
| Design Pipeline:150-153 | One-sentence player outcome before rules | STRENGTHENED | pipeline/templates/task-card.md:16; pipeline/checklists/design-review.md:15 | check_card required field `Player outcome` |
| Design Pipeline:154-157 | Mechanic must supply choice, feedback, etc. or be challenged | COVERED | pipeline/checklists/design-review.md:15 | gate (flag to scope decision-maker) |
| Design Pipeline:158-167 | Spec covers states, blocked paths, cues, edge cases | COVERED | pipeline/checklists/design-review.md:16-35 | gate (design review); Done-when needs blocked path (check_card) |
| Design Pipeline:165 | Accessibility, device meaning, localization independence | ADAPTED | pipeline/checklists/design-review.md:21-23; pipeline/ui/accessibility.md:20 | ui_check signals/strings; localization reduced to live text in a string table |
| Design Pipeline:168-171 | Design states consequences; tech picks representation | COVERED | pipeline/roles/game-designer.md:5; pipeline/roles/game-designer.md:52 | doc only |
| Design Pipeline:172-181 | Check directly affected contracts (other game's clusters) | ADAPTED | pipeline/templates/task-card.md:28-29; pipeline/checklists/card-ready.md:20 | check_card `usedby`; clusters were other game's setting |
| Design Pipeline:182-185 | Ask owners a specific question; escalate, never weaken | COVERED | AGENTS.md:30-31; AGENTS.md:132-133; AGENTS.md:99 | doc only; decision row with default |
| Design Pipeline:186-187 | Cheapest experiment with question, variables, stop rule | STRENGTHENED | pipeline/templates/spike-card.md:9-26 | check_card spike fields (Decision row, Decides it, Time box ≤60 min) |
| Design Pipeline:188-191 | Spec alone does not authorize coding or art | COVERED | AGENTS.md:58-59; pipeline/roles/game-designer.md:52 | doc only; no card, no work |
| Design Pipeline:192-193 | Traceable build id and starting state | STRENGTHENED | pipeline/qa/playtests.md:20; AGENTS.md:79 | check_pr evidence header; results log build + tuning commit |
| Design Pipeline:194-199 | Observed / measured / reported / inferred / decided | COVERED | pipeline/qa/playtests.md:63-66 | required field (results-log columns) |
| Design Pipeline:200-207 | Narrowest cause: invalid test, defect, cue, rule, balance | COVERED | pipeline/qa/playtests.md:35; pipeline/roles/game-designer.md:38-40 | doc only; encounter_check E13/E25 (FLAG f81a824: E25 runs only with SURV-04 lift loss on, off in GDD 1.3) before blaming player |
| Design Pipeline:208-211 | Fix in the owning system, no easy-subsystem grab | COVERED | pipeline/qa/playtests.md:35; pipeline/roles/gameplay-dev.md:14 | doc only; lane_guard / File lane |
| Design Pipeline:212-213 | Change one bounded cause; record linked sets | COVERED | pipeline/checklists/tuning.md:8; pipeline/templates/test-note.md:9 | doc only + manifest_check --note (`what_changed` one string) |
| Design Pipeline:214-217 | Stop rules and Keep/Revise/Defer/Propose Cut | COVERED | pipeline/templates/spike-card.md:22-26; pipeline/roles/game-designer.md:33 | doc only |
| Design Pipeline:218-219 | Acceptance package with explicit disposition | STRENGTHENED | pipeline/templates/gate-record.md:8-23 | check_card --gate-record; per gate, not per feature |
| Design Pipeline:220-225 | Design acceptance never claims milestone closure | COVERED | pipeline/roles/producer.md:40; pipeline/roles/producer.md:73 | doc only; humans close gates |
| Design Pipeline:226-227 | No doc inflation; one home per requirement | ADAPTED | pipeline/checklists/card-ready.md:5; AGENTS.md:65; AGENTS.md:53 | pipeline_check cross-doc consistency; placeholders for later items |
| Design Pipeline:228-241 | Artifact menu: clarification, spec, experiment, tuning, record | ADAPTED | pipeline/templates/task-card.md; pipeline/templates/spike-card.md; pipeline/checklists/tuning.md:34-36; pipeline/templates/test-note.md; docs/decisions.md:21 | check_card / manifest_check --note; collapsed to card, spike, tuning row, test note, decision row |
| Design Pipeline:242-253 | Feature spec headings: identity, scope, states, recovery | STRENGTHENED | pipeline/templates/task-card.md:6-46; pipeline/checklists/design-review.md:14-35 | check_card required fields |
| Design Pipeline:254 | Evidence-owned variables, no invented final constants | ADAPTED | pipeline/roles/gameplay-dev.md:35; pipeline/checklists/design-review.md:11 | doc only; DISPUTABLE: we build a stated default number with a decision row instead of leaving it open |
| Design Pipeline:255-261 | Acceptance scenarios, open decisions, testability over length | COVERED | pipeline/templates/task-card.md:33-46 | check_card (measurable Done-when, blocked case) |
| Design Pipeline:262-269 | Stable requirement IDs and a trace chain | ADAPTED | docs/feature-manifest.json; pipeline/templates/task-card.md:13; pipeline/qa/test-map.md | check_card features, manifest_check, test.sh --require; GDD feature IDs replace GD-xxx IDs |
| Design Pipeline:270-281 | Example acceptance wording for other game | DROPPED | - | (a) other game's examples, stated as not rules |
| Design Pipeline:282-285 | Workstreams preamble | DROPPED | - | (b) no rule content |
| Design Pipeline:286-289 | Own real-time service tasks of other game | DROPPED | - | (a) other game's setting |
| Design Pipeline:290-291 | Prove recovery and readable causes under crowded load | COVERED | pipeline/checklists/design-review.md:34; pipeline/checklists/level-sections.md:111-115; pipeline/qa/playtests.md:43 | gate (design review), CAM_Eval_Stress, P2 |
| Design Pipeline:290 | Confirm controller parity before accepting interactions | PORTED | pipeline/checklists/design-review.md:33; pipeline/qa/playtests.md:23 | design-review checkbox; device noted per run |
| Design Pipeline:292-309 | Owner mode, guests, economy workstreams | DROPPED | - | (a) other game's management and economy systems |
| Design Pipeline:308 | Several viable strategies; skill yields different outcomes | ADAPTED | docs/balance.md:17; pipeline/qa/playtests.md:47; pipeline/checklists/level-sections.md:75 | encounter_check E20 (no camping), P6 designer run survives, 30-60% cold survive |
| Design Pipeline:310-315 | Building capabilities and layouts (other game) | DROPPED | - | (a) other game's building system |
| Design Pipeline:314 | Removing a capability disables only its dependents | ADAPTED | pipeline/unreal-rules.md:59; pipeline/qa/test-map.md:45 | FlagsOffBaselineUnchanged, DisabledDependencyRejectedWithLog |
| Design Pipeline:316-321 | Teach real rules; cues not audio or colour alone | STRENGTHENED | pipeline/checklists/design-review.md:21-25; pipeline/ui/accessibility.md:17-19 | ui_check grayscale/signals; P1/P2 cold players |
| Design Pipeline:320 | No critical action needs a separate controller model | PORTED | pipeline/checklists/design-review.md:33 | design-review checkbox |
| Design Pipeline:322-333 | Saving and continuity contract | ADAPTED | pipeline/checklists/design-review.md:26; pipeline/ui/accessibility.md:54; pipeline/unreal-rules.md:59 | SettingsPersist test; game has no progress save, only settings + clean restart |
| Design Pipeline:328 | Quit vs process kill, no final checkpoint promise | DROPPED | - | (a) no save system in this game |
| Design Pipeline:334-346 | Evidence ladder; match evidence to claim | COVERED | pipeline/qa/playtests.md:41; pipeline/level/encounter.md; docs/gdd/GDD-B1.0.md:296; pipeline/roles/game-designer.md:42 | P0 paper walk, encounter_check sim, cold playtests |
| Design Pipeline:347-361 | Canonical scenario families (other game) | ADAPTED | pipeline/qa/playtests.md:39-54; pipeline/qa/test-map.md | P0-P11 + QA-01..12 replace other game's families |
| Design Pipeline:362-365 | Each test defines build, fixture, seed, tuning, question | STRENGTHENED | pipeline/templates/test-note.md:8; pipeline/qa/playtests.md:20; pipeline/templates/spike-card.md:15 | manifest_check --note; Decides it written before running |
| Design Pipeline:366-367 | Watch behavior before asking; track misreads, hesitation | COVERED | pipeline/qa/playtests.md:21-23 | doc only |
| Design Pipeline:368-369 | No universal sample size; targets from baseline | ADAPTED | pipeline/qa/playtests.md:3; pipeline/qa/playtests.md:29-30; pipeline/roles/game-designer.md:56 | gate; DISPUTABLE: we fix minimums (2 cold, 4 for `met`) and pass thresholds |
| Design Pipeline:370-371 | Comparative tests control conditions | COVERED | pipeline/templates/spike-card.md:23; pipeline/qa/playtests.md:25 | doc only |
| Design Pipeline:372-377 | Defect vs confusing vs degenerate vs slow | STRENGTHENED | pipeline/qa/playtests.md:35; pipeline/checklists/level-sections.md:75; pipeline/roles/qa-build.md:32 | encounter_check E20 catches degenerate camping; frame-time gate |
| Design Pipeline:378-379 | Investigate surprises; do not auto-suppress emergence | ADAPTED | pipeline/qa/playtests.md:32 | doc only; bug check + retest before rule change, no explicit "keep emergent" line |
| Design Pipeline:380-385 | One owner, repro, disposition; no duplicate logs | COVERED | pipeline/qa/playtests.md:37 | required field |
| Design Pipeline:386-389 | Fix relationships before tuning coefficients | COVERED | pipeline/checklists/tuning.md:14-15; pipeline/roles/game-designer.md:37-39 | doc only |
| Design Pipeline:390-391 | Tuning record: baseline, candidate, expected, observed, rollback | COVERED | pipeline/checklists/tuning.md:8-11; pipeline/checklists/tuning.md:18-19; pipeline/checklists/tuning.md:35 | doc only; old value in commit message is the rollback |
| Design Pipeline:392-400 | Systemic analyses of other game's economy etc. | ADAPTED | docs/balance.md:8-17; pipeline/checklists/level-sections.md | encounter_check; per-phase targets replace other game's analyses |
| Design Pipeline:401-402 | Assists keep causality unless separately authorized | COVERED | pipeline/ui/accessibility.md:53; docs/decisions.md:161 | AssistSlidersScale test |
| Design Pipeline:403-406 | Content family contract before quantity | STRENGTHENED | pipeline/level/encounter.md; pipeline/checklists/level-sections.md:13-23 | encounter_check --data / --wiring on pattern IDs |
| Design Pipeline:407-408 | Same behavior shares definition; counts are production's | STRENGTHENED | pipeline/checklists/design-review.md:37-43; pipeline/roles/gameplay-dev.md:38; docs/jam-brief.md:11 | check_card `cap` (content caps) |
| Design Pipeline:409-412 | Retest the adjacent causal chain after a change | PORTED | pipeline/checklists/design-review.md:39 | design-review §3; re-run before merge or at gate |
| Design Pipeline:413-416 | Chain examples: speed, access, market, save changes | ADAPTED | pipeline/checklists/tuning.md:16-17 | encounter_check E13/E25 (FLAG f81a824: E25 runs only with SURV-04 lift loss on, off in GDD 1.3) + P1/P7 rerun only for movement values |
| Design Pipeline:417-418 | New art/camera rechecks cues and dense readability | PORTED | pipeline/checklists/design-review.md:38 | design-review §3; art_check + ui_check output in PR |
| Design Pipeline:419-424 | QA owns test plan; design owns conformance | ADAPTED | pipeline/roles/qa-build.md; pipeline/roles/game-designer.md:17 | doc only |
| Design Pipeline:425-428 | Consult by decision with options and a lean | COVERED | AGENTS.md:132-133; AGENTS.md:30-31 | doc only (Unknowns format) |
| Design Pipeline:429-434 | What to ask Production, TD and Lead Dev | ADAPTED | AGENTS.md:33-54; pipeline/roles/game-designer.md:3-6 | doc only; role boundaries in cards |
| Design Pipeline:435-436 | Art states which cues must read; art OK is not readability | COVERED | pipeline/checklists/design-review.md:21; pipeline/qa/playtests.md:49 | P8 with cold players, separate from art review |
| Design Pipeline:437-438 | QA repro/retest; self-run tests are not independent QA | COVERED | pipeline/roles/game-designer.md:42; pipeline/roles/qa-build.md:44; pipeline/roles/qa-build.md:58 | doc only |
| Design Pipeline:439-440 | Coordinate with UX/audio, do not take their decisions | ADAPTED | AGENTS.md:43-47 | doc only; separate roles own each |
| Design Pipeline:441-446 | Formal handoff trigger and contents | STRENGTHENED | AGENTS.md:86; .github/PULL_REQUEST_TEMPLATE.md:26-39 | check_pr `next`, `journal`, `links` |
| Design Pipeline:447-450 | X-vs-Y conflicts: no one silently changes contract | COVERED | AGENTS.md:30-31; pipeline/roles/gameplay-dev.md:50; docs/decisions.md:17 | doc only |
| Design Pipeline:451-464 | Pause only affected work; continue the rest | STRENGTHENED | AGENTS.md:87-88 | check_card --blocked-by; main-red.yml |
| Design Pipeline:465-475 | Change classes and their routes | ADAPTED | AGENTS.md:67-68; docs/gdd/README.md:12-28; docs/jam-brief.md:64-71 | doc only; routine work free, humans approve MVP/cut/decisions |
| Design Pipeline:476-477 | Impact analysis across systems | STRENGTHENED | docs/gdd/README.md:18-23; pipeline/templates/task-card.md:28-29 | gdd_impact.py "cited by", check_pr GDD impact |
| Design Pipeline:478-483 | One concise decision record format | STRENGTHENED | docs/decisions.md:11-21 | pipeline_check fails cited IDs with no row |
| Design Pipeline:484-485 | No conflicting registers; reopen only on new evidence | COVERED | docs/decisions.md:15-16 | doc only |
| Design Pipeline:486-489 | Debt/risk labels with owner and trigger | COVERED | pipeline/qa/playtests.md:36-37; docs/jam-brief.md:73-74; pipeline/roles/gameplay-dev.md:37 | required field (severity) |
| Design Pipeline:490-497 | Propose controlled revision; never quietly edit GDD | COVERED | AGENTS.md:98; pipeline/roles/game-designer.md:22; pipeline/roles/game-designer.md:53 | doc only |
| Design Pipeline:498-515 | Acceptance questions, tailored to the change | ADAPTED | pipeline/checklists/design-review.md:3-35 | gate (design review); tailored by skipping non-rule cards |
| Design Pipeline:516-519 | Long acceptance state ladder | ADAPTED | AGENTS.md:70 | doc only; (b) cut to todo/doing/review/done + blocked |
| Design Pipeline:520-521 | Prototype accepted as evidence only; no silent deferral | COVERED | pipeline/templates/spike-card.md:21; pipeline/templates/gate-record.md:29; AGENTS.md:70 | check_card --gate-record; spike branch never merged |
| Design Pipeline:522-528 | Disposition vocabulary incl. evidence insufficient | STRENGTHENED | pipeline/templates/gate-record.md:23; pipeline/qa/playtests.md:29 | check_card --gate-record; insufficient never passes |
| Design Pipeline:529-534 | Special gates for other game's systems | ADAPTED | pipeline/qa/playtests.md:8-9 | gate; GDD §11 gates mapped to P-tests |
| Design Pipeline:535 | Interaction gate: keyboard and controller meaning | PORTED | pipeline/checklists/design-review.md:33; pipeline/qa/playtests.md:23 | design-review checkbox; G2+ pad run |
| Design Pipeline:536 | Save UX gate | DROPPED | - | (a) no save system |
| Design Pipeline:537-538 | Readability gate at representative density | COVERED | pipeline/qa/playtests.md:49; pipeline/roles/integrator.md:30 | P8 + CAM_Eval_Stress, art_check |
| Design Pipeline:539-540 | Gates are concerns, producer sets them | COVERED | pipeline/roles/producer.md:40-47 | doc only |
| Design Pipeline:541-548 | Release-candidate experience recommendation | STRENGTHENED | pipeline/checklists/submission.md:41-48; pipeline/templates/gate-record.md:23 | submission_check, check_card --gate-record |
| Design Pipeline:549-557 | Rhythm: intake, integration runs, change notes, retro | STRENGTHENED | AGENTS.md:15-19; pipeline/roles/producer.md:32-38; pipeline/templates/gate-record.md:18; pipeline/templates/gate-record.md:31 | check_card --status retro questions; daily package |
| Design Pipeline:558-559 | No fixed meetings; prefer async handoffs | ADAPTED | AGENTS.md:65-66; pipeline/roles/producer.md:26-38 | doc only; ours has a fixed jam cadence but all on GitHub |
| Design Pipeline:560-571 | Lightweight / focused / full path by risk | ADAPTED | pipeline/checklists/design-review.md:3-4; pipeline/checklists/card-ready.md:5 | doc only; two levels: rule cards vs others |
| Design Pipeline:572-573 | AI drafts but never approves or claims unverified saves | COVERED | AGENTS.md:52; AGENTS.md:77; AGENTS.md:94 | doc only + check_pr evidence |
| Design Pipeline:574-575 | Brief delegations fully; avoid prose-only agent passes | ADAPTED | pipeline/templates/task-card.md:33-46; AGENTS.md:90 | check_card; loops stop at the bar or after 3 flat rounds (D-new-no-round-cap) |
| Design Pipeline:576-581 | Status in tracker not chat; verify pushed files | STRENGTHENED | AGENTS.md:18-19; AGENTS.md:65-66; AGENTS.md:86 | journal.py, check_pr `journal` |
| Design Pipeline:582-585 | Templates are formats, not extra files | COVERED | pipeline/templates/task-card.md:3-4 | doc only |
| Design Pipeline:586-600 | Task / feature brief template | STRENGTHENED | pipeline/templates/task-card.md:6-46 | check_card required fields |
| Design Pipeline:601-619 | Prototype or tuning experiment template | ADAPTED | pipeline/templates/spike-card.md:9-25; pipeline/templates/test-note.md:6-12; pipeline/qa/playtests.md:63 | check_card spike fields, manifest_check --note; no "alternative explanations" field |
| Design Pipeline:620-634 | Design acceptance handoff template | STRENGTHENED | pipeline/templates/gate-record.md:7-24 | check_card --gate-record |
| Design Pipeline:635-650 | Material change proposal template | ADAPTED | docs/decisions.md:21; AGENTS.md:132-133 | pipeline_check; no per-area impact field |
| Design Pipeline:651-657 | Adoption steps by studio head and producer | DROPPED | - | (b) adoption approval bureaucracy |
| Design Pipeline:658-660 | Simplify process after use; check checks earn their cost | ADAPTED | pipeline/templates/gate-record.md:18; pipeline/templates/gate-record.md:31 | check_card retro questions; asks what slowed us, not whether each check caught a defect |
| Design Pipeline:661-664 | Controlled maintenance of this pipeline | ADAPTED | AGENTS.md:99; AGENTS.md:53 | pipeline_check; changes by PR, never weaken a check without a measurement |
| Design Pipeline:665-666 | Examples are not specs; requirements stay in GDD | COVERED | AGENTS.md:23-28 | doc only |
| Design Pipeline:667-671 | Non-goal: do not reopen approved GDD | COVERED | AGENTS.md:98 | doc only |
| Design Pipeline:672 | Non-goal: no new mechanics or hidden systems | STRENGTHENED | pipeline/checklists/design-review.md:35; pipeline/templates/task-card.md:13-15 | check_card (features must be authorized) |
| Design Pipeline:673 | Illustrative art never becomes a requirement | COVERED | pipeline/checklists/design-review.md:12 | doc only |
| Design Pipeline:674 | No broad content before the core loop works | STRENGTHENED | pipeline/roles/producer.md:54; docs/jam-brief.md:60; pipeline/roles/producer.md:76 | check_card --lanes (no stretch while MVP is open) |
| Design Pipeline:675 | Non-goal: prescribing Unity assemblies, save formats | DROPPED | - | (a) Unity-specific |
| Design Pipeline:676 | Never present unexecuted work as passed | COVERED | AGENTS.md:77; pipeline/qa/playtests.md:29 | check_pr evidence |
| Design Pipeline:677-679 | Not assigning budgets; no self-approval of changes | COVERED | AGENTS.md:94; pipeline/roles/game-designer.md:4 | doc only |
| Design Pipeline:680-694 | Disposition and executive-approval closing section | DROPPED | - | (b) adoption boilerplate |

### inherited: Game Designer charter

| Source | Item | Status | Our location | Enforcement |
|---|---|---|---|---|
| Game Designer charter:1-17 | Title, version and approval header | DROPPED | - | no rule content |
| Game Designer charter:18-27 | Persona identity statement | DROPPED | - | no rule content; persona prose |
| Game Designer charter:28-45 | List of expected design duties | ADAPTED | pipeline/roles/game-designer.md:13-42 | doc only; persona list became concrete Owns, Outputs, How you work |
| Game Designer charter:46-49 | Deliver validated design, inside approved scope | COVERED | pipeline/roles/game-designer.md:45-49 | doc only (role Done when) |
| Game Designer charter:50-55 | Humans keep authority; expertise grants no scope | COVERED | pipeline/roles/game-designer.md:4,51-56; AGENTS.md:67-68 | doc only |
| Game Designer charter:56-92 | Success = accepted experiences, not volume | ADAPTED | pipeline/roles/game-designer.md:45-49 | doc only; prose reduced to outcome-based Done when |
| Game Designer charter:93-156 | Expertise lists (core, systems, interaction) | DROPPED | - | no rule content; capability list |
| Game Designer charter:157-162 | Design defines behavior; UX, TD, engineering implement | COVERED | AGENTS.md:34-48; pipeline/roles/ui-ux.md:13-14 | doc only |
| Game Designer charter:163-197 | Analysis and production-aware expertise lists | DROPPED | - | no rule content; capability list |
| Game Designer charter:198-217 | Director plus practitioner; don't delegate everything | ADAPTED | pipeline/roles/game-designer.md:28-34 | doc only; agent writes its own cards, cannot sub-delegate |
| Game Designer charter:218-246 | Requirements come from the active project only | COVERED | AGENTS.md:5-13,21 | doc only |
| Game Designer charter:247-258 | Player experience before feature count | COVERED | pipeline/checklists/design-review.md:15; pipeline/templates/task-card.md:16 | required field (Player outcome, check_card) |
| Game Designer charter:259-266 | Choices must have distinguishable outcomes | ADAPTED | pipeline/qa/playtests.md:44,50 | gate (P3, P9); checked as player-observed choice |
| Game Designer charter:267-276 | Clarity before complexity; challenge costly complexity | ADAPTED | pipeline/qa/playtests.md:43; pipeline/checklists/card-ready.md:16 | gate (P2); doc only; stretch changing no core decision goes last |
| Game Designer charter:277-284 | Judge features in whole-game context | ADAPTED | pipeline/checklists/level-sections.md:66; pipeline/checklists/card-ready.md:16 | encounter_check E4 (FLAG f81a824: E4/E19/E24 run only with 2+ owl patterns since 6130c77; GDD 1.3 has one, so dormant); per-phase rule, not whole-game review |
| Game Designer charter:285-292 | Hidden information is not real difficulty | ADAPTED | pipeline/roles/game-designer.md:40; pipeline/checklists/level-sections.md:69,144 | encounter_check E6 (FLAG f81a824: its overlap part only with 2+ patterns), `--playtest` explained=n. ADAPTED (final 11): its overlap part needs 2+ owl patterns; GDD 1.3 has one, so doc-only today |
| Game Designer charter:293-307 | Separate hypothesis, requirement, implemented, observed, validated | COVERED | pipeline/checklists/design-review.md:8-12; pipeline/qa/playtests.md:63-66; docs/feature-manifest.json | required field (GDD ref tag); manifest_check |
| Game Designer charter:308-317 | Simplify for feasibility, keep the core experience | COVERED | docs/jam-brief.md:64-71 | doc only (never-cut list, cut trigger) |
| Game Designer charter:318-327 | Accessibility is a design responsibility | STRENGTHENED | pipeline/checklists/design-review.md:22-23; pipeline/ui/accessibility.md:11-26; pipeline/qa/playtests.md:5-6 | ui_check flashes, grayscale, signals |
| Game Designer charter:328-337 | Challenge with evidence and alternatives; respect decisions | COVERED | AGENTS.md:133; docs/decisions.md:15 | doc only |
| Game Designer charter:338-345 | Avoid speculative systems costing more than value | ADAPTED | docs/jam-brief.md:60; AGENTS.md:58-59; pipeline/roles/dev-lead.md:37 | check_card (Hook only), Dev Lead item 10; done through flags and stretch order |
| Game Designer charter:346-363 | Executive authority list | ADAPTED | AGENTS.md:67-68; docs/jam-brief.md:83-98 | doc only; People seats replace executives |
| Game Designer charter:364-369 | May challenge, may not replace direction or grow scope | COVERED | pipeline/roles/game-designer.md:53; pipeline/checklists/card-ready.md:9 | check_card `--lanes` (no stretch while MVP is open) |
| Game Designer charter:370-396 | Design authority list; find ambiguities; respect others | ADAPTED | pipeline/roles/game-designer.md:13-19,52-53; AGENTS.md:30-31 | doc only; agent proposes, human design owner decides |
| Game Designer charter:397-414 | Recommend vs decide; prototype is not authorization | COVERED | docs/decisions.md:6; pipeline/templates/spike-card.md:21,26 | doc only |
| Game Designer charter:415-444 | Delegated decision matrix | ADAPTED | AGENTS.md:34-48; pipeline/roles/game-designer.md:13-19,51-56 | doc only; matrix replaced by per-role Owns and Never |
| Game Designer charter:445-465 | Routine work needs no approval; binding rules stay | COVERED | AGENTS.md:67-68,97 | doc only |
| Game Designer charter:466-491 | Materiality test for escalating changes | ADAPTED | AGENTS.md:67-68; pipeline/checklists/tuning.md:11 | doc only; every number change is human-reviewed, so no materiality call |
| Game Designer charter:492-514 | Ownership checklist across the whole experience | COVERED | pipeline/checklists/design-review.md:14-35; pipeline/qa/playtests.md:34-37 | doc only (Producer checklist) |
| Game Designer charter:515-539 | Design acceptance needs evidence; working code is not enough | ADAPTED | pipeline/qa/playtests.md:8; pipeline/templates/gate-record.md:10-11,34 | check_card `--gate-record`; design acceptance at gate playtests, not per PR |
| Game Designer charter:540-567 | Distinct acceptance states, never collapsed | ADAPTED | AGENTS.md:70; pipeline/templates/gate-record.md:9-23 | check_card `--gate-record`; 10 states became 4 labels plus separate gate lines |
| Game Designer charter:568-587 | Conditional acceptance needs owner, disposition, trigger | ADAPTED | pipeline/templates/gate-record.md:23,29,34 | check_card `--gate-record`; exception = owner + fix-or-cut hour, no player-impact field |
| Game Designer charter:588-599 | Collaborative, not deferential, with leadership | ADAPTED | AGENTS.md:133 | doc only; options with a stated lean |
| Game Designer charter:600-618 | Explain consequential tradeoffs to decision makers | ADAPTED | AGENTS.md:31,131 | required field (decision row "Why it matters") |
| Game Designer charter:619-630 | Seven-step creative disagreement procedure | COVERED | AGENTS.md:133; docs/decisions.md:23 | doc only |
| Game Designer charter:631-638 | No manufactured disagreement; reopen only on evidence | COVERED | docs/decisions.md:15 | doc only; "manufactured" half folded into the MISSING challenge port |
| Game Designer charter:639-681 | Production split; no scope growth; joint scope cuts | ADAPTED | pipeline/roles/game-designer.md:33; docs/jam-brief.md:64-71; pipeline/checklists/card-ready.md:9 | check_card `--lanes`; GD feeds playtest dispositions, not estimates |
| Game Designer charter:682-713 | Design owns information, art owns its expression | COVERED | pipeline/checklists/design-review.md:21; docs/decisions.md:60 | doc only (D0, cue names art-bible row) |
| Game Designer charter:714-719 | Art may not add gameplay states silently | COVERED | pipeline/checklists/design-review.md:12; docs/decisions.md:60 | doc only (ILLUSTRATIVE adds no rule) |
| Game Designer charter:720-747 | Design owns what, technical direction owns how | COVERED | AGENTS.md:39; pipeline/roles/game-designer.md:52 | doc only |
| Game Designer charter:748-757 | Consult TD when mechanic needs new capability | ADAPTED | AGENTS.md:85,99 | doc only; via split proposal and TD-only engine settings |
| Game Designer charter:758-763 | No technical convenience as requirement; raise conflicts | COVERED | pipeline/roles/gameplay-dev.md:50; AGENTS.md:84 | doc only (requirements conflict → decision row) |
| Game Designer charter:764-781 | Lead Dev owns implementation; designer stays available | ADAPTED | AGENTS.md:37-38; docs/gdd/questions-B1.0.md | doc only; questions go to decision rows or questions file |
| Game Designer charter:782-793 | Unclear requirement steps; never invent mechanics | COVERED | AGENTS.md:30-31; pipeline/roles/gameplay-dev.md:35; pipeline/checklists/design-review.md:35,42-43; pipeline/roles/dev-lead.md:38 | Dev Lead review item 11 |
| Game Designer charter:794-797 | Designer may write prototype code | ADAPTED | pipeline/roles/game-designer.md:5,52 | doc only; DISPUTABLE: our GD never writes C++, ini or assets |
| Game Designer charter:798-821 | QA finding is evidence; explanation can't erase failure | COVERED | pipeline/roles/qa-build.md:44,59; pipeline/qa/playtests.md:32 | doc only |
| Game Designer charter:822-832 | Classify spec vs observed mismatch, assign owner | ADAPTED | pipeline/qa/playtests.md:35-37; pipeline/roles/game-designer.md:38-39 | doc only; six causes became bug/cue/design/invalid test |
| Game Designer charter:833-863 | UX decision rights; no fake specialist review | ADAPTED | pipeline/roles/ui-ux.md:13-14; AGENTS.md:50 | doc only; UX is its own role |
| Game Designer charter:864-882 | Consult audio and others; no standing ceremonies | ADAPTED | pipeline/checklists/design-review.md:21,27 | audio_check `--log`; localization out of scope |
| Game Designer charter:883-896 | Proportionate design lifecycle | ADAPTED | pipeline/checklists/design-review.md:3-4 | doc only; full checklist only for rule cards |
| Game Designer charter:897-916 | Establish project, constraints, owner, evidence first | COVERED | AGENTS.md:5-19; pipeline/templates/task-card.md:7-46 | required field (check_card) |
| Game Designer charter:917-935 | Define what the player should experience | COVERED | pipeline/checklists/design-review.md:15; pipeline/templates/task-card.md:16 | required field (Player outcome) |
| Game Designer charter:936-960 | Model states, actions, transitions, conditions | COVERED | pipeline/checklists/design-review.md:16-19; pipeline/level/encounter.md | doc only |
| Game Designer charter:961-1000 | Spec fields; binding vs illustrative vs hypothesis | COVERED | pipeline/templates/task-card.md:16-46; pipeline/checklists/design-review.md:8-35 | required field (check_card) |
| Game Designer charter:1001-1032 | Cheapest prototype; hypothesis, stop, decision informed | STRENGTHENED | pipeline/templates/spike-card.md:9-26; pipeline/checklists/level-sections.md:124-127 | check_card spike (Decides it, Time box ≤ 60); encounter_check `--card` C4 |
| Game Designer charter:1033-1056 | Evidence supports, contradicts or insufficient; intuition isn't observation | COVERED | pipeline/qa/playtests.md:29,66-67 | doc only (Result values, Inferred label) |
| Game Designer charter:1057-1072 | Bounded iteration; one variable; stop when met | STRENGTHENED | pipeline/checklists/tuning.md:8-13,18-19; AGENTS.md:90 | gate record fails a `pending` tuning row |
| Game Designer charter:1073-1093 | Reconcile; never silently change an accepted system | COVERED | pipeline/checklists/design-review.md:35; AGENTS.md:30-31,97 | doc only |
| Game Designer charter:1094-1101 | Separate design acceptance from other acceptances | ADAPTED | pipeline/templates/gate-record.md:10-11 | doc only; separate MVP and playtest lines |
| Game Designer charter:1102-1122 | Handoff fields; no enthusiastic description as spec | STRENGTHENED | AGENTS.md:86; pipeline/templates/task-card.md:33-34 | check_pr (Next:, links); check_card measurable Done-when |
| Game Designer charter:1123-1132 | No mechanics only for variety | ADAPTED | pipeline/checklists/level-sections.md:66 | encounter_check E4 (FLAG f81a824: E4/E19/E24 run only with 2+ owl patterns since 6130c77; GDD 1.3 has one, so dormant); speed-only phase change fails |
| Game Designer charter:1133-1140 | Consistent rules; context differences get feedback | COVERED | pipeline/checklists/design-review.md:18 | doc only (blocked path has own cue) |
| Game Designer charter:1141-1159 | Evaluate decisions by information, tradeoff, timing | ADAPTED | pipeline/qa/playtests.md:44,50 | gate (P3, P9) |
| Game Designer charter:1160-1177 | Define what player must know, when, how urgent | STRENGTHENED | pipeline/checklists/design-review.md:21-25; pipeline/qa/playtests.md:49 | ui_check signals; gate (P8) |
| Game Designer charter:1178-1198 | Intended challenge vs accidental friction | STRENGTHENED | pipeline/roles/game-designer.md:40; docs/balance.md:11-17 | encounter_check `--playtest` (explained=n) |
| Game Designer charter:1199-1219 | Progression and escalation fit the experience | ADAPTED | pipeline/checklists/level-sections.md:64-80 | encounter_check E3, E4, E19, E24 (FLAG f81a824: E4/E19/E24 run only with 2+ owl patterns since 6130c77; GDD 1.3 has one, so dormant). ADAPTED (final 11): E4/E19/E24 need 2+ owl patterns; GDD 1.3 has one, so only E3 runs today |
| Game Designer charter:1220-1244 | Economy sources, sinks, recovery; model ≠ fun | ADAPTED | docs/decisions.md:38-39; pipeline/checklists/level-sections.md:92-94 | encounter_check E25 (FLAG f81a824: E25 runs only with SURV-04 lift loss on, off in GDD 1.3); no economy, health and wear are the resources |
| Game Designer charter:1245-1263 | Simulation serves experience; predictable cause and effect | ADAPTED | pipeline/qa/playtests.md:43; pipeline/checklists/level-sections.md:54 | encounter_check E12; gate (P2); other game's setting removed |
| Game Designer charter:1264-1282 | Controls: actions, priority, cancel, conflicts | COVERED | pipeline/checklists/design-review.md:16-20 | doc only |
| Game Designer charter:1283-1301 | Accessibility barrier list (timing, colour, audio) | STRENGTHENED | pipeline/ui/accessibility.md:11-26,49-59,61-70 | ui_check ci (FLAG f81a824: E1 now calls the Toggle setting open, Q8; settled D18 and ui_check's required HoldToggleSetting still demand it) |
| Game Designer charter:1302-1303 | No universal accessibility features without evidence | ADAPTED | pipeline/ui/accessibility.md:52-53; pipeline/qa/playtests.md:5-6 | doc only; DISPUTABLE: fixed assist tier prescribed up front |
| Game Designer charter:1304-1319 | Degenerate strategies; not every emergent one is bad | ADAPTED | pipeline/checklists/level-sections.md:75-76 | encounter_check E20; only camping, on data |
| Game Designer charter:1320-1343 | Simplest design; don't cut essential value | COVERED | docs/jam-brief.md:11,64-71; pipeline/checklists/card-ready.md:15 | check_card (content caps) |
| Game Designer charter:1344-1353 | Docs communicate; avoid long ambiguous docs | ADAPTED | AGENTS.md:3 | pipeline_check budget; applied to agent docs |
| Game Designer charter:1354-1371 | Know binding vs superseded docs; newer ≠ approved | COVERED | AGENTS.md:7-8,23-27; docs/gdd/README.md:5-10 | manifest_check; pipeline_check |
| Game Designer charter:1372-1398 | GDD contents; keep governance out of GDD | ADAPTED | docs/gdd/README.md:6; docs/gdd/questions-B1.0.md | doc only; GDD is human-authored and read-only |
| Game Designer charter:1399-1414 | GDD vs tech design vs code vs QA authority | COVERED | AGENTS.md:23-28; pipeline/checklists/design-review.md:12; pipeline/roles/gameplay-dev.md:50 | doc only |
| Game Designer charter:1415-1429 | Vague goals become observable behavior | STRENGTHENED | pipeline/checklists/design-review.md:24; pipeline/templates/task-card.md:33-34 | check_card measurable Done-when |
| Game Designer charter:1430-1431 | Don't invent arbitrary numerical thresholds | ADAPTED | docs/balance.md:4,22; pipeline/checklists/level-sections.md:45,71 | doc only; DISPUTABLE: we require numbers, marked proposed until accepted |
| Game Designer charter:1432-1466 | Figures carry authority; images set no rules | COVERED | pipeline/checklists/design-review.md:12; docs/decisions.md:60 | required field (GDD ref tag) |
| Game Designer charter:1467-1485 | Handoff readiness; open questions not assumptions | STRENGTHENED | pipeline/checklists/card-ready.md:3-22; pipeline/checklists/design-review.md:35 | check_card |
| Game Designer charter:1486-1497 | Keep supersession history; no silent rewrites | COVERED | docs/decisions.md:13-16; docs/gdd/README.md:6; AGENTS.md:80 | pipeline_check (IDs resolve) |
| Game Designer charter:1498-1507 | Prototype answers a real design question | COVERED | pipeline/templates/spike-card.md:1-4 | check_card spike (Decision row) |
| Game Designer charter:1508-1526 | Pick method by the uncertainty | ADAPTED | pipeline/checklists/level-sections.md:124-127; pipeline/templates/spike-card.md:9-18 | encounter_check (scripted sim); examples became P0, sim, spike |
| Game Designer charter:1527-1541 | Prototype code and assets are not production | COVERED | pipeline/templates/spike-card.md:21 | doc only (spike branch never merged) |
| Game Designer charter:1542-1560 | Experiment record fields, proportional | COVERED | pipeline/templates/spike-card.md:9-18,24-25 | check_card spike |
| Game Designer charter:1561-1575 | Stop experiments when answered or out of budget | COVERED | pipeline/templates/spike-card.md:16,22 | check_card (Time box ≤ 60) |
| Game Designer charter:1576-1597 | Observation, report, measurement, interpretation, decision kept apart | COVERED | pipeline/qa/playtests.md:63-66 | required field (log columns) |
| Game Designer charter:1598-1616 | Each playtest names its questions | COVERED | pipeline/qa/playtests.md:39-54 | doc only (each P-test has What and Pass) |
| Game Designer charter:1617-1634 | Playtest design: participants, build, conditions | COVERED | pipeline/qa/playtests.md:1-7,19-25,63 | doc only |
| Game Designer charter:1635-1650 | Qualitative evidence; one preference isn't representative | COVERED | pipeline/qa/playtests.md:24,28-29 | doc only |
| Game Designer charter:1651-1654 | One severe usability failure is a defect | COVERED | pipeline/qa/playtests.md:31; docs/decisions.md:87 | doc only |
| Game Designer charter:1655-1672 | Metrics tied to design questions | STRENGTHENED | pipeline/qa/playtests.md:11-17 | encounter_check `--playtest` |
| Game Designer charter:1673-1674 | No universal success thresholds | ADAPTED | pipeline/qa/playtests.md:42-52 | gate; DISPUTABLE: fixed pass line per P-test |
| Game Designer charter:1675-1676 | Correlation is not causation | ADAPTED | pipeline/roles/game-designer.md:24 | doc only; data says where, observer says why |
| Game Designer charter:1677-1686 | State sample limits; no false certainty | STRENGTHENED | pipeline/qa/playtests.md:29-30; docs/balance.md:22 | gate (insufficient never passes; met needs 4 players) |
| Game Designer charter:1687-1702 | Check build first; don't redesign or dismiss | COVERED | pipeline/qa/playtests.md:31-32; pipeline/roles/game-designer.md:38-39 | doc only |
| Game Designer charter:1703-1716 | Design playtest and QA validation both needed | COVERED | pipeline/templates/gate-record.md:10-11; pipeline/qa/playtests.md:8; pipeline/roles/qa-build.md:44 | gate |
| Game Designer charter:1717-1741 | Set balance objective before changing values | COVERED | pipeline/roles/game-designer.md:37; docs/balance.md:8-17 | doc only |
| Game Designer charter:1742-1761 | Models help but are not proof | ADAPTED | tools/encounter_check.py; pipeline/checklists/tuning.md:12-13; pipeline/roles/game-designer.md:42 | encounter_check E13, E25 (FLAG f81a824: E25 runs only with SURV-04 lift loss on, off in GDD 1.3). ADAPTED (final 11): E25 needs SURV-04 lift loss, off in GDD 1.3, so only E13 runs today |
| Game Designer charter:1762-1776 | Know ranges and systemic effects before tuning | STRENGTHENED | pipeline/checklists/tuning.md:16-17,20-22; docs/feel-spec.md:138 | encounter_check `--envelope` |
| Game Designer charter:1777-1788 | Baseline, record changes; number moved ≠ better | STRENGTHENED | pipeline/checklists/tuning.md:8-13,34-35 | gate record fails `pending` rows |
| Game Designer charter:1789-1805 | Diagnose dominant strategies found in play | PORTED | pipeline/qa/playtests.md:23; pipeline/roles/game-designer.md:33 | observer notes; GD output line keep/cause per strategy |
| Game Designer charter:1806-1809 | Balance accepted against intended experience | COVERED | docs/balance.md:8-22 | doc only |
| Game Designer charter:1810-1811 | No universal numerical balance thresholds | ADAPTED | docs/balance.md:11-17,22 | doc only; DISPUTABLE: fixed proposed targets per phase |
| Game Designer charter:1812-1815 | Incomplete evidence: name uncertainty and decision | COVERED | pipeline/roles/game-designer.md:47; docs/balance.md:22 | doc only |
| Game Designer charter:1816-1835 | Routine refinement; notify affected owners | COVERED | AGENTS.md:67-68; pipeline/templates/task-card.md:28-29; pipeline/checklists/card-ready.md:20 | check_card usedby |
| Game Designer charter:1836-1853 | Material change steps; update records | STRENGTHENED | AGENTS.md:30-31,131; docs/gdd/README.md:12-28 | gdd_impact; check_pr GDD impact |
| Game Designer charter:1854-1874 | Design debt classified, bounded fixes | ADAPTED | docs/gdd/questions-B1.0.md; pipeline/roles/gameplay-dev.md:37 | doc only; no debt register, gaps go to questions file and issues |
| Game Designer charter:1875-1894 | Cut scope keeping core; smaller coherent game | COVERED | docs/jam-brief.md:60-71; pipeline/templates/gate-record.md:8 | check_card `--gate-record` |
| Game Designer charter:1895-1917 | Lead design work, decompose, review | ADAPTED | pipeline/roles/producer.md:6-7; pipeline/roles/level-designer.md:59 | doc only; Producer decomposes, GD reviews numbers |
| Game Designer charter:1918-1932 | Delegate without exceeding recipient authority | ADAPTED | docs/decisions.md:6 | doc only; agents cannot spawn, never decide rows |
| Game Designer charter:1933-1954 | AI output reviewed; convincing ≠ evidence | COVERED | pipeline/roles/game-designer.md:42; pipeline/checklists/tuning.md:12; AGENTS.md:72-77 | doc only |
| Game Designer charter:1955-1971 | Verify tools, access, permissions before work | STRENGTHENED | AGENTS.md:9,15-19,65 | agent.sh `JAM_ROLE` write block; `CAN RUN` line |
| Game Designer charter:1972-2013 | Assignment brief fields, context-free | STRENGTHENED | pipeline/templates/task-card.md:6-46 | check_card (empty field fails) |
| Game Designer charter:2014-2030 | Agent states; don't infer later state | ADAPTED | AGENTS.md:63,69; pipeline/templates/task-card.md:57-58 | doc only; 10 states became 5 labels |
| Game Designer charter:2031-2050 | Review real outputs and unintended changes | STRENGTHENED | pipeline/roles/dev-lead.md:27-29,38 | Dev Lead items 2, 11; check_card `--lanes` |
| Game Designer charter:2051-2064 | Diagnose failure; no endless retries | COVERED | AGENTS.md:83-85,88-89 | check_card `--overrun` |
| Game Designer charter:2065-2086 | Prepared vs submitted; role switch isn't consultation | COVERED | AGENTS.md:52,63-65,93 | doc only (ROLE header on comments) |
| Game Designer charter:2087-2103 | Duty to challenge proposals that threaten experience | PORTED | pipeline/roles/game-designer.md:43 | §9 block naming a balance target or P-test |
| Game Designer charter:2104-2119 | Challenge format: concern, evidence, options, owner | COVERED | AGENTS.md:133 | doc only |
| Game Designer charter:2120-2129 | Preference isn't evidence; don't defend own idea | ADAPTED | pipeline/checklists/tuning.md:12-13 | doc only; own tuning kept only on cold-player evidence |
| Game Designer charter:2130-2145 | Give clear recommendations, not hand-backs | COVERED | AGENTS.md:133 | doc only (your lean) |
| Game Designer charter:2146-2157 | After decision: support, keep rationale, don't reopen | COVERED | docs/decisions.md:12-16 | doc only |
| Game Designer charter:2158-2174 | Source-of-truth steps before work | STRENGTHENED | AGENTS.md:5-19,23-30 | journal resume; `CAN RUN` line |
| Game Designer charter:2175-2180 | Newest ≠ approved; no other-project imports; memory ≠ docs | COVERED | docs/gdd/README.md:7; AGENTS.md:7,19,21 | doc only |
| Game Designer charter:2181-2184 | Unreadable source: disclose, invent nothing | PORTED | .github/PULL_REQUEST_TEMPLATE.md:28; tools/check_pr.py | check_pr rule unread (test_could_not_read_line_required) |
| Game Designer charter:2185-2210 | Keep design knowledge in existing records | COVERED | docs/decisions.md; pipeline/checklists/tuning.md:34; pipeline/qa/playtests.md:62 | pipeline_check; journal |
| Game Designer charter:2211-2233 | Decision record fields | COVERED | docs/decisions.md:11-23 | pipeline_check (IDs, owners) |
| Game Designer charter:2234-2254 | Session handoff; claim nothing unverified | STRENGTHENED | AGENTS.md:75-77,85 | journal checkpoint/export; check_pr |
| Game Designer charter:2255-2270 | Resume from last verified state | STRENGTHENED | AGENTS.md:18-19 | journal resume |
| Game Designer charter:2271-2299 | Verified vs unverified references | ADAPTED | docs/references.md:1-4; pipeline/unreal-rules.md:10; AGENTS.md:78 | doc only; `[VERIFY]` tag marks unverified facts |
| Game Designer charter:2300-2381 | Reference register (books, guidelines, GDC) | DROPPED | - | (b) reading list, no rule; port-log rejects registers |
| Game Designer charter:2382-2403 | Continuous professional development | DROPPED | - | (c) agent has no learning across sessions |
| Game Designer charter:2404-2468 | Performance dimensions and 1-5 self-rating | DROPPED | - | (b) self-ratings rejected; outcomes judged by role Done when |
| Game Designer charter:2469-2487 | Propose role-instruction fixes from repeated evidence | ADAPTED | pipeline/templates/gate-record.md:18,31; AGENTS.md:99; tools/run_reviewer_eval.py | check_card `--gate-record`; per-gate retro line, not proposal form |
| Game Designer charter:2488-2513 | No competing studio policy from one role | COVERED | AGENTS.md:1-3,52 | pipeline_check cross-doc consistency |
| Game Designer charter:2514-2576 | Four proportional response levels | ADAPTED | AGENTS.md:133; pipeline/checklists/design-review.md:3-4 | doc only; one Unknowns format, checklist only for rule cards |
| Game Designer charter:2577-2594 | Compact activation directive | ADAPTED | pipeline/roles/game-designer.md:1-11 | doc only; role card is the activation text |
| Game Designer charter:2595-2636 | Commitment list and slogans | DROPPED | - | no rule content |
| Game Designer charter:2637-2648 | Document control block | DROPPED | - | no rule content |
