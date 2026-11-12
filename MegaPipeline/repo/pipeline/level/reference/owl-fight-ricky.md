# Reference: Ricky's owl fight (proposed encounter preset OWL-FIGHT-RICKY)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


Source: Ricky in the team Discord, #owl-fight-mechanics, 10 Nov 2026 19:28 PST. He describes the rebuilt fight as it
plays now (build WIN015), reviewed by an encounter specialist without starting the game. The team's goal from the
meeting notes: bring the pipeline build closer to the demonstrated fight.

This file is the reference the encounter critic judges against (`python3 tools/encounter_check.py --critic-packet
OWL-FIGHT-RICKY/<phase>`). It is not the GDD. GDD 1.3 stays the baseline and the default preset. Whether this fight
replaces it is decision row `D-new-encounter-ricky` (owner Richard). The data is preset `OWL-FIGHT-RICKY` in
`pipeline/level/encounter.json`; numbers it lists under `numbers_from_reference` come from this description, every
other number there is a pipeline proposal.

## The goal
- Ella fights through the Keeper's wings, three hanging mechanisms, then the clock.
- Shooting, absorbing and regaining altitude compete: shooting and absorbing make Ella fall.
- Damage reduces both umbrella health and upward lift.

## Phase 1: wings
- Two reachable wing regions share 180 HP. Breaking them stops the damaging wind gusts. The damaged wings stay attached.
- Gust: warns an altitude band, then pushes left and deals damage. Counter: move out of the warned band.
- Absorbing does not cancel the gust. A protected dash avoids the damage but not the push.

## Phase 2: hanging mechanisms
- After the wings, the mechanisms become targets in order: front 100 HP, middle 110 HP, rear 120 HP.
- Each can be shot while its head moves. Breaking one cancels its attack and makes the next one available.
- Front: warns, then throws straight at where Ella was targeted. Counter: move off the line.
- Middle: follows a high or a low curve. Counter: clear the whole curve, not only the straight path.
- Rear: moves halfway, pauses (safe), then continues to its original target. Counter: it is not done when it pauses.
- Only the outward-moving head hurts. The chain and the return are harmless.

## Phase 3: the clock
- After wings and mechanisms, shoot the clock during its openings. 320 max HP.
- Outer-part hits can expose it earlier, so it can be chipped, but it keeps at least 40% for the final phase.
  Earlier damage carries forward.
- The final clock opens on its own cycle. Its double beat fires a red group, then repeats the same paths without
  re-aiming. Counter: move away from the first pattern and do not drift back into it.
- The clock at zero completes the fight. Story: the Keeper leaves alive.

## Throughout the fight
- Red shots: four-shot volleys, faster as the fight goes on. They hurt and cannot normally be absorbed.
- Yellow shots: two-shot packets. Contact hurts, but catching them on purpose repairs the umbrella and charges Stored
  Thunder, also after the catch-XP limit.
- Talon rake: when Ella gets close the claw warns and commits to a quick strike. Counter: bait it, then move away or
  change altitude. It re-arms only after Ella leaves the area and comes back.
- Breaking a mechanism briefly stuns the Keeper and exposes the clock. New attacks stop; shots already flying still hurt.
- A clock hit can briefly slow the world. An optional eye can appear: hitting it blacks out and clears old threats,
  but does not extend the clock's vulnerability.

## Testing notes from the same post
- A normal full run starts with the wings. The saved Boss Practice setup starts at phase 3 and skips wings and
  mechanisms, and practice uses different movement and protection settings, so it can feel different.
- Several attack visuals (the finished talon and grasp/throw animations) are still placeholders.
- Automated behaviour does not show that the fight is fair or fun: a human playtest decides that.
