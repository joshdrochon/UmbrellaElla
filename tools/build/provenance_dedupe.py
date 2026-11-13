#!/usr/bin/env python3
"""Collapse duplicate provenance rows after a merge (Nov 12: branches that each kept their own row for a take merged into
two or three rows, and audio_check fails a path with more than one row). One row per asset_path is kept:
- an Audio take: the row that agrees with the committed blind-critic record for its bytes (pass -> a non-placeholder
  row, fail -> the placeholder row); an "approved by" row always wins; with no record, the last row.
- any other path: the last row.
Rewrites pipeline/art/provenance.csv in place and prints what it collapsed. Usage: provenance_dedupe.py [--check]"""
import csv, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audio_check
P = os.path.join(ROOT, "pipeline", "art", "provenance.csv")


def main():
    with open(P, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    head, body = rows[0], rows[1:]
    oi = head.index("origin")
    by = {}
    for i, r in enumerate(body):
        if r:
            by.setdefault(r[0], []).append(i)
    drop = set()
    for path, idx in by.items():
        if len(idx) < 2:
            continue
        keep = idx[-1]
        if path.startswith("Audio/Source/") and path.lower().endswith(".wav"):
            sid = path.split("/")[2]
            takes = sorted(os.path.join(ROOT, p) for p in by if p.startswith(f"Audio/Source/{sid}/") and p.lower().endswith(".wav"))
            rec = audio_check.critic_verdict(sid, [t for t in takes if os.path.isfile(t)], ROOT)
            approved = [i for i in idx if "approved by" in body[i][oi]]
            if approved:
                keep = approved[-1]
            elif rec is not None:
                passed = rec.get("verdict") == "pass" and rec.get("style_pass")
                want = [i for i in idx if body[i][oi].startswith("placeholder") != passed]
                if want:
                    keep = want[-1]
        drop.update(i for i in idx if i != keep)
        print(f"provenance_dedupe: {path}: {len(idx)} rows -> 1 ({body[keep][oi][:60]})")
    if not drop:
        print("provenance_dedupe: no duplicate rows"); return 0
    if "--check" in sys.argv:
        return 1
    with open(P, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(head)
        w.writerows(r for i, r in enumerate(body) if i not in drop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
