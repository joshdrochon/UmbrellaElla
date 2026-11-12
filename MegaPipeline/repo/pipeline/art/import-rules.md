# Unreal import rules for art (on demand: Asset Specialist, Art Director, Technical Director)

Load this for any card that imports or changes a texture, sprite or flipbook, and at each gate.
The rules are data in `pipeline/art/style.json` (`unreal_import`, `anims`, `naming`) and are checked by
`tools/sprite_check.py`. Status: **proposed**. No engine was installed when they were written, so every
Unreal property, enum and ini key name below is [VERIFY] until card 0.4a reads it from 5.8.4.

## 1. Project defaults (Config), set once in card 0.3
`python3 tools/sprite_check.py --config Config` must print PASS. It reads:

| File | Section | Key | Rule |
|---|---|---|---|
| DefaultEditor.ini | `[/Script/Paper2DEditor.PaperImporterSettings]` | `DefaultSpriteTextureGroup` | set, not `TEXTUREGROUP_Pixels2D`; equals `unreal_import.texture.lod_group` once D-new-art-texgroup sets it (proposed `TEXTUREGROUP_UI`) |
| | | `bOverrideTextureCompression` | `True` |
| | | `DefaultSpriteTextureCompression` | `TC_EditorIcon` (UserInterface2D) |
| | | `UnlitDefaultMaskedMaterialName` | `/Paper2D/MaskedUnlitSpriteMaterial.MaskedUnlitSpriteMaterial` |
| | | `UnlitDefaultTranslucentMaterialName` | `/Paper2D/TranslucentUnlitSpriteMaterial.TranslucentUnlitSpriteMaterial` |
| | | `bPickBestMaterialWhenCreatingSprites` | set. True or False is open (decision row requested: D-new-art-pickbest, proposed False). The check moves to `equals` once decided |
| | | `DefaultPixelsPerUnrealUnit` | set; equals `unreal_import.pixels_per_unit` once card 0.10 fills it (D-new-port-10) |
| DefaultEngine.ini | `[/Script/Paper2D.PaperRuntimeSettings]` | `bResizeSpriteDataToMatchTextures` | `True` (a D13 2×→1× switch keeps pivots and collision) |
| | | `bEnableSpriteAtlasGroups` | `False` (experimental) |

All key names [VERIFY on 5.8.4]. A missing `Config/` prints SKIP until card 0.3 merges; after that CI runs it with `--require-dir`
(CI step requested from the TD; until it lands, card 0.3's PR pastes `--config Config --require-dir` PASS).
`python3 tools/sprite_check.py --uproject UmbrellaElla.uproject` must print PASS: Plugins lists `{"Name": "Paper2D", "Enabled": true}` and no `PaperZD`.

## 2. Per-asset rules (editor dump)
`python3 tools/sprite_check.py --import-report Saved/ArtDump.json` prints one error per broken rule per asset.
The dump is made inside the editor by `tools/ue/art_dump.py` over `/Game/UmbrellaElla/Art`. The script does not exist yet.
Card 0.4d (owner Technical Director agent, gate patch applied by the TD human; after 0.4a and 0.10b, before 0.10) writes it [VERIFY the 5.8.4
`-run=pythonscript` / commandlet name]. Its output is an envelope; a hand dump is the bare `assets` list:

```
{"tool": "tools/ue/art_dump.py", "root": "/Game/UmbrellaElla/Art", "assets": [ ...one object per asset... ]}
{"class": "Texture2D",  "name", "filter", "srgb", "compression", "never_stream", "lod_group", "mip_gen", "width", "height",
 "sheet": {"grid": [w, h], "margin", "spacing"} (copied from the source PNG's .sprite.json sidecar)}
{"class": "PaperSprite","name", "kind" (optional, from the sheet sidecar), "material", "collision", "atlas_group", "pivot_mode",
 "pivot", "render_geometry", "width", "height", "sockets": [{"name", "location": [x, y]}], "pixels_per_unit",
 "texture" (source texture name), "source_uv": [x, y], "source_size": [w, h]}
{"class": "PaperFlipbook","name", "fps", "keyframes": [{"sprite": "SPR_<Asset>_<Anim>_NN", "frame_run": 1}, ...]}
```
Source properties [VERIFY]: `Filter`, `SRGB`, `CompressionSettings`, `NeverStream`, `LODGroup`, `MipGenSettings`;
`DefaultMaterial`, `SpriteCollisionDomain`, `AtlasGroup`, `PivotMode`, `CustomPivotPoint`, render geometry mode, `Sockets` (each `SocketName` and `LocalTransform` X, Z),
`PixelsPerUnrealUnit`, `SourceTexture`, `SourceUV`, `SourceDimension`; `FramesPerSecond`, `KeyFrames` (each `Sprite` and `FrameRun`).
The sidecar is found from the texture's source file path (`AssetImportData`) [VERIFY].
The format contract is `tests/fixtures/art_dump/anchors.json` (the 5 anchors). It must print errors=0; the same file with one
texture set to `TF_Nearest` must print errors=1 (`tests/test_sprite_check.py`). The dump script's own test should reuse it.
An empty dump or an unknown class is an error, so a dump that found nothing never passes.

| Rule | Error when |
|---|---|
| filter | Filter is `TF_Nearest` |
| srgb | sRGB off |
| compression | not `TC_EditorIcon` (UserInterface2D) |
| stream | NeverStream off |
| texture_group | `TEXTUREGROUP_Pixels2D` (unfiltered group); once `unreal_import.texture.lod_group` is set, any other group (World has mips and LOD bias) |
| mips | per D13 (`unreal_import.texture.mips`: null until decided; `mips` needs mips and power-of-two, `none` needs no mips) |
| material | by kind: silhouette and tile need the unlit masked material; only fx may use unlit translucent. Kind = dump `kind`, else `kind_prefixes` (`SPR_FX*` fx, `SPR_Paper*`/`SPR_Rock*` tile), else silhouette |
| collision | sprite collision not None |
| atlas | any atlas group set |
| pivot | mode differs from `required_pivot` for the asset prefix (Ella, Spikes Bottom_Center; Shot, Cross, Flyer Center_Center; Rock Bottom_Left), or not in the allowed list; or sprites of one `SPR_<Asset>_` differ in pivot across any of its anims |
| ppu | sprites differ in `pixels_per_unit`, or differ from `unreal_import.pixels_per_unit` once set |
| geometry | sprite over 256 px using Full Rect (`SourceBoundingBox`) render geometry (overdraw) |
| socket | `SPR_Ella_*` without a `Muzzle` socket (name proposed); a socket with no `location`; one socket moving more than `socket_drift_max_px` (2) in x or y across the frames of one `SPR_<Asset>_<Anim>` set |
| fps / frames | `FB_<Asset>_<Anim>` FramesPerSecond outside the `anims` row; unique keyframe sprites outside its frame range; a keyframe that is not `SPR_<Asset>_<Anim>_NN`; `_NN` not ascending (unless the row says `"order": "any"`); the same sprite twice in a row (use `frame_run`); more than 60 unique sprites over all flipbooks (jam cap) |
| grid | a `SPR_<Asset>_<Anim>_NN` frame whose `source_uv` or `source_size` is not cell NN of its texture's `sheet` grid (cells counted left to right, then top to bottom, after margin and spacing), or whose texture has no `sheet` [VERIFY that Grid-mode Extract Sprites keeps the full cell and numbers every cell, empty ones too] |
| dump | empty dump, or a class other than the three above |
| gate (only with `--gate`) | not the `art_dump.py` envelope with root `/Game/UmbrellaElla/Art`; `unreal_import.status` not `verified`; `unreal_import.texture.mips` null (D13 open); `unreal_import.texture.lod_group` null (D-new-art-texgroup open); a frame whose texture is missing from the dump |

Done when (each gate): `python3 tools/sprite_check.py --import-report Saved/ArtDump.json --gate` on the script's dump of all of
`Content/UmbrellaElla/Art` prints PASS errors=0, pasted in the gate record. So a gate cannot pass before 0.4a (names), 0.4d
(script) and D13 (mips). D13 cutoff and its default are requested in `docs/decisions.md` (proposed: before card 0.10, default `none`).

### Card 0.4d done-when (the card row is in `pipeline/day0-cards.md`)
Owner Technical Director agent; kickoff applies its gate patch (`tools/git_gate.py apply --auto`). Lane: `tools/ue/art_dump.py`, `pipeline/art/style.json`, `pipeline/art/import-rules.md`. After 0.4a and 0.10b, before 0.10.
- `tools/ue/art_dump.py` runs headless on `/Game/UmbrellaElla/Art` and writes the envelope above to `Saved/ArtDump.json`.
- On the 5 anchors, `--import-report` prints errors=0, the same as `tests/fixtures/art_dump/anchors.json`.
- With one anchor texture set to `TF_Nearest` in the editor, it prints errors=1 (`filter`). Both outputs pasted.
- With one `SPR_Ella_Open_NN` Muzzle socket moved 4 px, it prints errors=1 (`socket`): the dump writes each socket's `location`.
- Its own test loads `tests/fixtures/art_dump/anchors.json` as the format contract.
- Every property, enum, ini key and texture group name in this file and in `style.json` is read from 5.8.4 and pasted
  on the card. `grep -c VERIFY pipeline/art/import-rules.md` prints 0, and `style.json unreal_import.status` is `verified`.
- Naming Template: Extract Sprites, Grid mode, on one anchor sheet, with `SPR_<Asset>_<Anim>_{0}`. The card pastes the
  names it made. If they are not 2-digit (`_0` instead of `_00`), the card adds the rename step (section 3 fallback),
  runs it on that sheet, and pastes `--names` PASS.
- The texture group the dump reports for the anchors is pasted, so D-new-art-texgroup can set `lod_group`.
The rule logic is tested in `tests/test_sprite_check.py` with a fixture that breaks each rule once.

### Until `art_dump.py` exists: hand dump (Technical Director)
The rules do not change. The TD writes the dump by hand instead of the script, then runs the same command.
1. In the editor, open each new or changed `T_`, `SPR_`, `FB_` asset in the card. Copy each field in the schema above from its
   Details panel into `Saved/ArtDump.json` (not committed). Flipbooks: list every keyframe's sprite and frame run, in order.
2. Run `python3 tools/sprite_check.py --import-report Saved/ArtDump.json`.
3. Paste in the PR: the PASS line with errors=0, the asset count in the dump, and the line `hand dump by <TD name>`.
Done when: errors=0 is pasted, and the dump's asset count equals the number of `.uasset` files the PR adds or changes under
`Content/UmbrellaElla/Art` (`git diff --name-only origin/main | grep -c 'Content/UmbrellaElla/Art/.*\.uasset'`).
A hand dump never covers a gate. Gates need the script's dump of the whole folder; `--gate` fails a bare list.

## 3. Names
`python3 tools/sprite_check.py --names Content/UmbrellaElla/Art` checks every `.uasset` name:
`^(T|SPR|FB)_<Asset>_<State or Anim>(_NN)?(_PH)?$`, no `_v2`, `_final`, `_new`.
Frames: `SPR_<Asset>_<Anim>_<NN>`, 2 digits from 00. Extract with Extract Sprites, Grid mode, Naming Template
`SPR_<Asset>_<Anim>_{0}` [VERIFY the token and zero-padding on 5.8.4], using the sheet's cell, margin and spacing from its sidecar.
Fallback if 5.8.4 cannot pad (card 0.4d finds out): after extracting, rename each `_N` frame to `_0N` in the editor
(Python `unreal.EditorAssetLibrary.rename_asset`, run from the Output Log [VERIFY]), never with file tools.
`--names` flags an unpadded frame and points here. Done when: `--names` prints PASS on the sheet's folder.

## 4. Umbrella width
`python3 tools/sprite_check.py --width-ratio <open sheet.png> <closed sheet.png>` must print PASS: the narrowest open frame's
opaque box is at least `sprite.umbrella_width_ratio_min` (1.8) times the widest closed frame's. Grid comes from each sheet's sidecar.

## 5. Engine colour (swatch)
`python3 tools/make_art_calibration.py --swatch <path>` writes the palette swatch. Placed under `CAM_Eval_Swatch`, its
capture must pass `python3 tools/art_check.py --swatch <capture>` (every cell ΔE76 ≤ 3). Set `style.json swatch.rect`
to where the swatch lands in the capture. Re-run on any trigger in `art-director.md` step 10.

## 6. Optional 3D source by Blender script (Art Director choice; off by default)
Only when the Art Director picks a 3D source for a prop or background, on the card. Otherwise this path does not exist.
- The model is a Python script that Blender runs headless (`blender -b -P <script>.py`). Never hand-edit the mesh:
  fix the one script line and re-run it.
- Simple shapes only (primitives, extrusions, bevels). No realistic meshes.
- The script renders a sprite. The sprite goes through the normal gates: `sprite_check.py` on the sheet and
  `art_check.py` on the in-engine capture. The colour bible (`pipeline/art/art-bible.md`, `style.json`) applies to
  every output, as it does for drawn sprites.
- `pipeline/art/provenance.csv` records the script as the source: `tool` = Blender, `origin` = the script path.
- A downloaded model needs a CC licence in its provenance row, and a script decimates it to low-poly before render.
Source: R12 in `docs/references.md`.
