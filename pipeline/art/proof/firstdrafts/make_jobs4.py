"""jobs.json for assetgen batch: one flash draft per drawn slot with no candidate (firstdrafts lane, round 6). The shared style block is added by assetgen."""
import json, sys
KEY = ("The background is one perfectly flat, even, pure green #00FF00 from edge to edge, the shapes cut cleanly against it, "
 "and the shapes use no green. The canvas holds only the subject floating on the green, nothing else, no text. ")
ELLA = "Ella is an adult with dark brown hair, a hat, a cloth mask hiding her face, a scarf, boots, holding a black umbrella with light stripes with two hands. "
J = {
 "ella-shield": ("16:9", "Ella absorbing: four poses in a row, side view, braced with the umbrella canopy open in front of her like a shield, a gold glow gathering on the canopy. "+ELLA+KEY),
 "ella-attack": ("16:9", "Ella shooting: four poses in a row, side view, the umbrella held level like a lance, build, release, a gold pulse leaving the tip, recovery. "+ELLA+KEY),
 "scene-gameplay-frame": ("16:9", "A full gameplay frame for a 2D side-scroller: a dark lakeside town skyline in haze below, a clockwork owl hanging a mechanism high above, soft ash-blue sky, small gold lights, Ella small on the left rising with an umbrella. Fill the whole canvas edge to edge, no text, no border."),
 "vfx-blackout": ("21:9", "Blackout effect: four stages in a row, soft dark fog and ink-wash haze rolling in and swallowing the light, arched curls of smoke, low drifting fog. "+KEY),
 "vfx-blocked": ("21:9", "Blocked effect: four stages in a row, a gold pulse shot striking an umbrella canopy and stopping, a soft gold glow ring and small ivory sparks flaring and fading. "+KEY),
 "vfx-gold-fade": ("21:9", "Gold shot fade: four stages in a row, a gold #E9C46A pulse shot dimming, shrinking and dissolving into faint gold sparks. "+KEY),
 "vfx-gust": ("21:9", "Wind gust: four stages in a row, long pale curling wind ribbons sweeping horizontally, angular swirl lines, a damaging gust with a sharp front. "+KEY),
 "vfx-gust-puff": ("21:9", "Gust puff: four stages in a row, a small wing flap puff, soft pale ash-blue air puffs billowing outward from a point and thinning. "+KEY),
 "vfx-keeper-warning": ("21:9", "Keeper attack tell: four stages in a row, a thin crimson #FF3658 ring tightening around a point, then a short bright firing tell flash, angular. "+KEY),
 "vfx-light-shaft": ("21:9", "Light shaft: four stages in a row, a slanted soft gold and ivory shaft of light with faint dust motes, glowing from the umbrella and growing then fading. "+KEY),
 "vfx-needle-channel": ("21:9", "Needle spell channel: four stages in a row, a long straight level gold needle shaft charging, gold energy gathering along its length, glints. "+KEY),
 "vfx-needle-pierce": ("21:9", "Needle pierce: four stages in a row, a thin gold needle piercing through a target, a sharp flash at the hit and a thin gold trail. "+KEY),
 "vfx-needle-sliver": ("21:9", "Needle sliver: four stages in a row, small thin gold sliver shards splintering off and fading, angular faceted slivers. "+KEY),
 "vfx-part-break": ("21:9", "Mechanism part break: four stages in a row, a brass and iron gear cracking, shattering into gears, cogs and shards that fly apart and fall. "+KEY),
 "vfx-part-hit": ("21:9", "Mechanism part hit: four stages in a row, a quick impact flash on dark iron, ivory and gold sparks and a small shock ring. "+KEY),
 "vfx-slow": ("21:9", "Slow effect: four stages in a row, a pale clock face with one long hand ticking slowly, a curved reload arc, soft ash-blue ring. "+KEY),
 "vfx-stream-start": ("21:9", "Stream beam start: four stages in a row, a gold #E9C46A beam flaring up from a point, ivory strands and a bright core, angular spark edges. "+KEY),
 "vfx-stream-sustain": ("21:9", "Stream beam sustain: four loop frames in a row, a long steady horizontal gold #E9C46A beam with ivory interior strands and a bright core, faceted, spark edges. "+KEY),
 "vfx-stun": ("21:9", "Stun effect: four stages in a row, small gold stars and short zig-zag sparks circling a point, a dizzy halo that wobbles. "+KEY),
 "vfx-umbra": ("21:9", "Umbra effect: four stages in a row, a spreading pool of deep charcoal and ash-blue shadow with low fog curls and an arched wisp, soft ink-wash edges. "+KEY),
}
jobs=[]
for p,(asp,body) in J.items():
    prompt=("A "+{"16:9":"wide","21:9":"very wide 21:9","1:1":"square"}[asp]+" picture for a 2D game, piece "+p+". "+body)
    jobs.append(["--prompt",prompt,"--out",f"pipeline/art/proof/firstdrafts/{p}/draft1.png","--tier","draft","--aspect",asp,"--piece",p,"--provider","openrouter"])
json.dump(jobs,open(sys.argv[1],"w"),indent=1); print(len(jobs))
