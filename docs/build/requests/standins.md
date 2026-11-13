# Request: standins (art_inventory.py)

`tools/build/art_inventory.py` fails every imported `_PH` texture except the Ella idle: a `Content/.../Art/<Folder>/T_X_PH.uasset`
that no FILE_RULES line maps becomes `file:<path>` with piece None, so `lane_precheck` and the gate say "has no art-loop piece".
The stand-ins lane imports 60 slots, so it needs a general rule, not one line per texture.

Diff (in `discover()`, replace the `else:` branch that does `put("file:" + rel, rel, None)`):

```python
        else:
            m = re.match(r"^Content/[^/]+/Art/(\w+)/(T_\w+?)(?:_PH)?\.uasset$", rel)
            slot = "/Game/UmbrellaElla/Art/%s/%s" % (m.group(1), m.group(2)) if m else None
            hit = [v for v in rows if art_slots.slot_path(v) == slot] if slot else []
            if hit:
                put(hit[0], rel, rows[hit[0]][1])   # the texture is that visual's slot: same piece
            else:
                put("file:" + rel, rel, None)
```
(`discover()` must run the Source/enum visuals first, as it does today, so `rows` already holds them.)
Some slots serve several visuals (one texture for both genders, GoldRelease/GoldTravel); the first match is enough.

Also: the candidate copies live in `pipeline/art/proof/standins/<piece>/`, not `Art/Source/StandIns/`, because every file under `Art/` is an inventory visual and a sprite_check sidecar case.
