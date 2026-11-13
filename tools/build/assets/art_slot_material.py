"""Build M_ArtSlot_Unlit, the one material every art slot is drawn with (rebuildable).
Run (through tools/build/ue_slot.sh):
  UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=tools/build/assets/art_slot_material.py -unattended -nullrhi -nosplash -nocrashreports
Unlit, masked, two-sided. UV = ((U * TileU + Frame) / Cols, V * TileV); emissive = Art.RGB * Tint; opacity mask = Art.A.
Parameters match Source/UmbrellaElla/Private/Feedback/Art/ArtSlot.cpp: Art, Cols, Frame, TileU, TileV, Tint.
"""
import unreal

DEST = "/Game/UmbrellaElla/Materials"
NAME = "M_ArtSlot_Unlit"
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

path = "%s/%s" % (DEST, NAME)
if eal.does_asset_exist(path):
    eal.delete_asset(path)
mat = tools.create_asset(NAME, DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", True)


def node(cls, x, y):
    return mel.create_material_expression(mat, cls, x, y)


def link(a, a_out, b, b_in):
    if not mel.connect_material_expressions(a, a_out, b, b_in):
        raise RuntimeError("ART_SLOT could not connect %s.%s -> %s.%s" % (a.get_name(), a_out, b.get_name(), b_in))


def scalar(name, value, x, y):
    p = node(unreal.MaterialExpressionScalarParameter, x, y)
    p.set_editor_property("parameter_name", name)
    p.set_editor_property("default_value", value)
    return p


uv = node(unreal.MaterialExpressionTextureCoordinate, -1400, 0)
mask_u = node(unreal.MaterialExpressionComponentMask, -1200, -60)
mask_u.set_editor_property("r", True)
mask_u.set_editor_property("g", False)
mask_v = node(unreal.MaterialExpressionComponentMask, -1200, 80)
mask_v.set_editor_property("r", False)
mask_v.set_editor_property("g", True)
tile_u = scalar("TileU", 1.0, -1200, -200)
tile_v = scalar("TileV", 1.0, -1200, 220)
frame = scalar("Frame", 0.0, -1000, -200)
cols = scalar("Cols", 1.0, -800, -200)
mul_u = node(unreal.MaterialExpressionMultiply, -1000, -60)
mul_v = node(unreal.MaterialExpressionMultiply, -1000, 80)
add = node(unreal.MaterialExpressionAdd, -800, -60)
div = node(unreal.MaterialExpressionDivide, -650, -60)
app = node(unreal.MaterialExpressionAppendVector, -500, 0)
art = node(unreal.MaterialExpressionTextureSampleParameter2D, -350, 0)
art.set_editor_property("parameter_name", "Art")
tint = node(unreal.MaterialExpressionVectorParameter, -350, 300)
tint.set_editor_property("parameter_name", "Tint")
tint.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
colour = node(unreal.MaterialExpressionMultiply, -100, 100)
link(uv, "", mask_u, "")
link(uv, "", mask_v, "")
link(mask_u, "", mul_u, "A")
link(tile_u, "", mul_u, "B")
link(mask_v, "", mul_v, "A")
link(tile_v, "", mul_v, "B")
link(mul_u, "", add, "A")
link(frame, "", add, "B")
link(add, "", div, "A")
link(cols, "", div, "B")
link(div, "", app, "A")
link(mul_v, "", app, "B")
link(app, "", art, "UVs")
link(art, "RGB", colour, "A")
link(tint, "", colour, "B")
if not mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
    raise RuntimeError("ART_SLOT emissive")
if not mel.connect_material_property(art, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
    raise RuntimeError("ART_SLOT mask")
mel.recompile_material(mat)
eal.save_asset(path)
unreal.log("ART_SLOT material %s" % path)
