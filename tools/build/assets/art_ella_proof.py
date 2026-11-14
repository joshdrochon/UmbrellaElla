#!/usr/bin/env python3
"""Proof composite for an Ella piece: study | in-game before | in-game after, side by side at one height.

  python3 tools/build/assets/art_ella_proof.py <before.png> <after.png> <out.png> [--height 540] [--zoom x,y,w,h]

The study is Ricky's Other Realm study (bar-other-realm). --zoom adds a second row: the same box (fractions of the
frame, 0..1) cut from all three, so a small figure can be seen; for the study it is the box around Ella.
Needs Pillow.
"""
import argparse
import sys

from PIL import Image, ImageDraw

STUDY = "pipeline/art/reference/discord/20261111-0318_Ricky_other-realm.png"
STUDY_ELLA_BOX = (0.27, 0.32, 0.12, 0.18)    # fractions: Ella and her umbrella in the study
LABEL_PAD = 6
LABEL_FILL = (233, 196, 106)


def panel(img, height):
    return img.convert("RGB").resize((round(img.width * height / img.height), height), Image.LANCZOS)


def cut(img, box):
    x, y, w, h = box
    return img.crop((round(x * img.width), round(y * img.height), round((x + w) * img.width), round((y + h) * img.height)))


def row(images, labels, height):
    panels = [panel(i, height) for i in images]
    out = Image.new("RGB", (sum(p.width for p in panels), height))
    x = 0
    draw = ImageDraw.Draw(out)
    for p, label in zip(panels, labels):
        out.paste(p, (x, 0))
        draw.text((x + LABEL_PAD, LABEL_PAD), label, fill=LABEL_FILL)
        x += p.width
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("out")
    ap.add_argument("--height", type=int, default=540)
    ap.add_argument("--zoom", help="x,y,w,h fractions of the game frame around Ella")
    args = ap.parse_args(argv)
    study, before, after = Image.open(STUDY), Image.open(args.before), Image.open(args.after)
    rows = [row([study, before, after], ["study", "in-game before", "in-game after"], args.height)]
    if args.zoom:
        box = tuple(float(v) for v in args.zoom.split(","))
        rows.append(row([cut(study, STUDY_ELLA_BOX), cut(before, box), cut(after, box)],
                        ["study (Ella)", "before (Ella)", "after (Ella)"], args.height))
    width = max(r.width for r in rows)
    out = Image.new("RGB", (width, sum(r.height for r in rows)))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    out.save(args.out)
    print("proof: %s %dx%d" % (args.out, out.width, out.height))
    return 0


if __name__ == "__main__":
    sys.exit(main())
