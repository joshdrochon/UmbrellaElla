"""Builds jobs.json for tools/assetgen.py batch: one flash first draft per piece with no image yet (firstdrafts lane)."""
import json, sys
STYLE = ("Style: a dark painterly etched storybook illustration, ink and wash with fine etched cross-hatching and a faint "
 "paper grain inside the shapes only. Large shapes have a clean near-black ink outline #171614 about 2 px wide at this size. "
 "One light source sits in front and slightly above: upper edges brighter, lower edges shaded with fine hatching. "
 "Palette: charcoal and ash-blue darks, muted sepia, bone ivory #FFF5DC, warm gold #E9C46A, bronze #94611E, with only tiny accents of crimson #FF3658. Seed variation 3: a fresh composition. ")
SPRITE_OLD = ("The background is one perfectly flat, even, pure green #00FF00 from edge to edge, the shapes cut cleanly against it, "
 "and the shapes use no green. The canvas holds only the subject floating on the green, nothing else, no text. ")
SPRITE = SPRITE_OLD
SCENE = "Fill the whole canvas edge to edge, no characters, no text, no border. "
UI = ("A dark game menu screen in the same etched look as a clockwork title screen: charcoal and muted sepia ground, gold line work, "
 "etched clock faces and gears as ornament, hand-lettered engraved headings. Fill the whole canvas, no border. ")
KEEPER = ("The Keeper is a crownless fabricated metal owl in side profile: rigid perforated vane wings, exactly two feet, "
 "a chest clock with one long hand, three distinct mechanisms hanging on their own chains (front armillary, middle cage, rear gear), "
 "dark iron, bronze and brass with warm amber eyes. ")
J = {
 "bg-base": ("16:9", SCENE+"A quiet sky backdrop layer for a 2D side-scroller: soft ash-blue to charcoal sky, faint painterly cloud wash, "
   "a few small gold lights, nothing in the foreground, no horizon objects. Muted, dark, calm."),
 "bg-atmosphere": ("16:9", "A cloud bank, a trailing mist, a curl of haze and underside mist, drawn as soft ink-wash layers on a flat green background, a 2D game atmosphere layer. "+SPRITE),
 "bg-start-end": ("16:9", SCENE+"The start and end screen background: dark charcoal and muted sepia, faint blue, small gold lights drifting slowly, distant etched clockwork silhouettes in haze. No characters."),
 "ella-condition": ("16:9", "Ella shown as six small full-body figures in a row, a condition scale from whole to faded: Ella is an adult in a hat with dark brown hair, "
   "a cloth mask hiding her face, a scarf, boots, holding an umbrella with two hands. Left to right: complete; boots faded; boots and hat faded; "
   "only mask and scarf remain solid; a thin flickering outline in a critical state; a faint ghost. Side view. "+SPRITE),
 "ella-motion": ("16:9", "Ella in four movement poses in a row, side view, airborne: an overhead hop, a forward falling cartwheel, a back falling cartwheel, a free-fall dash. "
   "Ella is an adult with dark brown hair, a hat, a cloth mask hiding her face, a scarf, holding a black umbrella with light stripes with two hands. "+SPRITE),
 "enemy-floodstrider": ("1:1", "The Floodstrider: a tall stilt-legged clockwork enemy figure in side view, a hunched cloaked walker on two long wading stilts with a dripping hem, "
   "a brass lantern, and a small caster arm raised to fire a pointed red projectile. "+SPRITE),
 "keeper-clock": ("1:1", "The chest clock of a metal owl, front view of the clock only: a brass-rimmed glass face with one long hand, cracks across the glass, hinged cover plates half open. "+SPRITE),
 "keeper-damage": ("16:9", "Six panels of one hanging clockwork mechanism of a metal owl, shown on six sprites in a row from intact to broken: "
   "all seven parts, then fewer, then half, then none, then a break with shards flying, then a stunned wobble. Dark iron and bronze. "+SPRITE),
 "keeper-departure": ("16:9", KEEPER+"The Keeper leaves alive, not defeated: it spreads its vane wings and rises away upward, drifting off with a calm, still-intact body, side view, shown as three poses in a row. "+SPRITE),
 "keeper-mech-front": ("1:1", "The Keeper's front mechanism: a brass armillary of rings hung on its own chain, a mechanical arm that grasps and throws, side view. "+SPRITE),
 "keeper-mech-middle": ("1:1", "The Keeper's middle mechanism: a hanging iron cage with a curved casting arm, on its own chain, side view. "+SPRITE),
 "keeper-mech-rear": ("1:1", "The Keeper's rear mechanism: a big hanging toothed gear on its own chain with a striking arm, side view. "+SPRITE),
 "keeper-talon": ("16:9", "A metal owl's talon in side view in two poses: an open raking claw, and a closed gripping fist. Dark iron with bronze joints and fine cross-hatching. "+SPRITE),
 "keeper-wing": ("16:9", KEEPER+"Only the wings, in four poses in a row: gathered, mid-flap, spread front, recovery. Rigid perforated vane wings, one worn with a missing vane. "+SPRITE),
 "menu-screen": ("16:9", UI+"A pause screen: a centered engraved panel with a ring of gold clock gears, three menu rows."),
 "stream-beam": ("21:9", "Ella's Streamed Blast: a long horizontal gold #E9C46A beam with ivory #FFF5DC interior strands and a bright core, seen as three stages in a row: start-up flare, the sustained beam, the stop fade. Angular, faceted, spark edges. "+SPRITE),
 "ui-journey-complete": ("16:9", UI+"The Journey Complete screen: a large engraved heading, eight stat rows with gold numbers, two buttons Try Again and Main Menu."),
 "ui-level-up": ("16:9", UI+"The level-up screen: a big engraved level number as the heading and a short list of menu items below."),
 "ui-purchase": ("16:9", UI+"The Ella and Spells purchase screen: level and points at the top, rows with a minus and a plus button each, buttons Confirm, Cancel and Done."),
 "ui-spell-wheel": ("1:1", "A spell wheel: a circular etched ring with four spell slots shown as locked, available and equipped, lettered and engraved like clock work, gold line work on dark charcoal, a still ring of gears. Fill the canvas, no border."),
 "ui-xp-ring": ("1:1", "A game HUD clock face with a thin glowing gold ring around it as an experience ring, etched clock numerals, one long hand, gold line work on dark charcoal. "+SPRITE),
 "vfx-clock-open": ("21:9", "The Keeper's chest clock opening: four stages in a row, cover plates sliding apart, glass catching light, hands visible. Brass and gold, flat side view. "+SPRITE),
 "vfx-departure": ("21:9", "The Keeper's departure effect: four stages in a row, soft gold sparks and curling pale wind lifting upward and fading. "+SPRITE),
 "vfx-eye-exposed": ("21:9", "An exposed amber eye of a metal owl: four stages in a row, a glowing amber #FFC76A eye with a vertical slit, a ring flare and tiny sparks. "+SPRITE),
 "vfx-keeper-recovery": ("21:9", "The Keeper's recovery cue: four stages in a row, cool pale blue mist and small gears settling, a steady faint ring. "+SPRITE),
 "vfx-keeper-strike": ("21:9", "The Keeper's strike effect: four stages in a row, a curved crimson #FF3658 slash with coral #FF7848 edge and pale core, angular shards. "+SPRITE),
 "vfx-restoration": ("21:9", "The restoration after blackout: four stages in a row, warm gold light blooming from a point and spreading as a soft ring, small sparks. "+SPRITE),
 "yellow-shot": ("1:1", "The yellow shot: a pointed angular projectile in side view, one sharp faceted blade, yellow #FFD84A and amber #F5AA28 with deep #94611E shadow, a pale core #FFF5DC, a short trail. "+SPRITE),
}
jobs=[]
for p,(asp,body) in J.items():
    prompt=("A "+{"16:9":"wide","21:9":"very wide 21:9","1:1":"square"}[asp]+" picture for a 2D game, piece "+p+". "+body+" "+STYLE)
    jobs.append(["--prompt",prompt,"--out",f"pipeline/art/proof/firstdrafts/{p}/draft3.png","--tier","draft","--aspect",asp,"--piece",p])
if len(sys.argv)>2 and sys.argv[2]=="final":
    for j in jobs:
        p=j[j.index("--piece")+1]
        j[j.index("--out")+1]=f"pipeline/art/proof/firstdrafts/{p}/final2.png"
        j[j.index("--tier")+1]="final"
        j+=["--image-size","2K","--from-draft",f"pipeline/art/proof/firstdrafts/{p}/draft3.png"]
json.dump(jobs,open(sys.argv[1],"w"),indent=1)
print(len(jobs))
