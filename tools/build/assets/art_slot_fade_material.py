"""Build M_ArtSlot_EdgeFade: the art slot material with soft left/right edges, for full-screen scene pictures whose
side edge scrolls into view (dcseamless, Josh Nov 13: the DC route read as "a mess of screens and frames"; the route
start and end pictures showed hard vertical cuts against the layered backdrop). Rebuildable:
  UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=tools/build/assets/art_slot_fade_material.py -unattended -nullrhi -nosplash -nocrashreports
Unlit, translucent, two-sided. Same parameters as M_ArtSlot_Unlit (Art, Cols, Frame, TileU, TileV, Tint) plus
FadeLeft / FadeRight (share of the picture width that fades at that edge; 0 = hard edge), FadeColor (haze tone, linear)
and OpacityShare (outer share of that band where opacity eases out). U = raw plane U,
edge = saturate(U / FadeLeft) * saturate((1 - U) / FadeRight);
emissive = lerp(FadeColor, Art.RGB, smoothstep(0, 1, edge)) * Tint; opacity = Art.A * smoothstep(0, OpacityShare, edge).
The picture's own pixels are untouched: the fade is composition only (approved art stays as approved).
"""
import unreal

DEST = "/Game/UmbrellaElla/Materials"
NAME = "M_ArtSlot_EdgeFade"
TINY = 0.0001
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

path = "%s/%s" % (DEST, NAME)
# Rebuild in place: an unattended commandlet cannot delete and re-create a loaded package (CanCreateAsset refuses).
if eal.does_asset_exist(path):
    mat = eal.load_asset(path)
    mel.delete_all_material_expressions(mat)
else:
    mat = tools.create_asset(NAME, DEST, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", True)


def node(cls, x, y):
    return mel.create_material_expression(mat, cls, x, y)


def link(a, a_out, b, b_in):
    if not mel.connect_material_expressions(a, a_out, b, b_in):
        raise RuntimeError("EDGE_FADE could not connect %s.%s -> %s.%s" % (a.get_name(), a_out, b.get_name(), b_in))


def scalar(name, value, x, y):
    p = node(unreal.MaterialExpressionScalarParameter, x, y)
    p.set_editor_property("parameter_name", name)
    p.set_editor_property("default_value", value)
    return p


def const(value, x, y):
    c = node(unreal.MaterialExpressionConstant, x, y)
    c.set_editor_property("r", value)
    return c


# UV exactly as M_ArtSlot_Unlit: ((U * TileU + Frame) / Cols, V * TileV)
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

# Edge fades on the raw plane U (0 at the picture's left edge, 1 at its right edge). Edge = 0 at a fading edge, 1 once
# FadeLeft/FadeRight in from it. The colour eases into FadeColor (the picture's own haze tone) across the whole band, so
# the land melts into haze; opacity eases out only over the outer OpacityShare of the band, so what dissolves is haze,
# never the painting (Josh, Nov 14: the 35% alpha ramp read as the barn picture dissolving into the void).
fade_l = scalar("FadeLeft", 0.0, -1000, 500)
fade_r = scalar("FadeRight", 0.0, -1000, 650)
share = scalar("OpacityShare", 0.4, -400, 900)
haze = node(unreal.MaterialExpressionVectorParameter, -400, -250)
haze.set_editor_property("parameter_name", "FadeColor")
haze.set_editor_property("default_value", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
tiny = const(TINY, -1000, 800)
zero = const(0.0, -400, 1000)
one = const(1.0, -400, 1100)
max_l = node(unreal.MaterialExpressionMax, -850, 500)
max_r = node(unreal.MaterialExpressionMax, -850, 650)
one_minus_u = node(unreal.MaterialExpressionOneMinus, -850, 800)
ramp_l = node(unreal.MaterialExpressionDivide, -700, 500)
ramp_r = node(unreal.MaterialExpressionDivide, -700, 650)
sat_l = node(unreal.MaterialExpressionSaturate, -550, 500)
sat_r = node(unreal.MaterialExpressionSaturate, -550, 650)
edges = node(unreal.MaterialExpressionMultiply, -400, 575)
colour_t = node(unreal.MaterialExpressionSmoothStep, -250, 300)
alpha_t = node(unreal.MaterialExpressionSmoothStep, -250, 700)
hazed = node(unreal.MaterialExpressionLinearInterpolate, -250, 0)
colour = node(unreal.MaterialExpressionMultiply, -100, 100)
opacity = node(unreal.MaterialExpressionMultiply, -100, 400)
link(fade_l, "", max_l, "A")
link(tiny, "", max_l, "B")
link(fade_r, "", max_r, "A")
link(tiny, "", max_r, "B")
link(mask_u, "", one_minus_u, "")
link(mask_u, "", ramp_l, "A")
link(max_l, "", ramp_l, "B")
link(one_minus_u, "", ramp_r, "A")
link(max_r, "", ramp_r, "B")
link(ramp_l, "", sat_l, "")
link(ramp_r, "", sat_r, "")
link(sat_l, "", edges, "A")
link(sat_r, "", edges, "B")
link(zero, "", colour_t, "Min")
link(one, "", colour_t, "Max")
link(edges, "", colour_t, "Value")
link(zero, "", alpha_t, "Min")
link(share, "", alpha_t, "Max")
link(edges, "", alpha_t, "Value")
link(haze, "", hazed, "A")
link(art, "RGB", hazed, "B")
link(colour_t, "", hazed, "Alpha")
link(hazed, "", colour, "A")
link(tint, "", colour, "B")
link(art, "A", opacity, "A")
link(alpha_t, "", opacity, "B")

if not mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
    raise RuntimeError("EDGE_FADE emissive")
if not mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY):
    raise RuntimeError("EDGE_FADE opacity")
mel.recompile_material(mat)
eal.save_asset(path)
unreal.log("EDGE_FADE material %s" % path)
