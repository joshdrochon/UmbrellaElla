#!/usr/bin/env python3
"""Resolve a merge conflict in docs/build/clause-audit.csv or docs/build/clause-proof.csv row by row (Nov 13).

Rows are keyed by (rule, clause), plus proof for clause-proof.csv (one clause may have several proofs). The result is
the union of both sides' rows. When both sides hold the same key with different values, the row whose tag/status says
proven wins; otherwise the lane's (theirs) row wins when main's row is unchanged from the merge base, else main's.
Rows only main removed stay removed; rows only the lane removed stay removed.
Usage: clause_csv_merge.py [FILE...] inside a checkout with an unresolved merge. Writes and stages each file."""
import csv, io, subprocess, sys

FILES = ("docs/build/clause-audit.csv", "docs/build/clause-proof.csv")


def stage(path, n):
    r = subprocess.run(["git", "show", f":{n}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def parse(text):
    rd = csv.DictReader(io.StringIO(text))
    return list(rd.fieldnames or []), list(rd)


def key(path, r):
    k = ((r.get("rule") or "").strip(), (r.get("clause") or "").strip())
    return k + (((r.get("proof") or "").strip(),) if path.endswith("clause-proof.csv") else ())


def proven(r):
    """clause-audit: tag 'proven'. clause-proof: status 'proven' (an older row without status counts as proven)."""
    if "tag" in r:
        return (r.get("tag") or "").strip() == "proven"
    return (r.get("status") or "proven").strip() == "proven"


def merge(path, base_t, ours_t, theirs_t):
    """ours = main (the gate merges the lane into main), theirs = the lane. Returns the merged CSV text."""
    hb, base = parse(base_t)
    ho, ours = parse(ours_t)
    ht, theirs = parse(theirs_t)
    fields = ho + [f for f in ht if f not in ho]
    b = {key(path, r): r for r in base}
    o = {key(path, r): r for r in ours}
    t = {key(path, r): r for r in theirs}
    out, order = {}, []
    for k in [key(path, r) for r in ours] + [key(path, r) for r in theirs]:
        if k in out:
            continue
        ro, rt, rb = o.get(k), t.get(k), b.get(k)
        if ro is None and rt is None:
            continue
        if ro is None:   # only the lane has it: added by the lane, or removed by main
            if rb is not None and rb == rt:
                continue
            pick = rt
        elif rt is None:   # only main has it: added by main, or removed by the lane
            if rb is not None and rb == ro:
                continue
            pick = ro
        elif ro == rt:
            pick = ro
        elif proven(ro) != proven(rt):
            pick = ro if proven(ro) else rt
        else:
            pick = rt if (rb is not None and ro == rb) else ro
        out[k] = pick
        order.append(k)
    w = io.StringIO()
    cw = csv.DictWriter(w, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    cw.writeheader()
    for k in order:
        cw.writerow({f: out[k].get(f) or "" for f in fields})
    return w.getvalue()


def main(argv):
    paths = argv[1:] or [p for p in FILES]
    unresolved = set(subprocess.run(["git", "diff", "--name-only", "--diff-filter=U"], capture_output=True,
                                    text=True).stdout.split())
    done = []
    for p in paths:
        if p not in unresolved:
            continue
        text = merge(p, stage(p, 1), stage(p, 2), stage(p, 3))
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        subprocess.run(["git", "add", p], check=True)
        done.append(p)
    print("clause_csv_merge: resolved " + (", ".join(done) if done else "nothing"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
