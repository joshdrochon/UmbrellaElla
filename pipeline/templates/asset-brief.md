# Asset brief (add to every Asset Specialist card) and asset handoff (end of every asset PR)

A fresh session must be able to make the asset from the card alone. Every reference is a repo path.
"The image we discussed" is not a reference. A brief with an empty field is not ready.

## Brief (in the card's Inputs)
```
Purpose:          <what the player must read from it, e.g. "umbrella is open, Ella will rise">
Anchors:          <repo paths of approved frames or the key art; traits to keep from each>
States / frames:  <exact list, e.g. idle-float 4, fall 3, open 3, close 3>
                  <for each flipbook: C++ state it shows, trigger, loop or one-shot, what interrupts it>
Size and pivot:   <the art-bible asset-spec row>
Sheet grid:       cell <W>x<H>, margin <px>, spacing <px> (goes into the .sprite.json sidecar)
Sockets:          <name, position in the sprite, same on every frame (`--import-report` fails a move over 2 px within one anim); e.g. Muzzle at the umbrella tip; or "none">
Motion pass:      _PH silhouette flipbook in L_Graybox, clip <link>, frame count confirmed by the Game Designer
Draw layer:       <the art-bible draw-order slot>
Tool:             <tool + plan, e.g. "image model X, free tier">; paid credits or sign-ups only by a named human with a `Spend OK:` link (agent-ops.md)
Banned:           cutting from the key art, prompts naming living artists or others' IP, pixel-art look, white or flat background
Paths:            Art/Source/<Asset>/** and Content/UmbrellaElla/Art/<Asset>/**
Gates:            art-director.md gates + pipeline/checklists/animation-review.md if animated
Generation budget: <max generations per state, e.g. 6>
Stop if:          budget used, or 3 review rounds in a row with the same gap and no better score (D-new-no-round-cap)
Receiving card:   <Integrator card ID that places it>
```
VFX briefs also state purpose, duration and draw layer. No full-screen flash.

## Handoff (last section of the asset PR)
```
Assets:      <T_/SPR_/FB_ paths>
State map:   <FB_ asset → C++ state>
Pivot:       <per sprite>
Sockets:     <name and position per sprite, or none>
Checks:      sprite_check --scan, --names, --import-report output (errors=0)
Collision:   sprite collision None (gameplay collision is on the actor)
Generations used: <n of budget>
Known limits: <or "none">
Next:        <Integrator card ID>
```
