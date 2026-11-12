"""Render one job's frames headless (run by Blender, never by python3):

  blender -b --factory-startup -P pipeline/art/blender/render_sprite.py -- --job <job.json>

The job (pipeline/art/blender/plan.py, written by tools/assetgen.py blender) names the builder, frame size, pivot,
facing, poses and look. Builds the stand-in (stand_ins.py), keys every pose on its frame, renders each frame to its
PNG (orthographic, transparent, ink-and-paper NPR), saves the .blend next to the frames (the provenance input), and
prints one line tools/assetgen.py reads:
  BLENDER_RENDER version=<x.y.z> frames=<n> blend=<path> freestyle=on|off compositor=on|off
Exit 1 on any error (Blender's own exit code stays 0 after a Python error, so the script exits itself).
"""
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--job" not in argv:
        raise SystemExit("render_sprite.py: pass -- --job <job.json>")
    return argv[argv.index("--job") + 1]


def main():
    import bpy
    import stand_ins
    with open(args(), encoding="utf-8") as fh:
        job = json.load(fh)
    scene, arm, extra, rep = stand_ins.setup(job)
    ppu = job["px_per_unit"]
    scene.frame_start, scene.frame_end = 1, max(1, len(job["poses"]))
    scene.render.fps = int(job.get("fps") or 12)
    os.makedirs(job["out_dir"], exist_ok=True)
    for p, out in zip(job["poses"], job["frames"]):
        scene.frame_set(p["index"] + 1)
        stand_ins.pose(arm, p, ppu, extra)
        for pb in arm.pose.bones:   # keyed, so the saved .blend holds the animation
            pb.keyframe_insert("rotation_quaternion", frame=p["index"] + 1)
            pb.keyframe_insert("scale", frame=p["index"] + 1)
        arm.keyframe_insert("location", frame=p["index"] + 1)
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.abspath(out)
        bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(job["blend"]), check_existing=False)
    print(f"BLENDER_RENDER version={bpy.app.version_string.split()[0]} frames={len(job['frames'])} "
          f"blend={job['blend']} freestyle={rep['freestyle']} compositor={rep['compositor']} engine={rep['engine']}")
    sys.stdout.flush()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:   # noqa: BLE001  any Blender error fails the step
        traceback.print_exc()
        sys.stdout.flush()
        os._exit(1)
