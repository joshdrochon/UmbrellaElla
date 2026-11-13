"""Import the UI art as textures (rebuildable). Sources: Art/Source/UI/Ground/*.png (build_ground.py).
Run: UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=Art/Source/UI/import_ui_art.py -unattended -nullrhi -nosplash -nocrashreports
Destination /Game/UmbrellaElla/UI. `_PH`: tracked placeholders until the art loop passes them (docs/build/worker-rules.md)."""
import os
import unreal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEST = "/Game/UmbrellaElla/UI"
NAMES = ["T_UI_Ground_PH", "T_UI_ClockFace_PH"]

tasks = []
for name in NAMES:
    src = os.path.join(ROOT, "Art", "Source", "UI", "Ground", name + ".png")
    if not os.path.isfile(src):
        unreal.log_warning("import_ui_art: missing %s" % src)
        continue
    t = unreal.AssetImportTask()
    t.filename = src
    t.destination_path = DEST
    t.destination_name = name
    t.replace_existing = True
    t.automated = True
    t.save = True
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for name in NAMES:
    tex = unreal.EditorAssetLibrary.load_asset("%s/%s" % (DEST, name))
    if not tex:
        continue
    # UI art: no mips, no block compression (the grain must survive), never streamed.
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("never_stream", True)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
unreal.log("import_ui_art done: %d textures" % len(tasks))
