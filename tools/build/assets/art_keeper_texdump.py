"""Print the import and render settings that decide how sharp T_Keeper_Owl_PH draws (numbers only, read-only).

  python3 tools/build/assets/art_keeper_texdump.py        (launches UnrealEditor-Cmd through ue_slot.sh; nothing is saved)
Lines start with TEXDUMP so the log can be grepped."""
import os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ASSET = "/Game/UmbrellaElla/Art/Keeper/T_Keeper_Owl_PH"
CVARS = ["r.AntiAliasingMethod", "r.ScreenPercentage", "r.ScreenPercentage.Default", "r.ScreenPercentage.Default.Desktop.Mode",
         "r.MaxAnisotropy", "r.TemporalAA.Upsampling", "r.Tonemapper.Sharpen", "r.TSR.History.ScreenPercentage",
         "r.MipMapLODBias", "r.TextureStreaming"]


def in_editor():
    import unreal
    tex = unreal.EditorAssetLibrary.load_asset(ASSET)
    if not tex:
        unreal.log_error("TEXDUMP missing %s" % ASSET); return
    for p in ["compression_settings", "lod_group", "mip_gen_settings", "filter", "srgb", "never_stream", "lod_bias",
              "max_texture_size", "power_of_two_mode", "compression_quality", "address_x", "address_y",
              "adjust_brightness", "adjust_saturation", "adjust_vibrance", "adjust_rgb_curve", "chroma_key_texture",
              "compression_no_alpha", "defer_compression", "downscale", "lossy_compression_amount"]:
        try:
            unreal.log_warning("TEXDUMP %s=%s" % (p, tex.get_editor_property(p)))
        except Exception as e:  # property name differs between engine versions
            unreal.log_warning("TEXDUMP %s=<n/a %s>" % (p, type(e).__name__))
    unreal.log_warning("TEXDUMP size=%dx%d" % (tex.blueprint_get_size_x(), tex.blueprint_get_size_y()))
    for c in CVARS:
        unreal.log_warning("TEXDUMP cvar %s=%s" % (c, unreal.SystemLibrary.get_console_variable_float_value(c)))


def launch():
    ue = os.environ.get("UE_ROOT", "/Users/Shared/Epic Games/UE_5.8")
    exe = os.path.join(ue, "Engine", "Binaries", "Mac", "UnrealEditor-Cmd")
    cmd = [os.path.join(ROOT, "tools", "build", "ue_slot.sh"), exe, os.path.join(ROOT, "UmbrellaElla.uproject"),
           "-run=pythonscript", "-script=" + os.path.abspath(__file__), "-unattended", "-nullrhi", "-nosound", "-nosplash",
           "-nocrashreports", "-stdout"]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).stdout
    lines = [l[l.index("TEXDUMP"):] for l in out.splitlines() if "TEXDUMP" in l]
    print("\n".join(lines) if lines else out[-3000:])
    return 0 if lines else 1


if __name__ == "__main__":
    try:
        import unreal  # noqa: F401
    except ImportError:
        sys.exit(launch())
    in_editor()
