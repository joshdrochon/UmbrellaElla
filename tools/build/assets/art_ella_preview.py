#!/usr/bin/env python3
"""Ella state previews for the team: GIF + MP4 at game frame rate (8 FPS), each over the paper tile and a flat dark
ground side by side, plus a frame strip. Candidates stay _PH; output is not shipped art.

  python3 tools/build/assets/art_ella_preview.py            # all four states
Output: pipeline/art/proof/artella/preview/<state>/<state>_preview.{gif,mp4}, <state>_strip.png
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PROOF = os.path.join(ROOT, "pipeline", "art", "proof", "artella")
PAPER = os.path.join(ROOT, "pipeline", "art", "reference", "Test_Assets", "SKY_StarPaper_Tile.png")
FPS = 8
PANEL_W, PANEL_H, SPRITE_H = 480, 600, 540
DARK = "0x1c1c22"
# state -> (candidate round folder, frame prefix, frame count)
STATES = {
    "open": ("up-open/R1/frames_up-open", "Ella_up-open", 4),
    "attack": ("attack/R2/frames_attack", "Ella_attack", 3),
    "shield": ("shield/R2/frames_shield", "Ella_shield", 3),
    "closed": ("closed/R2/frames_closed", "Ella_closed", 3),
}


def run(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"] + args, check=True)


def build(state):
    folder, prefix, count = STATES[state]
    pattern = os.path.join(PROOF, folder, prefix + "_%02d.png")
    out = os.path.join(PROOF, "preview", state)
    os.makedirs(out, exist_ok=True)
    spr = "[0:v]format=rgba,scale=-2:%d,split=2[a][b]" % SPRITE_H
    bg1 = "[1:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d[p]" % (PANEL_W, PANEL_H, PANEL_W, PANEL_H)
    bg2 = "color=c=%s:s=%dx%d:r=%d[d]" % (DARK, PANEL_W, PANEL_H, FPS)
    fc = ";".join([spr, bg1, bg2,
                   "[p][a]overlay=(W-w)/2:(H-h)/2:shortest=1[l]", "[d][b]overlay=(W-w)/2:(H-h)/2:shortest=1[r]",
                   "[l][r]hstack,fps=%d" % FPS])
    base = ["-framerate", str(FPS), "-start_number", "0", "-i", pattern, "-loop", "1", "-i", PAPER]
    # MP4: the strip loops 6 times (about 2-3 s)
    mp4_in = ["-stream_loop", "5", "-framerate", str(FPS), "-start_number", "0", "-i", pattern, "-loop", "1", "-i", PAPER]
    run(mp4_in + ["-filter_complex", fc + ",format=yuv420p[o]", "-map", "[o]", "-frames:v", str(count * 6),
                  "-r", str(FPS), "-movflags", "+faststart", os.path.join(out, state + "_preview.mp4")])
    # GIF: one loop of the strip, endless
    run(base + ["-filter_complex", fc + ",split[s0][s1];[s0]palettegen=reserve_transparent=0[pal];[s1][pal]paletteuse[o]",
                "-map", "[o]", "-frames:v", str(count), "-loop", "0", os.path.join(out, state + "_preview.gif")])
    # strip: all frames side by side on the dark ground
    run(["-framerate", str(FPS), "-start_number", "0", "-i", pattern, "-f", "lavfi", "-i",
         "color=c=%s:s=%dx%d" % (DARK, 360, 420), "-filter_complex",
         "[0:v]format=rgba,scale=-2:400[s];[1:v][s]overlay=(W-w)/2:(H-h)/2:shortest=1,tile=%dx1" % count,
         "-frames:v", "1", os.path.join(out, state + "_strip.png")])


if __name__ == "__main__":
    for st in (sys.argv[1:] or STATES):
        build(st)
        print("preview", st, "ok")
