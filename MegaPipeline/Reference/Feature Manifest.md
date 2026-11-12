> Generated from `docs/feature-manifest.json` at `a11903f` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

```json
{
 "manifest_version": "SH1.0-m1",
 "gdd_revision": "SH1.0",
 "gdd_snapshot": "docs/gdd/GDD-SH1.0.md",
 "rules_pdf": {
  "docs/rules/2026_Epic_AI_MegaJam_Official_Rules_EN.pdf": "71457d4dc8bea132e2a45dbffcffddcd6b9c69330706595b1e5fe32e9f042603"
 },
 "gdd_snapshots": {
  "docs/gdd/GDD-B1.0.md": "d49509cb448446d27e933ce38cd3ea0b3ed2150ea5cc1fa9bdb9f4aca942858d",
  "docs/gdd/GDD-1.3.md": "4d7e985b07e547b70d673f8feeea3451ecbbac8c2a1745d5246e4deb7c6bf6c8",
  "docs/gdd/GDD-SH1.0.md": "6fa96facfec7f4077c44ed688cdadd076faef8440f19e8a6f86966c583ca5684"
 },
 "note": "One record per Rule ID in the current GDD snapshot (GDD SH1.0, Umbrella Ella: The Stolen Hour). Statuses are copied from the GDD, never promoted or demoted: Rick approved every filled requirement as APPROVED_P0, priority P0 (revision note 2026-11-12), so all 204 feature records are APPROVED_P0, implementation_authorized and on. Empty template rows stay OPEN and are not features (open_without_id). The 7 approved note and prompt rows the GDD prints without an ID keep their content in approved_without_id with the feature that carries them (D-new-sh10-idless-rows). The tests mapping (feature -> QA-29..QA-42) is the pipeline's reading of the GDD's acceptance scenarios (D-new-qa-mapping). Numbers: approved_parameters traces each start to one GDD sentence (the GDD's section 9 parameter tables are still blank, so no value has a dev range yet: D-new-sh10-param-ranges). GDD 1.3 and B1.0 are history only. Checked by tools/manifest_check.py.",
 "statuses": [
  "CONFIRMED",
  "APPROVED_P0",
  "APPROVED_P1",
  "PROPOSED",
  "EXPERIMENT",
  "DEFERRED",
  "OPEN",
  "REJECTED"
 ],
 "priorities": [
  "P0",
  "P0_recommended",
  "P1_candidate",
  "experiment",
  "unstated",
  "none"
 ],
 "modules": {
  "input_adapter": "Input Adapter",
  "player_motor": "Player Motor",
  "umbrella_state": "Umbrella State",
  "attack_emitter": "Attack Emitter",
  "defense_receiver": "Defense Receiver",
  "health_condition": "Health/Condition",
  "projectile_service": "Projectile Service",
  "boss_director": "Boss Director",
  "wind_hazard_field": "Wind/Hazard Field",
  "encounter_director": "Encounter Director",
  "feedback_adapter": "Feedback Adapter",
  "test_harness": "Test Harness",
  "hit_region_router": "Hit Region Router",
  "animation_presenter": "Animation Presenter",
  "background_presenter": "Background Presenter",
  "progression": "Progression (XP, levels, points, unlocks)",
  "persistence": "Persistence (earned character data, checkpoints)",
  "level_director": "Level Director (Director's Cut route, chunks, refuges)",
  "enemy_director": "Enemy Director (regular enemies)",
  "menu_flow": "Menu Flow (start, pause, settings, credits, results)",
  "story_presenter": "Story Presenter (captions, narration, ending)",
  "hud": "HUD (clock health/lives hands, XP ring)"
 },
 "events": [
  "UmbrellaConfigChanged",
  "LiftAvailabilityChanged",
  "PlayerHealthChanged",
  "ProjectileSpawned",
  "ProjectileContact",
  "CatchAttempt",
  "CatchSucceeded",
  "CatchFailed",
  "BossTargetHit",
  "BossAttackTelegraphed",
  "WindEntered",
  "WindExited",
  "PlayerDefeated",
  "EncounterCompleted",
  "TestPresetLoaded",
  "AnimationCue",
  "BackgroundLooped",
  "ModeSelected",
  "PhaseStarted",
  "CheckpointReached",
  "CheckpointRetried",
  "LifeLost",
  "BossPartDestroyed",
  "XPAwarded",
  "LevelGained",
  "RunCompleted"
 ],
 "event_fields": [
  "timestamp_or_frame",
  "source_id",
  "target_id",
  "run_config_id",
  "relevant_feature_ids"
 ],
 "rejected_without_id": [],
 "approved_without_id": [
  {
   "gdd_cell": "[unassigned]",
   "status": "APPROVED_P0",
   "section": "4. Gameplay systems / Director’s Cut progression baseline",
   "starts": "Still to define: final boss-part XP",
   "what": "progression note: open boss-part XP tuning and snapshot details",
   "carried_by": "FLOW-13",
   "id_needed": false
  },
  {
   "gdd_cell": "[pending]",
   "status": "APPROVED_P0",
   "section": "8. Art, animation, VFX and audio / Exact text-only creation prompt (provisional)",
   "starts": "Pause background text-only art prompt",
   "what": "asset prompt for the Pause background (ART-08 UI coverage)",
   "carried_by": "FLOW-35",
   "id_needed": false
  },
  {
   "gdd_cell": "[pending]",
   "status": "APPROVED_P0",
   "section": "8. Art, animation, VFX and audio / Exact text-only creation prompt (provisional)",
   "starts": "Pause animation / integration prompt",
   "what": "asset prompt for the animated Pause backdrop (ART-08)",
   "carried_by": "FLOW-35",
   "id_needed": false
  },
  {
   "gdd_cell": "[unassigned]",
   "status": "APPROVED_P0",
   "section": "8. Art, animation, VFX and audio / Art-director brief",
   "starts": "Team / tools / delivery",
   "what": "art-director brief note: team, tools and delivery",
   "carried_by": "ART-05",
   "id_needed": false
  },
  {
   "gdd_cell": "[unassigned]",
   "status": "APPROVED_P0",
   "section": "8. Art, animation, VFX and audio / Art-director brief",
   "starts": "Decision ownership",
   "what": "art-director brief note: who approves art",
   "carried_by": "ART-05",
   "id_needed": false
  },
  {
   "gdd_cell": "[unassigned]",
   "status": "APPROVED_P0",
   "section": "8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts",
   "starts": "Clock HUD art-generation prompt",
   "what": "asset prompt for the clock HUD (FLOW-30, ART-08)",
   "carried_by": "ART-09",
   "id_needed": false
  },
  {
   "gdd_cell": "[unassigned]",
   "status": "APPROVED_P0",
   "section": "10. Testing and acceptance / Acceptance coverage (draft, NOT RUN)",
   "starts": "For every scenario record exact build",
   "what": "acceptance-coverage preamble for QA-29..QA-42",
   "carried_by": "QA-29..QA-42 (every QA scenario record)",
   "id_needed": false
  }
 ],
 "open_without_id": [
  {
   "gdd_cell": "[pending]",
   "section": "1. Game overview and player experience",
   "text": "[Overview requirement OPEN]"
  },
  {
   "gdd_cell": "[pending]",
   "section": "9. Technical and build requirements",
   "text": "[Technical requirement OPEN]"
  },
  {
   "gdd_cell": "[pending]",
   "section": "10. Testing and acceptance",
   "text": "[Additional test / release requirement OPEN]"
  },
  {
   "gdd_cell": "[pending]",
   "section": "11. Minimum playable scope and open decisions",
   "text": "[Scope decision pending]"
  },
  {
   "gdd_cell": "[pending]",
   "section": "12. Audit and pipeline handoff",
   "text": "[Additional audit requirement OPEN]"
  }
 ],
 "build_parameters": {
  "camera_mode": {
   "default": "fixed_single_screen",
   "allowed": [
    "fixed_single_screen",
    "scrolling"
   ],
   "status": "APPROVED_P0",
   "gdd_ref": "GDD SH1.0: the Keeper fight is one arena (section 5; exact camera OPEN); the Director's Cut route scrolls through nine chunks (FLOW-24, CAM-08). Default fixed_single_screen = the Keeper fight and the Start Game mode (G1); scrolling = the Director's Cut level.",
   "known_limitations": [
    "Pipeline default (D-new-sh10-camera): the GDD leaves exact spawn, camera and collision proportions OPEN. Keeper fight: fixed 16:9 view; Director's Cut level: side-scrolling camera that reveals the next current, hazard and exit (CAM-08)."
   ]
  }
 },
 "team_baseline": {
  "standing": "History. The 11/8 team baseline, the 2026-11-09 defaults and GDD 1.3 are superseded by GDD SH1.0 (D-new-gdd-sh10). Kept only so older cards can be read."
 },
 "features": [
  {
   "feature_id": "FLOW-02",
   "name": "two_mode_routes",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_02",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 2. Player journey and modes."
   ]
  },
  {
   "feature_id": "FLOW-03",
   "name": "first_start_tutorials_skippable",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_03",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 2. Player journey and modes.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-04",
   "name": "win_ending_story_credits",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_04",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 2. Player journey and modes.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "MOVE-04",
   "name": "shared_default_controls",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_04",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-05",
   "name": "rise_shoot_absorb_freefall_inputs",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-06",
   "name": "hop_dash_ride_inputs",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-07",
   "name": "trim_fixed_right_fire_no_steering",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-08",
   "name": "directors_cut_spell_select_pause_retry",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_08",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-09",
   "name": "menu_navigation_inputs",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_09",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-10",
   "name": "controller_menu_remaps_keyboard_mouse",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_10",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-11",
   "name": "global_player_rules",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_11",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-12",
   "name": "no_ammo_four_weapons_cap",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-31"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_12",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-13",
   "name": "four_state_movement_contract",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_13",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-14",
   "name": "fire_and_heal_only_while_dropping",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_14",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-15",
   "name": "protection_baseline",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-33"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_15",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-16",
   "name": "tutorial_redesign_controls_unchanged",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_16",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-17",
   "name": "controller_menu_remap",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_17",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Controls at a glance."
   ]
  },
  {
   "feature_id": "MOVE-18",
   "name": "shared_mechanics_both_modes",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-33"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_18",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Shared player contract."
   ]
  },
  {
   "feature_id": "MOVE-19",
   "name": "movement_input_priority",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_19",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Shared player contract."
   ]
  },
  {
   "feature_id": "MOVE-20",
   "name": "action_eligibility_interruption",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_20",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Shared player contract."
   ]
  },
  {
   "feature_id": "MOVE-21",
   "name": "movement_baseline_numbers",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [
    "dash_cooldown_s",
    "dash_distance",
    "dash_duration_s",
    "fall_speed",
    "free_fall_dash_multiplier",
    "free_fall_speed",
    "hop_cooldown_s",
    "hop_distance",
    "hop_duration_s",
    "hop_protection_s",
    "horizontal_max_speed",
    "rise_speed",
    "vertical_trim_pct"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_21",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Shared player contract."
   ]
  },
  {
   "feature_id": "SURV-05",
   "name": "clock_hud_health_lives_lift",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "health_condition"
   ],
   "conflicts": [],
   "parameters": [
    "min_lift",
    "post_hit_protection_s"
   ],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "SURV_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Shared player contract.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "UMB-05",
   "name": "absorption_baseline",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "umbrella_state",
    "defense_receiver"
   ],
   "conflicts": [],
   "parameters": [
    "absorb_cone_deg",
    "absorb_range",
    "capture_distance",
    "heal_per_recovery_rank",
    "heal_per_yellow",
    "pull_speed"
   ],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "UMB_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Shared player contract."
   ]
  },
  {
   "feature_id": "WIND-03",
   "name": "harmless_currents_and_boundaries",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "wind_hazard_field",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "WIND_03",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Shared player contract."
   ]
  },
  {
   "feature_id": "MOVE-22",
   "name": "profile_ownership_wind_response",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "input_adapter",
    "player_motor"
   ],
   "conflicts": [],
   "parameters": [
    "wind_acceleration",
    "wind_falling_decay",
    "wind_open_decay"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "MOVE_22",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Shared player contract."
   ]
  },
  {
   "feature_id": "COM-05",
   "name": "spell_set_by_mode",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "attack_emitter",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-31"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Four spell mechanics."
   ]
  },
  {
   "feature_id": "COM-06",
   "name": "small_blasts",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "attack_emitter",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [
    "damage",
    "range",
    "shots_per_s",
    "speed"
   ],
   "emits": [],
   "tests": [
    "QA-31"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Small Blasts."
   ]
  },
  {
   "feature_id": "COM-07",
   "name": "streamed_blast",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "attack_emitter",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [
    "growth_speed",
    "max_range",
    "tick_damage",
    "ticks_per_s",
    "width"
   ],
   "emits": [],
   "tests": [
    "QA-31"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Streamed Blast."
   ]
  },
  {
   "feature_id": "COM-08",
   "name": "twin_stars",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "attack_emitter",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [
    "damage",
    "range",
    "separation",
    "speed",
    "volleys_per_s"
   ],
   "emits": [],
   "tests": [
    "QA-31"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_08",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Twin Stars."
   ]
  },
  {
   "feature_id": "COM-09",
   "name": "needle_spell",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "attack_emitter",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [
    "damage",
    "range",
    "shots_per_s",
    "size_multiplier",
    "speed"
   ],
   "emits": [],
   "tests": [
    "QA-31"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_09",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Needle Spell."
   ]
  },
  {
   "feature_id": "COM-10",
   "name": "exactly_four_weapon_families",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "attack_emitter",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-31"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_10",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Weapon scope and equipment."
   ]
  },
  {
   "feature_id": "COM-11",
   "name": "spell_equip_unlock_rules",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "attack_emitter",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-29"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_11",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 3. Controls and player abilities / Weapon scope and equipment."
   ]
  },
  {
   "feature_id": "FLOW-05",
   "name": "completed_run_difficulty_scaling",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [
    "cadence_multiplier_cap",
    "cadence_multiplier_step",
    "count_multiplier_cap",
    "count_multiplier_step",
    "hp_multiplier_cap",
    "hp_multiplier_step"
   ],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Progression system card."
   ]
  },
  {
   "feature_id": "FLOW-06",
   "name": "final_hour_extreme_run",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [
    "final_hour_cadence_multiplier",
    "final_hour_count_multiplier",
    "final_hour_hp_multiplier"
   ],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Progression system card.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-07",
   "name": "checkpoint_retry_xp_policy",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression",
    "persistence"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Progression system card."
   ]
  },
  {
   "feature_id": "FLOW-08",
   "name": "quit_reload_checkpoint_progress",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression",
    "persistence"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_08",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Progression system card."
   ]
  },
  {
   "feature_id": "FLOW-09",
   "name": "checkpoint_retry_three_lives_full_heal",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression",
    "persistence"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-34"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_09",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Progression system card.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-10",
   "name": "win_carries_progression",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression",
    "persistence"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_10",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Progression system card."
   ]
  },
  {
   "feature_id": "FLOW-11",
   "name": "reallocation_run2_onward",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_11",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Progression system card.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-12",
   "name": "retry_enemy_xp_again",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_12",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Progression system card."
   ]
  },
  {
   "feature_id": "FLOW-13",
   "name": "boss_part_xp_and_rollback",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression",
    "persistence"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_13",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Progression system card."
   ]
  },
  {
   "feature_id": "FLOW-14",
   "name": "progression_baseline",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_14",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline."
   ]
  },
  {
   "feature_id": "FLOW-15",
   "name": "levels_points_xp_curve",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [
    "cumulative_xp_level_10",
    "cumulative_xp_level_20",
    "cumulative_xp_level_30",
    "cumulative_xp_level_62",
    "earned_points_at_cap",
    "level_cap",
    "max_hits_per_life",
    "max_lives",
    "start_hits_per_life",
    "start_lives",
    "target_completed_runs",
    "target_xp_per_run",
    "xp_curve_base"
   ],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_15",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline."
   ]
  },
  {
   "feature_id": "FLOW-16",
   "name": "spell_unlock_schedule",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [
    "unlock_level_needle",
    "unlock_level_streamed",
    "unlock_level_twin"
   ],
   "emits": [],
   "tests": [
    "QA-31"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_16",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline."
   ]
  },
  {
   "feature_id": "SURV-06",
   "name": "health_upgrade_tracks",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "health_condition",
    "progression"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "SURV_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "SURV-07",
   "name": "health_baseline_and_ranks",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "health_condition",
    "progression"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "SURV_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline."
   ]
  },
  {
   "feature_id": "FLOW-17",
   "name": "upgrade_application_safety",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_17",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-18",
   "name": "purchase_vs_reallocation",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_18",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline."
   ]
  },
  {
   "feature_id": "FLOW-19",
   "name": "kill_xp_rewards",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [
    "xp_clock",
    "xp_courier",
    "xp_floodstrider",
    "xp_front",
    "xp_middle",
    "xp_rear",
    "xp_roadwarden",
    "xp_wings"
   ],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_19",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline."
   ]
  },
  {
   "feature_id": "FLOW-20",
   "name": "reward_reconciliation",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression",
    "persistence"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_20",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline."
   ]
  },
  {
   "feature_id": "FLOW-21",
   "name": "difficulty_runs_contract",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_21",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline."
   ]
  },
  {
   "feature_id": "FLOW-22",
   "name": "persistence_contract",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression",
    "persistence"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_22",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline."
   ]
  },
  {
   "feature_id": "FLOW-23",
   "name": "developer_level_fixture",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "progression"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-31"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_23",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 4. Gameplay systems / Director’s Cut progression baseline.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "OWL-06",
   "name": "keeper_three_phase_checkpoints",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-34"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Attack allocation by phase."
   ]
  },
  {
   "feature_id": "OWL-07",
   "name": "keeper_complete_contract",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Complete Keeper attack contract."
   ]
  },
  {
   "feature_id": "OWL-08",
   "name": "keeper_body_and_hp",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "clock_hp",
    "clock_reserve_hp",
    "front_hp",
    "middle_hp",
    "rear_hp",
    "wings_hp"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_08",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Body, eligibility and phase changes."
   ]
  },
  {
   "feature_id": "OWL-09",
   "name": "wing_first_gating",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_09",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Body, eligibility and phase changes."
   ]
  },
  {
   "feature_id": "OWL-10",
   "name": "phase_checkpoint_retry",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32",
    "QA-34"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_10",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Body, eligibility and phase changes."
   ]
  },
  {
   "feature_id": "OWL-11",
   "name": "red_pressure",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [
    "red_interval_s",
    "red_spacing_s",
    "red_speed_clock",
    "red_speed_mechanisms",
    "red_speed_wings",
    "red_spread_clock_deg",
    "red_spread_mechanisms_deg",
    "red_spread_wings_deg",
    "reduced_interval_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_11",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Red pressure and yellow recovery."
   ]
  },
  {
   "feature_id": "OWL-12",
   "name": "red_cue_response",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32",
    "QA-33"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_12",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Red pressure and yellow recovery."
   ]
  },
  {
   "feature_id": "OWL-13",
   "name": "yellow_contract",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [
    "yellow_interval_s",
    "yellow_size",
    "yellow_speed_clock",
    "yellow_speed_mechanisms",
    "yellow_speed_wings"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_13",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Red pressure and yellow recovery."
   ]
  },
  {
   "feature_id": "OWL-14",
   "name": "yellow_presentation",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_14",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Red pressure and yellow recovery."
   ]
  },
  {
   "feature_id": "OWL-15",
   "name": "wing_gust_warning",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "gust_warning_s",
    "physical_interval_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_15",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Wing gust."
   ]
  },
  {
   "feature_id": "OWL-16",
   "name": "wing_gust_action",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "gust_band_width",
    "gust_lifetime_s",
    "gust_push",
    "gust_speed"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_16",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Wing gust."
   ]
  },
  {
   "feature_id": "OWL-17",
   "name": "wing_gust_cleanup",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_17",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Wing gust."
   ]
  },
  {
   "feature_id": "OWL-18",
   "name": "talon_trigger",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "talon_reach",
    "talon_warning_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_18",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Close talon rake."
   ]
  },
  {
   "feature_id": "OWL-19",
   "name": "talon_active",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "talon_strike_s",
    "talon_tip_width"
   ],
   "emits": [],
   "tests": [
    "QA-32",
    "QA-33"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_19",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Close talon rake."
   ]
  },
  {
   "feature_id": "OWL-20",
   "name": "talon_recovery_rearm",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "talon_cooldown_s",
    "talon_rearm_exit",
    "talon_recovery_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_20",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Close talon rake."
   ]
  },
  {
   "feature_id": "OWL-21",
   "name": "front_cast_warning",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "cast_warning_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_21",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Front mechanism cast."
   ]
  },
  {
   "feature_id": "OWL-22",
   "name": "front_cast_active",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "chain_head_width",
    "chain_reach",
    "chain_speed"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_22",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Front mechanism cast."
   ]
  },
  {
   "feature_id": "OWL-23",
   "name": "front_cast_recovery",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "chain_return_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_23",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Front mechanism cast."
   ]
  },
  {
   "feature_id": "OWL-24",
   "name": "middle_cast_parity",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "middle_offset"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_24",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Middle mechanism cast."
   ]
  },
  {
   "feature_id": "OWL-25",
   "name": "middle_cast_curved_path",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_25",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Middle mechanism cast."
   ]
  },
  {
   "feature_id": "OWL-26",
   "name": "rear_cast_two_stage",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "rear_pause_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_26",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Rear two-stage cast."
   ]
  },
  {
   "feature_id": "OWL-27",
   "name": "rear_cast_readability",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_27",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Rear two-stage cast."
   ]
  },
  {
   "feature_id": "OWL-28",
   "name": "clock_double_beat",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "repeat_recovery_s",
    "repeat_wait_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_28",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Clock double beat, cover and effects."
   ]
  },
  {
   "feature_id": "OWL-29",
   "name": "clock_protection",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "clock_open_s",
    "clock_protect_recovery_s",
    "final_exposure_cycle_s",
    "final_exposure_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_29",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Clock double beat, cover and effects."
   ]
  },
  {
   "feature_id": "OWL-30",
   "name": "mechanism_break_stun",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "break_stun_s",
    "fire_pause_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_30",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Clock double beat, cover and effects."
   ]
  },
  {
   "feature_id": "OWL-31",
   "name": "clock_hit_slow",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "slow_cooldown_s",
    "slow_s",
    "slow_world_scale"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_31",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Clock double beat, cover and effects."
   ]
  },
  {
   "feature_id": "OWL-32",
   "name": "eye_blackout",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "blackout_s",
    "eye_cooldown_s",
    "eye_window_s"
   ],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_32",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Clock double beat, cover and effects."
   ]
  },
  {
   "feature_id": "OWL-33",
   "name": "time_domains",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_33",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Clock double beat, cover and effects."
   ]
  },
  {
   "feature_id": "OWL-34",
   "name": "physical_move_scheduler",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32",
    "QA-33"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_34",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Scheduler, success and reset."
   ]
  },
  {
   "feature_id": "OWL-35",
   "name": "success_and_reset",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "boss_director",
    "hit_region_router"
   ],
   "conflicts": [],
   "parameters": [
    "departure_s"
   ],
   "emits": [],
   "tests": [
    "QA-34"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "OWL_35",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Scheduler, success and reset.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-24",
   "name": "directors_cut_nine_chunk_route",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [
    "chunk_length"
   ],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_24",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Director’s Cut full level."
   ]
  },
  {
   "feature_id": "FLOW-25",
   "name": "route_readability",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_25",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Director’s Cut full level."
   ]
  },
  {
   "feature_id": "FLOW-26",
   "name": "broken_mill_direction",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_26",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Director’s Cut full level."
   ]
  },
  {
   "feature_id": "HAZ-02",
   "name": "broken_mill_scope",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_02",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-03",
   "name": "broken_mill_room_guard",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_03",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-04",
   "name": "broken_mill_activation",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_04",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-05",
   "name": "broken_mill_one_shot_per_pass",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-06",
   "name": "broken_mill_two_choice_winds",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-07",
   "name": "broken_mill_field_ownership",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-08",
   "name": "broken_mill_underpass_estimates",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_08",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-09",
   "name": "broken_mill_ray_estimates",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_09",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-10",
   "name": "broken_mill_firing_fixture",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_10",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-11",
   "name": "broken_mill_firing_window",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_11",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-12",
   "name": "broken_mill_emission_checks",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_12",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-13",
   "name": "broken_mill_delayed_impact",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_13",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-14",
   "name": "broken_mill_prototype_checks",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_14",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-15",
   "name": "broken_mill_recovery_checks",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_15",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-16",
   "name": "broken_mill_human_acceptance",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_16",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-17",
   "name": "broken_mill_pool_gate",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_17",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "HAZ-18",
   "name": "broken_mill_art_evidence",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_18",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Broken Mill Roadwarden: proposed one-room test."
   ]
  },
  {
   "feature_id": "CAM-03",
   "name": "required_paths_basic_kit",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "CAM_03",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Traversal, geometry and camera contract."
   ]
  },
  {
   "feature_id": "CAM-04",
   "name": "calibrate_before_multiplying",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "CAM_04",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Traversal, geometry and camera contract."
   ]
  },
  {
   "feature_id": "CAM-05",
   "name": "interface_n",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "CAM_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Traversal, geometry and camera contract."
   ]
  },
  {
   "feature_id": "CAM-06",
   "name": "clearance_rules",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "CAM_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Traversal, geometry and camera contract."
   ]
  },
  {
   "feature_id": "CAM-07",
   "name": "descent_catch_flow",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "CAM_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Traversal, geometry and camera contract."
   ]
  },
  {
   "feature_id": "CAM-08",
   "name": "camera_reveal",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-33"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "CAM_08",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Traversal, geometry and camera contract."
   ]
  },
  {
   "feature_id": "HAZ-19",
   "name": "trap_baseline_air_mill",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_19",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Trap catalogue and pressure budget (proposed adjustable design)."
   ]
  },
  {
   "feature_id": "HAZ-20",
   "name": "timed_shutter",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_20",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Trap catalogue and pressure budget (proposed adjustable design)."
   ]
  },
  {
   "feature_id": "HAZ-21",
   "name": "hostile_bellows",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_21",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Trap catalogue and pressure budget (proposed adjustable design)."
   ]
  },
  {
   "feature_id": "HAZ-22",
   "name": "roof_bridge_teeth",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_22",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Trap catalogue and pressure budget (proposed adjustable design)."
   ]
  },
  {
   "feature_id": "HAZ-23",
   "name": "pressure_contract",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_23",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Trap catalogue and pressure budget (proposed adjustable design)."
   ]
  },
  {
   "feature_id": "COM-12",
   "name": "enemy_gender_variants",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "enemy_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-37"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_12",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Enemy roles and proposed combat baselines.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "COM-13",
   "name": "enemy_dual_color_shots",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "enemy_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-37"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_13",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Enemy roles and proposed combat baselines.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-46",
   "name": "procedural_placement_shot_color",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-40",
    "QA-42"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_46",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Enemy roles and proposed combat baselines.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "HAZ-41",
   "name": "floating_ground_containment",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "enemy_director",
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-41"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_41",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Enemy roles and proposed combat baselines."
   ]
  },
  {
   "feature_id": "FLOW-47",
   "name": "procedural_acceptance_gate",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-40",
    "QA-42"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_47",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Enemy roles and proposed combat baselines."
   ]
  },
  {
   "feature_id": "COM-14",
   "name": "roadwarden",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "enemy_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [
    "roadwarden_hp"
   ],
   "emits": [],
   "tests": [
    "QA-37"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_14",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Enemy roles and proposed combat baselines.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "COM-15",
   "name": "floodstrider",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "enemy_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [
    "floodstrider_hp"
   ],
   "emits": [],
   "tests": [
    "QA-37"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_15",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Enemy roles and proposed combat baselines.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "COM-16",
   "name": "sky_courier",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "enemy_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [
    "courier_hp"
   ],
   "emits": [],
   "tests": [
    "QA-37"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_16",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Enemy roles and proposed combat baselines.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "COM-17",
   "name": "courier_packet_lifecycle",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "enemy_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-37"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_17",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Enemy roles and proposed combat baselines.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "COM-18",
   "name": "kills_optional_firing_windows",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "enemy_director",
    "projectile_service"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-37"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "COM_18",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Enemy roles and proposed combat baselines."
   ]
  },
  {
   "feature_id": "HAZ-24",
   "name": "chunk_catalogue_rules",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_24",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-25",
   "name": "ch01_drop_and_catch",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_25",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-26",
   "name": "ch02_rooftop_line",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_26",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-27",
   "name": "ch03_yellow_crossing",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_27",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-28",
   "name": "ch04_underbridge",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_28",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-29",
   "name": "ch05_over_and_under",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_29",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-30",
   "name": "ch06_countercurrent_mill",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_30",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-31",
   "name": "ch07_shutter_pocket",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_31",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-32",
   "name": "ch08_bellows_lane",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_32",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-33",
   "name": "ch09_eave_transfer",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_33",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-34",
   "name": "ch10_switchback",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_34",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-35",
   "name": "ch11_warden_and_mill",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_35",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-36",
   "name": "ch12_stilt_and_courier",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_36",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-37",
   "name": "nine_slot_grammar",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_37",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-38",
   "name": "safer_bypass",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_38",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-39",
   "name": "seed_fixture_proposals",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_39",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "HAZ-40",
   "name": "determinism_fallback",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director",
    "wind_hazard_field"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "HAZ_40",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Authored 12-chunk / 24-variant catalogue."
   ]
  },
  {
   "feature_id": "FLOW-27",
   "name": "refuge_core",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_27",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Refuges and Keeper handoff."
   ]
  },
  {
   "feature_id": "FLOW-28",
   "name": "checkpoint_passage_boss_arrival",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_28",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Refuges and Keeper handoff."
   ]
  },
  {
   "feature_id": "FLOW-29",
   "name": "purchase_context",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "level_director"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-36"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_29",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 5. Levels and encounters / Refuges and Keeper handoff."
   ]
  },
  {
   "feature_id": "NAR-02",
   "name": "text_narration",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "story_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "NAR_02",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 6. Story and dialogue / Story presentation requirements (Director’s Cut).",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "NAR-03",
   "name": "single_story_delivery",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "story_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "NAR_03",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 6. Story and dialogue / Director’s Cut in-play story delivery."
   ]
  },
  {
   "feature_id": "NAR-04",
   "name": "opening_mother_caption",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "story_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "NAR_04",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 6. Story and dialogue / Director’s Cut in-play story delivery.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "NAR-05",
   "name": "light_and_umbra",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "story_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "NAR_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 6. Story and dialogue / Director’s Cut in-play story delivery."
   ]
  },
  {
   "feature_id": "NAR-06",
   "name": "keeper_clock_hand_clue",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "story_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "NAR_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 6. Story and dialogue / Director’s Cut in-play story delivery."
   ]
  },
  {
   "feature_id": "NAR-07",
   "name": "living_departure_ending",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "story_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "NAR_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 6. Story and dialogue / Director’s Cut in-play story delivery."
   ]
  },
  {
   "feature_id": "NAR-08",
   "name": "retry_and_new_run_story",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "story_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "NAR_08",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 6. Story and dialogue / Director’s Cut in-play story delivery.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-30",
   "name": "clock_health_hud",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "hud",
    "health_condition"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_30",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-48",
   "name": "xp_ring_hud",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "hud",
    "health_condition"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-35"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_48",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility."
   ]
  },
  {
   "feature_id": "FLOW-31",
   "name": "life_hand_depletion",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "hud",
    "health_condition"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_31",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-32",
   "name": "damage_healing_feedback",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "hud",
    "health_condition"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_32",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-33",
   "name": "prototype_health_model",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "hud",
    "health_condition"
   ],
   "conflicts": [],
   "parameters": [
    "chain_damage",
    "old_damage_divisor",
    "projectile_damage",
    "talon_damage",
    "trap_damage"
   ],
   "emits": [],
   "tests": [
    "QA-30"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_33",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-34",
   "name": "start_screen",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_34",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility."
   ]
  },
  {
   "feature_id": "FLOW-35",
   "name": "pause_menu_living_background",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_35",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility."
   ]
  },
  {
   "feature_id": "FLOW-36",
   "name": "player_settings_both_modes",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_36",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility."
   ]
  },
  {
   "feature_id": "FLOW-37",
   "name": "sound_sliders",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [
    "slider_max"
   ],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_37",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility."
   ]
  },
  {
   "feature_id": "FLOW-38",
   "name": "developer_game_options",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_38",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-39",
   "name": "credits",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_39",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-40",
   "name": "submenu_back_save",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_40",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility."
   ]
  },
  {
   "feature_id": "FLOW-49",
   "name": "journey_complete_statistics",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_49",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility / Director’s Cut win results."
   ]
  },
  {
   "feature_id": "FLOW-41",
   "name": "pause_and_start_design_retained",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_41",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility / Settings and earned-character interactions."
   ]
  },
  {
   "feature_id": "FLOW-42",
   "name": "ella_and_spells_purchase_flow",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_42",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility / Settings and earned-character interactions.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-43",
   "name": "settings_save_reset_scope",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_43",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility / Settings and earned-character interactions."
   ]
  },
  {
   "feature_id": "FLOW-44",
   "name": "developer_menu_candidates",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_44",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility / Settings and earned-character interactions.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "FLOW-45",
   "name": "accessibility_help_candidates",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "menu_flow"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "FLOW_45",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 7. Menus, settings and accessibility / Settings and earned-character interactions."
   ]
  },
  {
   "feature_id": "ART-03",
   "name": "new_art_text_only_after_kickoff",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ART_03",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Exact text-only creation prompt (provisional)."
   ]
  },
  {
   "feature_id": "ART-04",
   "name": "shared_start_end_background",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-38"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ART_04",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Exact text-only creation prompt (provisional)."
   ]
  },
  {
   "feature_id": "ART-05",
   "name": "player_experience_brief",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ART_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Art-director brief."
   ]
  },
  {
   "feature_id": "ART-06",
   "name": "visual_direction",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ART_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Art-director brief."
   ]
  },
  {
   "feature_id": "ART-07",
   "name": "gameplay_view_context",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ART_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Art-director brief.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "ANIM-02",
   "name": "animation_family_contract",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "animation_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ANIM_02",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts."
   ]
  },
  {
   "feature_id": "ANIM-03",
   "name": "ella_animation_coverage",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "animation_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ANIM_03",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts."
   ]
  },
  {
   "feature_id": "ANIM-04",
   "name": "whole_character_condition",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "animation_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ANIM_04",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "ANIM-05",
   "name": "spell_asset_families",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "animation_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ANIM_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts."
   ]
  },
  {
   "feature_id": "ANIM-06",
   "name": "keeper_animation_coverage",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "animation_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ANIM_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts."
   ]
  },
  {
   "feature_id": "ANIM-07",
   "name": "keeper_animation_invariants",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "animation_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ANIM_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts."
   ]
  },
  {
   "feature_id": "ANIM-08",
   "name": "world_enemy_animation_coverage",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "animation_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-37"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ANIM_08",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts."
   ]
  },
  {
   "feature_id": "ART-08",
   "name": "ui_art_coverage",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ART_08",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts."
   ]
  },
  {
   "feature_id": "ART-09",
   "name": "clock_hud_production",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ART_09",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts."
   ]
  },
  {
   "feature_id": "ANIM-09",
   "name": "audio_coverage",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "animation_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ANIM_09",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts."
   ]
  },
  {
   "feature_id": "ANIM-10",
   "name": "asset_family_acceptance",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "animation_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ANIM_10",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts."
   ]
  },
  {
   "feature_id": "ART-10",
   "name": "enemy_dual_color_art",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-37"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "ART_10",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Production state coverage and replaceable art contracts.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "BG-02",
   "name": "environment_components",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "background_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "BG_02",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Environment component recreation inventory."
   ]
  },
  {
   "feature_id": "BG-03",
   "name": "atmosphere_set",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "background_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "BG_03",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Environment component recreation inventory."
   ]
  },
  {
   "feature_id": "BG-04",
   "name": "architecture_and_land",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "background_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "BG_04",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Environment component recreation inventory."
   ]
  },
  {
   "feature_id": "BG-05",
   "name": "visual_assembly_layers",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "background_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "BG_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Environment component recreation inventory."
   ]
  },
  {
   "feature_id": "BG-06",
   "name": "clock_water_wind_assembly",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "background_presenter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "BG_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Environment component recreation inventory."
   ]
  },
  {
   "feature_id": "VFX-02",
   "name": "unreal_vfx_delivery",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "VFX_02",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Unreal VFX creation and integration."
   ]
  },
  {
   "feature_id": "VFX-03",
   "name": "weapon_vfx_wiring",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-31"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "VFX_03",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Unreal VFX creation and integration."
   ]
  },
  {
   "feature_id": "VFX-04",
   "name": "shared_combat_vfx_wiring",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "VFX_04",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Unreal VFX creation and integration."
   ]
  },
  {
   "feature_id": "VFX-05",
   "name": "keeper_vfx_wiring",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "VFX_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Unreal VFX creation and integration."
   ]
  },
  {
   "feature_id": "VFX-06",
   "name": "separate_render_layers",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "VFX_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Unreal VFX creation and integration."
   ]
  },
  {
   "feature_id": "VFX-07",
   "name": "nearby_surface_illumination",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "VFX_07",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Unreal VFX creation and integration."
   ]
  },
  {
   "feature_id": "VFX-08",
   "name": "lit_material_dependency",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "VFX_08",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Unreal VFX creation and integration.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "VFX-09",
   "name": "vfx_readability_sync",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "VFX_09",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Unreal VFX creation and integration."
   ]
  },
  {
   "feature_id": "VFX-10",
   "name": "vfx_performance_accessibility",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "VFX_10",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Unreal VFX creation and integration.",
    "The row keeps explicit OPEN details; they stay OPEN (docs/decisions.md D-new-sh10-open-details), never a reason to drop the row."
   ]
  },
  {
   "feature_id": "VFX-11",
   "name": "vfx_acceptance",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "feedback_adapter"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "VFX_11",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 8. Art, animation, VFX and audio / Unreal VFX creation and integration."
   ]
  },
  {
   "feature_id": "CORE-04",
   "name": "system_boundaries",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "test_harness"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "CORE_04",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 9. Technical and build requirements / System ownership and reproducible build identity."
   ]
  },
  {
   "feature_id": "CORE-05",
   "name": "stable_anchors_input_consumption",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "test_harness"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-32"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "CORE_05",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 9. Technical and build requirements / System ownership and reproducible build identity."
   ]
  },
  {
   "feature_id": "CORE-06",
   "name": "build_identity_record",
   "status": "APPROVED_P0",
   "status_text": "APPROVED_P0",
   "owner": "unassigned",
   "priority": "P0",
   "default_enabled": true,
   "requires": [
    "test_harness"
   ],
   "conflicts": [],
   "parameters": [],
   "emits": [],
   "tests": [
    "QA-39"
   ],
   "implementation_authorized": true,
   "ticket": null,
   "flag": "CORE_06",
   "gdd_revision": "SH1.0",
   "known_limitations": [
    "APPROVED_P0 in GDD SH1.0 (Rick's approval of all filled requirements, revision note 2026-11-12). GDD section: 9. Technical and build requirements / System ownership and reproducible build identity."
   ]
  }
 ],
 "approved_parameters": {
  "source": "GDD SH1.0 numbers as printed in sections 3, 4, 5 and 7 (adjustable prototype baselines, not balance). The GDD's section 9 parameter tables are blank, so each value has a start traced to one GDD sentence (tools/manifest_check.py PROSE_ROWS) and no dev range or step (D-new-sh10-param-ranges). Units: GDD world units and seconds; pipeline default 1 world unit = 1 Unreal cm (D-new-sh10-units). No AI tunes these.",
  "values": {
   "MOVE-21.rise_speed": {
    "start": 120,
    "unit": "units/s"
   },
   "MOVE-21.fall_speed": {
    "start": 330,
    "unit": "units/s"
   },
   "MOVE-21.free_fall_speed": {
    "start": 610,
    "unit": "units/s"
   },
   "MOVE-21.horizontal_max_speed": {
    "start": 290,
    "unit": "units/s"
   },
   "MOVE-21.vertical_trim_pct": {
    "start": 20,
    "unit": "%"
   },
   "MOVE-21.hop_distance": {
    "start": 40,
    "unit": "units"
   },
   "MOVE-21.hop_duration_s": {
    "start": 0.22,
    "unit": "s"
   },
   "MOVE-21.hop_cooldown_s": {
    "start": 0.7,
    "unit": "s"
   },
   "MOVE-21.hop_protection_s": {
    "start": 0.2,
    "unit": "s"
   },
   "MOVE-21.dash_distance": {
    "start": 85,
    "unit": "units"
   },
   "MOVE-21.dash_duration_s": {
    "start": 0.16,
    "unit": "s"
   },
   "MOVE-21.dash_cooldown_s": {
    "start": 0.3,
    "unit": "s"
   },
   "MOVE-21.free_fall_dash_multiplier": {
    "start": 0.5,
    "unit": "x"
   },
   "MOVE-22.wind_acceleration": {
    "start": 3,
    "unit": "1/s"
   },
   "MOVE-22.wind_open_decay": {
    "start": 1.5,
    "unit": "1/s"
   },
   "MOVE-22.wind_falling_decay": {
    "start": 12,
    "unit": "1/s"
   },
   "SURV-05.min_lift": {
    "start": 0.3,
    "unit": "x"
   },
   "SURV-05.post_hit_protection_s": {
    "start": 0.65,
    "unit": "s"
   },
   "UMB-05.absorb_range": {
    "start": 240,
    "unit": "units"
   },
   "UMB-05.absorb_cone_deg": {
    "start": 60,
    "unit": "degrees"
   },
   "UMB-05.pull_speed": {
    "start": 700,
    "unit": "units/s"
   },
   "UMB-05.capture_distance": {
    "start": 24,
    "unit": "units"
   },
   "UMB-05.heal_per_yellow": {
    "start": 0.5,
    "unit": "health"
   },
   "UMB-05.heal_per_recovery_rank": {
    "start": 0.3,
    "unit": "health"
   },
   "COM-06.shots_per_s": {
    "start": 5,
    "unit": "1/s"
   },
   "COM-06.damage": {
    "start": 10,
    "unit": "damage"
   },
   "COM-06.speed": {
    "start": 700,
    "unit": "units/s"
   },
   "COM-06.range": {
    "start": 1500,
    "unit": "units"
   },
   "COM-07.ticks_per_s": {
    "start": 10,
    "unit": "1/s"
   },
   "COM-07.tick_damage": {
    "start": 4,
    "unit": "damage"
   },
   "COM-07.growth_speed": {
    "start": 1200,
    "unit": "units/s"
   },
   "COM-07.max_range": {
    "start": 1400,
    "unit": "units"
   },
   "COM-07.width": {
    "start": 14,
    "unit": "units"
   },
   "COM-08.separation": {
    "start": 44,
    "unit": "units"
   },
   "COM-08.volleys_per_s": {
    "start": 5,
    "unit": "1/s"
   },
   "COM-08.damage": {
    "start": 7,
    "unit": "damage"
   },
   "COM-08.speed": {
    "start": 700,
    "unit": "units/s"
   },
   "COM-08.range": {
    "start": 1500,
    "unit": "units"
   },
   "COM-09.shots_per_s": {
    "start": 3,
    "unit": "1/s"
   },
   "COM-09.damage": {
    "start": 14,
    "unit": "damage"
   },
   "COM-09.speed": {
    "start": 1000,
    "unit": "units/s"
   },
   "COM-09.range": {
    "start": 1700,
    "unit": "units"
   },
   "COM-09.size_multiplier": {
    "start": 0.7,
    "unit": "x"
   },
   "FLOW-05.hp_multiplier_cap": {
    "start": 2,
    "unit": "x"
   },
   "FLOW-05.hp_multiplier_step": {
    "start": 0.1,
    "unit": "x per completed run"
   },
   "FLOW-05.cadence_multiplier_cap": {
    "start": 1.3,
    "unit": "x"
   },
   "FLOW-05.cadence_multiplier_step": {
    "start": 0.03,
    "unit": "x per completed run"
   },
   "FLOW-05.count_multiplier_cap": {
    "start": 2,
    "unit": "x"
   },
   "FLOW-05.count_multiplier_step": {
    "start": 0.1,
    "unit": "x per completed run"
   },
   "FLOW-06.final_hour_hp_multiplier": {
    "start": 2,
    "unit": "x"
   },
   "FLOW-06.final_hour_cadence_multiplier": {
    "start": 1.35,
    "unit": "x"
   },
   "FLOW-06.final_hour_count_multiplier": {
    "start": 2,
    "unit": "x"
   },
   "FLOW-15.start_hits_per_life": {
    "start": 3,
    "unit": "hits"
   },
   "FLOW-15.start_lives": {
    "start": 3,
    "unit": "lives"
   },
   "FLOW-15.max_hits_per_life": {
    "start": 11,
    "unit": "hits"
   },
   "FLOW-15.max_lives": {
    "start": 11,
    "unit": "lives"
   },
   "FLOW-15.level_cap": {
    "start": 62,
    "unit": "level"
   },
   "FLOW-15.earned_points_at_cap": {
    "start": 61,
    "unit": "points"
   },
   "FLOW-15.xp_curve_base": {
    "start": 100,
    "unit": "XP"
   },
   "FLOW-15.cumulative_xp_level_10": {
    "start": 916,
    "unit": "XP"
   },
   "FLOW-15.cumulative_xp_level_20": {
    "start": 1981,
    "unit": "XP"
   },
   "FLOW-15.cumulative_xp_level_30": {
    "start": 3096,
    "unit": "XP"
   },
   "FLOW-15.cumulative_xp_level_62": {
    "start": 7000,
    "unit": "XP"
   },
   "FLOW-15.target_xp_per_run": {
    "start": 700,
    "unit": "XP"
   },
   "FLOW-15.target_completed_runs": {
    "start": 10,
    "unit": "runs"
   },
   "FLOW-16.unlock_level_streamed": {
    "start": 10,
    "unit": "level"
   },
   "FLOW-16.unlock_level_twin": {
    "start": 20,
    "unit": "level"
   },
   "FLOW-16.unlock_level_needle": {
    "start": 30,
    "unit": "level"
   },
   "FLOW-19.xp_roadwarden": {
    "start": 10,
    "unit": "XP"
   },
   "FLOW-19.xp_floodstrider": {
    "start": 20,
    "unit": "XP"
   },
   "FLOW-19.xp_courier": {
    "start": 10,
    "unit": "XP"
   },
   "FLOW-19.xp_wings": {
    "start": 60,
    "unit": "XP"
   },
   "FLOW-19.xp_front": {
    "start": 60,
    "unit": "XP"
   },
   "FLOW-19.xp_middle": {
    "start": 80,
    "unit": "XP"
   },
   "FLOW-19.xp_rear": {
    "start": 100,
    "unit": "XP"
   },
   "FLOW-19.xp_clock": {
    "start": 150,
    "unit": "XP"
   },
   "FLOW-24.chunk_length": {
    "start": 1920,
    "unit": "units"
   },
   "FLOW-33.projectile_damage": {
    "start": 1,
    "unit": "health"
   },
   "FLOW-33.trap_damage": {
    "start": 1,
    "unit": "health"
   },
   "FLOW-33.chain_damage": {
    "start": 1.25,
    "unit": "health"
   },
   "FLOW-33.talon_damage": {
    "start": 1.5,
    "unit": "health"
   },
   "FLOW-33.old_damage_divisor": {
    "start": 8,
    "unit": "x"
   },
   "OWL-08.wings_hp": {
    "start": 180,
    "unit": "HP"
   },
   "OWL-08.front_hp": {
    "start": 100,
    "unit": "HP"
   },
   "OWL-08.middle_hp": {
    "start": 110,
    "unit": "HP"
   },
   "OWL-08.rear_hp": {
    "start": 120,
    "unit": "HP"
   },
   "OWL-08.clock_hp": {
    "start": 320,
    "unit": "HP"
   },
   "OWL-08.clock_reserve_hp": {
    "start": 128,
    "unit": "HP"
   },
   "OWL-11.red_spacing_s": {
    "start": 0.09,
    "unit": "s"
   },
   "OWL-11.red_spread_wings_deg": {
    "start": 36,
    "unit": "degrees"
   },
   "OWL-11.red_spread_mechanisms_deg": {
    "start": 70,
    "unit": "degrees"
   },
   "OWL-11.red_spread_clock_deg": {
    "start": 48,
    "unit": "degrees"
   },
   "OWL-11.red_speed_wings": {
    "start": 240,
    "unit": "units/s"
   },
   "OWL-11.red_speed_mechanisms": {
    "start": 270,
    "unit": "units/s"
   },
   "OWL-11.red_speed_clock": {
    "start": 300,
    "unit": "units/s"
   },
   "OWL-11.red_interval_s": {
    "start": 1.35,
    "unit": "s"
   },
   "OWL-11.reduced_interval_s": {
    "start": 2.16,
    "unit": "s"
   },
   "OWL-13.yellow_speed_wings": {
    "start": 180,
    "unit": "units/s"
   },
   "OWL-13.yellow_speed_mechanisms": {
    "start": 195,
    "unit": "units/s"
   },
   "OWL-13.yellow_speed_clock": {
    "start": 210,
    "unit": "units/s"
   },
   "OWL-13.yellow_interval_s": {
    "start": 2.3,
    "unit": "s"
   },
   "OWL-13.yellow_size": {
    "start": 1.2,
    "unit": "x"
   },
   "OWL-15.physical_interval_s": {
    "start": 6.5,
    "unit": "s"
   },
   "OWL-15.gust_warning_s": {
    "start": 1.1,
    "unit": "s"
   },
   "OWL-16.gust_speed": {
    "start": 350,
    "unit": "units/s"
   },
   "OWL-16.gust_band_width": {
    "start": 120,
    "unit": "units"
   },
   "OWL-16.gust_lifetime_s": {
    "start": 3,
    "unit": "s"
   },
   "OWL-16.gust_push": {
    "start": 280,
    "unit": "units/s"
   },
   "OWL-18.talon_reach": {
    "start": 270,
    "unit": "units"
   },
   "OWL-18.talon_warning_s": {
    "start": 1.05,
    "unit": "s"
   },
   "OWL-19.talon_tip_width": {
    "start": 48,
    "unit": "units"
   },
   "OWL-19.talon_strike_s": {
    "start": 0.18,
    "unit": "s"
   },
   "OWL-20.talon_recovery_s": {
    "start": 1,
    "unit": "s"
   },
   "OWL-20.talon_cooldown_s": {
    "start": 3.5,
    "unit": "s"
   },
   "OWL-20.talon_rearm_exit": {
    "start": 370,
    "unit": "units"
   },
   "OWL-21.cast_warning_s": {
    "start": 0.9,
    "unit": "s"
   },
   "OWL-22.chain_reach": {
    "start": 800,
    "unit": "units"
   },
   "OWL-22.chain_speed": {
    "start": 400,
    "unit": "units/s"
   },
   "OWL-22.chain_head_width": {
    "start": 32,
    "unit": "units"
   },
   "OWL-23.chain_return_s": {
    "start": 1.2,
    "unit": "s"
   },
   "OWL-24.middle_offset": {
    "start": 80,
    "unit": "units"
   },
   "OWL-26.rear_pause_s": {
    "start": 0.65,
    "unit": "s"
   },
   "OWL-28.repeat_wait_s": {
    "start": 0.6,
    "unit": "s"
   },
   "OWL-28.repeat_recovery_s": {
    "start": 0.85,
    "unit": "s"
   },
   "OWL-29.clock_open_s": {
    "start": 1.8,
    "unit": "s"
   },
   "OWL-29.clock_protect_recovery_s": {
    "start": 1.3,
    "unit": "s"
   },
   "OWL-29.final_exposure_s": {
    "start": 1.9,
    "unit": "s"
   },
   "OWL-29.final_exposure_cycle_s": {
    "start": 4.8,
    "unit": "s"
   },
   "OWL-30.break_stun_s": {
    "start": 1.2,
    "unit": "s"
   },
   "OWL-30.fire_pause_s": {
    "start": 0.65,
    "unit": "s"
   },
   "OWL-31.slow_s": {
    "start": 3,
    "unit": "s"
   },
   "OWL-31.slow_world_scale": {
    "start": 0.35,
    "unit": "x"
   },
   "OWL-31.slow_cooldown_s": {
    "start": 3,
    "unit": "s"
   },
   "OWL-32.eye_window_s": {
    "start": 2,
    "unit": "s"
   },
   "OWL-32.eye_cooldown_s": {
    "start": 5,
    "unit": "s"
   },
   "OWL-32.blackout_s": {
    "start": 3,
    "unit": "s"
   },
   "OWL-35.departure_s": {
    "start": 2.5,
    "unit": "s"
   },
   "COM-14.roadwarden_hp": {
    "start": 40,
    "unit": "HP"
   },
   "COM-15.floodstrider_hp": {
    "start": 60,
    "unit": "HP"
   },
   "COM-16.courier_hp": {
    "start": 40,
    "unit": "HP"
   },
   "FLOW-37.slider_max": {
    "start": 100,
    "unit": "%"
   }
  },
  "fixtures": {
   "arena_cm": [
    1920,
    1080
   ],
   "note": "Pipeline prototype default (D-new-sh10-units), not a GDD number: the Keeper arena uses the 1920 x 1080 room size the GDD gives for its one-room prototype (HAZ-03); exact Keeper arena proportions are OPEN in GDD SH1.0 section 5."
  }
 }
}
```
