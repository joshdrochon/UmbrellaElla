# Reviewer eval results

Runner: `python3 tools/run_reviewer_eval.py` · reviewer CLI `claude -p` (Claude Code, default model) · Josh's Mac · 2026-11-06.
Raw outputs are in `evals/reviewer/runs/` locally (gitignored); summaries are copied here. Every run is listed, including failures.

| Run | Setup | Defects found | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 191617 | v1 cases, reviewer could read the repo | 13/13 | 8/8 | 12/12 | 2/3 | FAIL |
| 191951 | clean cases only | – | – | – | 2/3 | FAIL |
| 192045, 192345, 192631 | clean cases given test evidence | 13/13 | 8/8 | 12/12 | 3/3 | PASS ×3 |
| 193201, 193534, 193851 | uniform wording, reviewer isolated (no file/shell tools, empty folder) | 13/13 | 8/8 | 12/12 | 2/3, 3/3, 3/3 | 1 FAIL, 2 PASS |
| 194251, 194647, 195030 | case 15 fixed, Unreal rules updated | 13/13 | 8/8 | 12/12 | 2/3, 3/3, 3/3 | 1 FAIL, 2 PASS |
| **195457, 195848, 200244** | **case 13 fixed, evidence line aligned with the rules** | **13/13** | **8/8** | **12/12** | **3/3** | **PASS ×3** |

Across all 14 full runs: every planted defect was found and every defective change was blocked, every time.
The failures were all clean code wrongly rejected. Each time, the reviewer's reason was valid:
- Case 14 (run 191617): `Velocity.Z < 0` is also true walking downhill, so the "clean" code broke the falling rule. No test evidence either.
- Case 15 (run 193201): a non-owning pointer held strongly, against our own `TWeakObjectPtr` rule.
- Case 13 (run 194251): logic in the character instead of the umbrella component, which the new code-layout rule requires; test name not `<Area>.<Behavior>`.
Fixes went into the clean cases and into the shared evidence line, never into the defective cases or the reviewer prompt
(other than the verdict rule "any medium finding blocks", made to match the scorer).

How to read it: the Dev Lead prompt reliably catches these planted bugs. It is strict, and it will reject code that breaks
any rule in `pipeline/unreal-rules.md`, so clean code must actually follow the rules. 15 cases is small; add a case for every real miss during the jam.
Not covered yet: missing-evidence cases (every case claims build and tests passed), Codex as the reviewer, other models.

## Round 2 (35 cases: 20 new ones written by a separate agent, incl. 4 evidence cases)
| Run | Change | Defects found | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 232645 | 35 cases; rules + reviewer card grew in round 2 (lanes, structure rules, world-test rule) | 22/22 | 18/18 | 28/28 | 3/7 | FAIL |

Why the 4 clean cases were rejected (read from the run JSON):
- 13: TickComponent writes `Velocity.Z` with no tick order set against the movement component, and has no world test. Valid under the new checklist item 6.
- 14: written before the lane rules; attack logic sits in the character, not `UEllaAttackComponent`. Valid; the case is stale.
- 33: same tick-order gap as 13, and the braking step that crosses zero uses the brake acceleration for the whole frame (frame-rate dependent). Valid.
- 35: one medium finding was speculative ("if CanAttack applies a threshold...") about code not in the diff. Reviewer fault.

## Round 3 case refresh (no run yet)
All 35 cases were moved onto the current rules (per-component lanes, `AEllaCharacter` shell, `GetDefault<UUmbrellaTuning>()-><Comp>.<Field>`,
one UENUM state per component, tick prerequisite stated in Context, rule + world tests, split-at-threshold braking), so each defective case
breaks only its planted rule. Clean cases 13, 14, 33 and 35 were stale under the round-2 rules (reasons above); 14 now lives in
`UEllaAttackComponent`. Case 09's second planted API changed from `SetGravity` to `PlayOneShot2D`, because presentation code may not
write gravity. Expected lines were recomputed by script from the new diffs.
| 001843, 003151, 004431 | all 35 cases refreshed to the round-2 rules | 28/29 ×3 | 17/18 ×3 | 30/30 ×3 | 5/7, 6/7, 6/7 | FAIL ×3 |

- Case 13 rejected 3/3, validly: its own Done-when says speed "levels off at RiseSpeed", but `Max(CurrentZ, ...)` never brings a faster upward speed down (e.g. after a kill bounce). Case fixed (`FInterpConstantTo`, plus a level-off rule test; braking stated out of scope).
- Case 15 rejected 1/3 (wanted an invariant block and more negative tests). Left as is: 2/3 approve, and the findings are rule-backed but borderline.
- Case 31 missed 3/3 by the scorer, though blocked every time: the reviewer named the test-count drop as a finding but still wrote `checks_seen.tests: pass` (echoing the tool's PASS). Fix went into the reviewer card: `checks_seen` is the reviewer's judgement, with the cases that make `tests` = fail listed.
| 005802, 011227, 012751 | case 13 fixed; `checks_seen` defined in the reviewer card | 29/29 ×3 | 18/18 ×3 | 30/30 ×3 | 6/7, 4/7, 4/7 | PASS, FAIL, FAIL |

- Detection is now perfect in all 3 runs, including case 31.
- The new failures were caused by my `checks_seen` wording: it says tests fail when the run skipped `--baseline`/`--require`, and the shared evidence line didn't show those flags. So the reviewer blocked clean cases 13, 15, 32, 35 for evidence, correctly by its card. Fix went into the evidence line (it now shows the real command per AGENTS.md), not the card. Case 15's world test now lists its negative overlaps, which its "defeats it once" Done-when needs.
| **014310, 015628, 020800** | **evidence line shows the real test command; case 15 test lists negatives** | **29/29 ×3** | **18/18 ×3** | **30/30 ×3** | **7/7 ×3** | **PASS ×3** |

Round 2 total: 10 full runs of 35 cases. Every run blocked every defective change. Planted defects were missed only in 3 runs, all case 31 (scored miss: blocked, but checks_seen said pass) before the card defined checks_seen. Clean-case failures were each traced to a case or evidence line that broke our own rules, except one speculative reviewer finding (case 35, run 232645), fixed in the card ("a finding about code you cannot see is low at most").

## Round 4 (55 cases: 20 new, 36-55)
New cases: 36 character shell with logic, 37 non-const query, 38 comment contradicts code, 39/40 delegate on another actor (defect/clean),
41/42 actor lookup every tick, 43/44 settings written at runtime, 45/46 looping timer, 47/48 parallel bools vs one UENUM,
49/50 INV-n with no test, 51/52 behavior-picking bool, 53 no module_check output (evidence), 54 inline lambda by-ref capture,
55 stored lambda by-ref capture. 33 older task.md files now name world tests `UmbrellaElla.<Area>.World.<Name>`.
The shared evidence line now shows a NONUNITY=1 build and module_check exit 0, which the reviewer card requires.
Pass bar adds MUST_CATCH in `tools/run_reviewer_eval.py`: cases 37 and 38 must be fully caught in each run.
| Run | Change | Defects found | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 180818, 180821, 180824 | 55 cases, first run | 40/41, 41/41, 40/41 | 20/20 ×3 | 41/41 ×3 | 10/14, 11/14, 11/14 | FAIL ×3 |

- Case 39 scored as missed 2/3, though caught: the reviewer pointed at the EndPlay line, outside the planted range. Fix: EndPlay added as an `also` place.
- Clean cases 46 and 52 rejected 3/3, validly: `UpdateWind` and `ApplyWalk` write no member, so card item 4 wants them `const`. Cases fixed.
- Clean case 44 rejected 2/3, validly: a second state bool next to `EAttackState`, and its world test ended PIE (item 17). Case changed.
- Clean case 13 rejected 1/3: its comment did not match the code (item 16, new). Comment fixed.
- Clean case 15 rejected 1/3: public `UPROPERTY` delegate `OnDefeated` breaks rule C as built. Left as is; it depends on D-new-public-state.
| **183121, 183124, 183127** | **cases 13, 39, 44, 46, 52 fixed** | **41/41 ×3** | **20/20 ×3** | **41/41 ×3** | **13/14, 12/14, 13/14** | **PASS ×3** |

- Cases 37 and 38 (MUST_CATCH) were caught in all 6 runs.
- Case 44 was still rejected 3/3: the reviewer calls `NextCooldownSeconds` a hidden "combo pending" state outside `EAttackState`. That is a fair reading of the one-enum rule; the case should move the combo into the enum before the next round.
- Case 32 rejected 1/3 (overlap does not refire for an actor already inside the box). Left as is.

## Round 5 (consolidation pass, 55 cases)
Changed: `pipeline/unreal-rules.md` split into a core plus `pipeline/unreal/*.md` (the runner loads all of them, so the
reviewer sees the same rules); a link fix in `pipeline/roles/dev-lead.md`; every case's task line "GDD rule: attack only
while the umbrella is closed and Ella is falling" became "GDD rule: open umbrella = rise, closed umbrella = fall (GDD §4)",
because the GDD is now THE LAST HOUR; case 30's build-log path no longer names a personal home folder. No planted defect changed.
Correction (round 6): only the task line changed then. The code and Done-when of the attack cases still used the old rule
(TryAttack on IA_Attack, attack only while closed and falling), and about 20 more cases still described the platformer.
| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 215814, 222138, 222142 | consolidation pass | 1.0, 0.976, 1.0 | 20/20 ×3 | 41/41 ×3 | 13/14, 12/14, 12/14 | PASS ×3 |

- MUST_CATCH cases 37 and 38 were caught in all 3 runs.
- Clean case 44 (combo cooldown) was rejected 2/3, the same "second state outside the enum" reading as round 4. Its task is a retired stretch item (D19). It should be rewritten for the owl game.
- Clean case 15 (enemy header) was rejected 2/3. It is also an old-game case (enemies are gone).

- Run 222138 scored one planted defect as missed (case 45, loop-timer), but still blocked that change.

## Round 6 (case refresh for the new game, 55 cases)
Written by a separate agent session; `pipeline/roles/dev-lead.md` and the `pipeline/` rules were not touched.
- Shared task line is now "GDD rules: open umbrella = rise, closed umbrella = fall (GDD §4); the wand fires on its own at the
  tuned cadence, only while the owl is in the firing lane with line of sight, and there is no attack input (GDD §5, D1 default)."
- Old attack-gate cases now plant a broken auto-fire rule in `UEllaAttackComponent`: 04 fires outside the lane (blocker),
  25 inverts the line-of-sight check (blocker), 27 calls a made-up `AActor::HasLineOfSightTo` (blocker); 14 (clean) and 35
  (clean rule test `UmbrellaElla.Wand.FiresOnlyInLane`) follow the D1 default; 21 and 36 and 07 dropped `IA_Attack`.
- Platformer cases moved to current lanes: enemy → `AClockworkOwl` (01, 02, 06, 15, 28, 39, 40, 43, 44), spikes → owl
  telegraph timer (19, 32, 55), enemy defeat → `AOwlBolt` (11, 30), level end → `ASurvivalClock` (31), per-tick enemy facing →
  `AArenaBottomExit` / `BOTTOM_EXIT` (41, 42, 53), ground/air walk → open/closed steering (51, 52), attack flipbook/flash →
  hurt reaction (09, 54), title/results maps → title/arena maps with `ShowRunEnd(ERunResult)` (23), channels → OwlBolt/WandShot (24).
- Other cases: MVP numbers remapped to the new list, "lift-off from the ground", "kill bounce", "hazards and enemies" removed.
- Each planted defect keeps its id, kind and severity. Expected lines were recomputed by script from the new diffs.
| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 20261107-234655 | first run after the refresh | 0.976 | 20/20 | 40/41 | 11/14 | FAIL |
| 20261108-001002, 003154, 003159 | cases 01/02/15, 14 (and its siblings), 41/42/53 fixed | 1.0 ×3 | 20/20 ×3 | 41/41 ×3 | 13/14, 14/14, 12/14 | PASS ×3 |

- Run 234655, case 51: the reviewer found the planted bool parameter, but wrote prose after the JSON whose `{ return; }`
  broke the runner's JSON extraction, so the verdict scored "invalid". Runner limit, not a case fault; not changed here.
- Clean rejections in run 234655, each valid, each fixed in the case: 14 used `IsValid` and `TWeakObjectPtr::Get` without
  listing them as already used (item 5), and its comment overstated "fires at once"; 15 had a "stops for good" rule with no
  numbered INV (now INV-1 in the header, cited by the test); 42 read Ella's position with no tick order (Context now states
  TG_PostPhysics).
- Clean case 34 rejected in runs 001002 and 003159, validly: its Done-when says BP_Ella keeps its flipbooks, but no test loaded
  BP_Ella. Clean case 15 rejected in run 003159, validly: Context said BP_ClockworkOwl sets a sprite the header does not have.
  Both fixed after the three runs (34 and 18 now list a BP_Ella asset test; 15/01/02 Context corrected). Not re-run yet.
- MUST_CATCH cases 37 and 38 were caught in all 4 runs.

## Round 7 (case refresh for GDD B1.0, 55 cases)
Written by a separate agent session; `pipeline/roles/dev-lead.md`, `pipeline/` rules and `tools/` were not touched.
- Shared task line is now "GDD rules (GDD B1.0 ...): only UP_OPEN lifts and every other umbrella configuration falls at normal
  gravity, with no fast fall (§3); only the Player Motor writes velocity and gravity (§4); a non-CONFIRMED feature runs only behind
  IsFeatureEnabled(EFeatureId::<ID>) at its manifest default (§5); COM-01 is automatic in intent, its trigger OPEN (DEC-02);
  the card's features are implementation_authorized."
- Lanes moved to the 12 GDD B modules: velocity/lift → `UPlayerMotorComponent` reading `EUmbrellaConfig` from
  `UUmbrellaStateComponent` (05, 12, 13, 20, 22, 26, 27, 33, 37); umbrella state (17, 47, 48); presentation → `UFeedbackAdapterComponent`
  (03, 09, 10, 18, 21, 34, 38, 45, 46, 54); Flow/OnSurvivalEnd/ASurvivalClock → `UEncounterDirectorSubsystem` with the six §8 states and
  EncounterCompleted/PlayerDefeated on `UGameEventsSubsystem` (01, 02, 15, 23, 31, 39-43, 51-53); `AOwlBolt` → Projectile/ (11, 30);
  owl timers cleared in `ResetForRestart()` (19, 32, 44, 55); channels → Projectile/ArenaBounds (24); shell has no attack input (07, 36).
- Old auto-fire cases: 04 (blocker) emits without checking the COM_01 flag; 25 (blocker) inverts the flag check; 27 (blocker) calls a
  made-up `UCharacterMovementComponent::IsAirborne()` in the Motor; 14 and 35 stay clean (flag + cooldown on the DEC-02 `RequestEmit` seam).
  44 (retired combo cooldown) is now a clean owl `ResetForRestart`; 51/52 are now an `EndEncounter(bool bSurvived)` bool parameter.
- Each planted defect keeps its id, kind and severity. Expected lines recomputed by script from the new diffs; 45 gains its EndPlay as an
  `also` place (reviewer pointed there, as in case 39 in round 4).
| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 20261108-202146 | first run after the refresh | 0.976 | 20/20 | 41/41 | 9/14 | FAIL |
| 20261108-204754 | 14, 15, 34, 45/46, 52 fixed | 1.0 | 20/20 | 41/41 | 13/14 | PASS |
| 20261108-211213, 213731, 220146 | 45/46 test fixed | 1.0 ×3 | 20/20 ×3 | 41/41 ×3 | 13/14, 12/14, 12/14 | PASS ×3 |
| 20261108-222544 (--only 8 cases) | 14, 15, 34 fixed | 1.0 | 4/4 | 5/5 | 1/3 | (partial) |
| 20261108-223108 (--only 6 cases) | 14 cooldown, 15 first-run reset fixed | 1.0 | 4/4 | 4/4 | 1/2 | (partial) |
| 20261108-223524 (--only 01, 02, 15) | 15 header comment fixed | 1.0 | 1/1 | 2/2 | 1/1 | (partial) |

Every clean rejection was valid and fixed in the case (never the prompt or a defective case):
- 202146: 14 Done-when "reset makes the next request ready" untested; 15 two writers of `EOwlState` (now one `SetState(State, Why)`);
  34 test covered only UP_OPEN/NO_LIFT; 46 my restart edit stopped the wind loop for good; 52 Done-when blocked cases untested.
  45 scored missed: the reviewer cited the EndPlay line, outside the planted range.
- 204754: 46 Done-when "no wind field → silent" untested.
- 211213-220146: 14 cooldown clamp is frame-quantized (2/3), 15 drift speed untested and a stale member comment (2/3), 34 test never
  returned to UP_OPEN (1/3). Fixed after the three runs.
- 222544: my carry-over fix let a shot come up to one frame early against Done-when; reverted to whole frames, now stated in Done-when
  with a gap test. 15: `CurrentDriftPoint` unset on the first run, `DriftPoints[1]` unguarded (now BeginPlay calls `ResetForRestart`, which
  warns under 2 points). 223108: 15 header comment did not match that. 223524: 15 approved.
- The cases as committed passed only the partial re-runs after 220146, not a fresh full run of 55.
- MUST_CATCH cases 37 and 38 were caught in every run.

## Round 8 (clean cases 14, 40, 52 after run 20261108-230255)
Written by a separate agent session; only cases 14, 40, 52 and this file were touched. In 230255 all three rejections were valid:
14 float cooldown countdown depended on tick order vs RequestEmit (could fire a frame early); 40 the test never read the owl's
position for "stops drifting"; 52 DefeatEndsRunOnce did not sweep DeltaSeconds.
- Fix A: 14 now stores `NextEmitTime` (world time) and compares in RequestEmit, no tick, Done-when says world time within
  UE_KINDA_SMALL_NUMBER; 40 test records and re-reads GetActorLocation(); 52 DefeatEndsRunOnce sweeps 1/30, 1/60, 1/120.
- Fix B (after 235325): 40 Context lists INV-1 in the header block and the test cites it (reviewer raised the missing INV as med).
- Fix C (after full run 002114): 14 test reads each spawn's kind, origin and velocity (Done-when spawn request was untested);
  52 lacked GDD B §8 "defeat wins in one update": Context now says CompleteEncounter() runs only from the Director's Tick, which ticks
  after every tick group, Done-when states defeat wins, CompletionEndsRunOnce adds a same-update defeat check.
  Full run 004657 started 38 s before Fix C landed; its 14 and 52 ran after it, so it used the fixed cases.

| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 20261108-235325 (--only 14, 40, 52) | Fix A | n/a | 0/0 | n/a | 2/3 (40: INV) | (partial) |
| 20261108-235457, 235605 (--only 14, 40, 52) | Fix B | n/a | 0/0 | n/a | 3/3, 3/3 | (partial) |
| 20261108-235732 | full, Fix B | 1.0 | 20/20 | 41/41 | 13/14 (34) | PASS |
| 20261109-002114 | full, Fix B | 1.0 | 20/20 | 41/41 | 10/14 (14, 35, 48, 52) | FAIL |
| 20261109-004657 | full, Fix C | 1.0 | 20/20 | 41/41 | 12/14 (34, 48) | PASS |
| 20261109-011347, 011459 (--only 14, 40, 52) | Fix C | n/a | 0/0 | n/a | 3/3, 3/3 | (partial) |

Clean rejections outside this round's scope, not fixed: 34 (SMOKE_OK line has no workbench= field, blocker, 2/3 full runs, same reason
both times; looks valid against the SMOKE_OK contract), 48 (NoLift stored as a state and the default; gameplay-code.md says NO_LIFT is derived and DEC-01 says no input
is UP_OPEN, 2/3, looks stale against the 11/8 attack baseline), 35 (rule test cites INV-1 but never calls RequestEmit, 1/3).
- MUST_CATCH cases 37 and 38 were caught in every run.

## Round 9 (clean cases re-filed to GDD 1.3 and 6130c77)
Only clean cases and this file were touched; no defective case or expected.json changed.
- All 14 clean cases: the GDD rules line now cites GDD 1.3 (NO_LIFT derived, no per-state gravity multiplier, DEC-01 holds, DEC-02
  fires +X only in ATTACK_DESCENT, APPROVED_P0 flags default on) instead of GDD B1.0 and "COM-01 trigger is OPEN".
- 34: SMOKE_OK line has workbench=0, with workbench-check PASS and BUILD_INFO workbench=0.
- 35: the rule test no longer claims INV-1; it covers CanEmit, and the merged world test that calls RequestEmit cites INV-1.
- 48: rewritten to DEC-01: starts UpOpen, ApplyInput(FUmbrellaInput) resolves shield > attack > UpOpen, no NoLift state.
- 13, 33: EUmbrellaConfig list is the GDD 1.3 states; GravityScale is one value for every falling state.
- 14, 35: COM-01 is MVP 9 (APPROVED_P0), not Stretch; 14 names the ATTACK_DESCENT trigger and +X aim. 46: WIND-01 is MVP 11.
- 32: one bolt per volley (BOLT_Single). 40, 52: GDD 1.3 §8.

| Run | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|
| 20261109-015026 | 0.976 | 20/20 | 41/41 | 14/14 | pass true, recall below 1.0 |
| 20261109-021615 | 1.0 | 20/20 | 41/41 | 14/14 | PASS |
| 20261109-024124 | 1.0 | 20/20 | 41/41 | 14/14 | PASS |

Reviewer mistake, not fixed: 015026 missed 49 inv-untested on location. It named INV-2 at HealthComponent.h:3 in the summary but
filed the finding at HealthComponent.cpp:42, outside the planted range.
- Defective cases still cite GDD B1.0 in their GDD rules line.
- MUST_CATCH cases 37 and 38 were caught in every run.

## Round 10 (defective cases re-filed to GDD 1.3)
The 41 defective cases still cited GDD B1.0, so a reviewer could tell clean from defective by the citation. Only
defective cases and this file were touched. No planted defect, expected verdict or line range changed, and no diff line
count changed, so expected.json is untouched.
- All 41 defective cases: the GDD rules line is now the clean cases' GDD 1.3 line.
- GDD B §3/§4/§8/§9 references now cite GDD 1.3 (02, 03, 10, 17, 29, 30, 31, 38, 39, 43, 45, 47, 51).
- 04, 25: COM-01 is MVP 9 (APPROVED_P0), not Stretch. RequestEmit's trigger is ATTACK_DESCENT with +X aim, matching 14.
- 45: WIND-01 is MVP 11, matching 46. 19, 55: one bolt per volley (BOLT_Single), matching 32.
- 05, 20, 26: EUmbrellaConfig list and the GravityScale wording match 13/33.
- 03, 10, 12, 27, 37: tests set ATTACK_DESCENT/SHIELD_DESCENT (ApplyInput), not NoLift or RequestOpen/RequestClose.
- 07, 36: Input Adapter binds IA_Attack and IA_Shield (DEC-01), not IA_Umbrella; dropped "no attack input until DEC-01/02".
- 17: Config starts UpOpen (diff context line), and the test sets AttackDescent twice and then UpOpen once.
- 47: starts UpOpen (bUpOpen = true); RequestClose gives AttackDescent and is called on IA_Attack. The planted bFalling
  bool at line 49 is unchanged.
- 31: DEC-06 is the provisional 90 s survival default (END-01.survival_s), not a 150 s fixture.
- 02: BossTargetHit(region=BODY); the CLOCK collider is a later card (DEC-08, OWL-05).
- 7c94d50 changed one reviewer-visible rule (workbench #ifdef). No case uses it, so no clean case went stale.

| Run | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|
| 20261109-031511 | 1.0 | 20/20 | 41/41 | 14/14 | PASS |
| 20261109-034016 | 1.0 | 20/20 | 41/41 | 14/14 | PASS |
| 20261109-040547 | 1.0 | 20/20 | 41/41 | 14/14 | PASS |

- No reviewer misses. MUST_CATCH cases 37 and 38 were caught in every run.

## Round 11 (re-run against the rules at 50927e5)
The rules changed between 19251b5 and 50927e5 (smoke hook contract, GetMutableDefault/const_cast ban, tuning via GetDefault,
build commit stamp, build log last line, input_vz on SMOKE_OK). Only case 34 went stale; no defective case or expected.json changed.
- 34: evidence.txt now pastes the build script's last line (`build exit: 0  mode=nonunity  commit=3e7a91c ...`), adds
  input_vz=-412 to SMOKE_OK, says the package stamped UMBRELLAELLA_BUILD_COMMIT=3e7a91c (BUILD_INFO commit=3e7a91c), and adds the
  SMOKE_EFFECTIVE at=start and at=end lines (commit=3e7a91c workbench=0 platform=Windows manifest=1.3-m1) with bake_preset.py
  effective PASS.

| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 20261109-103039 | full, 34 not yet fixed (stopped earlier attempt) | 1.0 | 20/20 | 41/41 | 13/14 (34: SMOKE_OK has no input_vz) | pass true |
| 20261109-105727 | full, 34 not yet fixed (stopped partway, 40/55 cases, not scored) | n/a | n/a | n/a | n/a | (partial) |
| 20261109-112117 (--only 34) | 34 fixed | n/a | 0/0 | n/a | 1/1 | (partial) |
| 20261109-112144 | full, 34 fixed | 1.0 | 20/20 | 41/41 | 14/14 | PASS |
| 20261109-114643 | full, 34 fixed | 1.0 | 20/20 | 41/41 | 14/14 | PASS |
| 20261109-121135 | full, 34 fixed | 1.0 | 20/20 | 41/41 | 14/14 | PASS |

- No reviewer misses. MUST_CATCH cases 37 and 38 were caught in every run.
- Unit tests: `python3 -m unittest discover -s tests` -> Ran 1458 tests, OK (skipped=2).

## Round 13 (Official Rules round, on top of 2236f37)
Rules the reviewer loads changed only in the editor MCP pointer in `pipeline/unreal-rules.md`; no case or expected.json changed.

| Run | Change | Recall | Blockers | Defective blocked | Clean approved | Bar |
|---|---|---|---|---|---|---|
| 20261109-175718 | full, 55 cases | 1.0 | 20/20 | 41/41 | 14/14 | PASS |

- No reviewer misses. MUST_CATCH cases 37 and 38 were caught.
