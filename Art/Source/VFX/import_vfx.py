"""Import the VFX sheets and build the two VFX materials (rebuildable; art lane artfx).
Run (through tools/build/ue_slot.sh):
  UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=Art/Source/VFX/import_vfx.py -unattended -nullrhi -nosplash -nocrashreports
Textures: Art/Source/VFX/Raw/<Sheet>_PH.png -> /Game/UmbrellaElla/Art/VFX/T_<Sheet>_PH (tracked placeholders until the art loop
passes them). Materials: M_VFX_Sheet_PH (unlit translucent, one row of frames stepped by the Frame parameter) and
M_VFX_Spill_PH (unlit additive soft disc: the light an effect spills on what is behind it). Names match
Source/UmbrellaElla/Private/Feedback/Vfx/VfxSheetVisual.cpp and VfxCatalog.cpp.
"""
import glob
import os

import unreal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "Art", "Source", "VFX", "Raw")
DEST = "/Game/UmbrellaElla/Art/VFX"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary

tasks = []
for png in sorted(glob.glob(os.path.join(SRC, "VFX_*_PH.png"))):
    task = unreal.AssetImportTask()
    task.filename = png
    task.destination_path = DEST
    task.destination_name = "T_" + os.path.splitext(os.path.basename(png))[0]
    task.automated = True
    task.replace_existing = True
    task.save = True
    tasks.append(task)
tools.import_asset_tasks(tasks)

first = None
for task in tasks:
    path = "%s/%s" % (DEST, task.destination_name)
    tex = eal.load_asset(path)
    if not tex:
        unreal.log_error("VFX_IMPORT missing %s" % path)
        continue
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    eal.save_asset(path)
    first = first or tex
    unreal.log("VFX_IMPORT texture %s %dx%d" % (path, tex.blueprint_get_size_x(), tex.blueprint_get_size_y()))


def fresh_material(name, blend):
    path = "%s/%s" % (DEST, name)
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    mat = tools.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("blend_mode", blend)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    return mat, path


def link(a, a_out, b, b_in):
    if not mel.connect_material_expressions(a, a_out, b, b_in):
        raise RuntimeError("VFX_IMPORT could not connect %s.%s -> %s.%s" % (a.get_name(), a_out, b.get_name(), b_in))


def link_out(a, a_out, prop):
    if not mel.connect_material_property(a, a_out, prop):
        raise RuntimeError("VFX_IMPORT could not connect %s.%s -> %s" % (a.get_name(), a_out, prop))


def node(mat, cls, x, y):
    return mel.create_material_expression(mat, cls, x, y)


def scalar(mat, name, value, x, y):
    p = node(mat, unreal.MaterialExpressionScalarParameter, x, y)
    p.set_editor_property("parameter_name", name)
    p.set_editor_property("default_value", value)
    return p


# --- M_VFX_Sheet_PH: UV = ((U + Frame) / Cols, V); emissive = sheet RGB; opacity = sheet A * Opacity.
mat, path = fresh_material("M_VFX_Sheet_PH", unreal.BlendMode.BLEND_TRANSLUCENT)
uv = node(mat, unreal.MaterialExpressionTextureCoordinate, -1200, 0)
mask_u = node(mat, unreal.MaterialExpressionComponentMask, -1000, -60)
mask_u.set_editor_property("r", True)
mask_u.set_editor_property("g", False)
mask_v = node(mat, unreal.MaterialExpressionComponentMask, -1000, 80)
mask_v.set_editor_property("r", False)
mask_v.set_editor_property("g", True)
frame = scalar(mat, "Frame", 0.0, -1000, -200)
cols = scalar(mat, "Cols", 8.0, -800, -200)
opacity = scalar(mat, "Opacity", 1.0, -400, 300)
add = node(mat, unreal.MaterialExpressionAdd, -800, -60)
div = node(mat, unreal.MaterialExpressionDivide, -650, -60)
app = node(mat, unreal.MaterialExpressionAppendVector, -500, 0)
sheet = node(mat, unreal.MaterialExpressionTextureSampleParameter2D, -350, 0)
sheet.set_editor_property("parameter_name", "Sheet")
if first:
    sheet.set_editor_property("texture", first)
mul = node(mat, unreal.MaterialExpressionMultiply, -100, 200)
link(uv, "", mask_u, "")
link(uv, "", mask_v, "")
link(mask_u, "", add, "A")
link(frame, "", add, "B")
link(add, "", div, "A")
link(cols, "", div, "B")
link(div, "", app, "A")
link(mask_v, "", app, "B")
link(app, "", sheet, "UVs")
link(sheet, "A", mul, "A")
link(opacity, "", mul, "B")
link_out(sheet, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
link_out(mul, "", unreal.MaterialProperty.MP_OPACITY)
mel.recompile_material(mat)
eal.save_asset(path)
unreal.log("VFX_IMPORT material %s" % path)

# --- M_VFX_Spill_PH: emissive = Tint * Opacity * saturate(1 - 2 * |UV - 0.5|)^2, additive.
mat, path = fresh_material("M_VFX_Spill_PH", unreal.BlendMode.BLEND_ADDITIVE)
uv = node(mat, unreal.MaterialExpressionTextureCoordinate, -1200, 0)
centre = node(mat, unreal.MaterialExpressionConstant2Vector, -1200, 150)
centre.set_editor_property("r", 0.5)
centre.set_editor_property("g", 0.5)
sub = node(mat, unreal.MaterialExpressionSubtract, -1000, 0)
length = node(mat, unreal.MaterialExpressionLength, -850, 0)
two = node(mat, unreal.MaterialExpressionConstant, -850, 150)
two.set_editor_property("r", 2.0)
twice = node(mat, unreal.MaterialExpressionMultiply, -700, 0)
inv = node(mat, unreal.MaterialExpressionOneMinus, -550, 0)
sat = node(mat, unreal.MaterialExpressionSaturate, -420, 0)
sq = node(mat, unreal.MaterialExpressionMultiply, -290, 0)
opacity = scalar(mat, "Opacity", 0.35, -290, 200)
tint = node(mat, unreal.MaterialExpressionVectorParameter, -290, 350)
tint.set_editor_property("parameter_name", "Tint")
tint.set_editor_property("default_value", unreal.LinearColor(1.0, 0.9, 0.7, 1.0))
gain = node(mat, unreal.MaterialExpressionMultiply, -150, 100)
out = node(mat, unreal.MaterialExpressionMultiply, 0, 200)
link(uv, "", sub, "A")
link(centre, "", sub, "B")
link(sub, "", length, "")
link(length, "", twice, "A")
link(two, "", twice, "B")
link(twice, "", inv, "")
link(inv, "", sat, "")
link(sat, "", sq, "A")
link(sat, "", sq, "B")
link(sq, "", gain, "A")
link(opacity, "", gain, "B")
link(gain, "", out, "A")
link(tint, "", out, "B")
link_out(out, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(mat)
eal.save_asset(path)
unreal.log("VFX_IMPORT material %s" % path)
unreal.log("VFX_IMPORT done textures=%d" % len(tasks))
