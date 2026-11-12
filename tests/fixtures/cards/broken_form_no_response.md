### MVP item (number from docs/jam-brief.md), Day 0, or Stretch: <name>

9

### GDD ref (section + short quote)

Hazards: "spikes damage Ella"

### GDD revision (the one in docs/gdd/CURRENT, e.g. B1.0)

SH1.0

### Features (IDs from docs/feature-manifest.json)

HAZ-19

### Player outcome (the player sees X, does Y, can tell why; "none" for tooling cards)

Ella touches spikes, flashes, and loses one heart

### Owner role

Gameplay Dev

### Reviewer role (must differ from owner)

Dev Lead

### Human who runs and merges this

Rick

### Inputs and outputs (exact paths)

In: Source/UmbrellaElla/Public/Health/HealthComponent.h
Out: Source/UmbrellaElla/{Public,Private}/Hazard/Hazard.*

### Context (what the code or asset next to Outputs does today, with file:line)

new files only

### File lane, do-not-touch paths, binary files to lock

_No response_

### Out of scope (behaviors not to build; the reviewer rejects them)

No knockback, no new animation states

### Used by (BPs, maps, widgets or components that read what this card changes; follow-up card IDs)

BP_Spikes (Integrator card UE-040)

### Needs (build | tests | editor MCP | Windows packaging machine)

build, tests

### Done when (each line checkable)

- [ ] UmbrellaElla.Hazard.SpikesDamage passes: health drops by 1 on overlap
- [ ] Ella takes no second hit for 1.0 s after the first (invulnerability window)

### Budget and cut tier

60 min agent + 15 min human, MVP

### Unknowns (Decision needed / Why it matters / Proposed test / Choice; "none" if none)

none
