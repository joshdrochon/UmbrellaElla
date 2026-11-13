#!/usr/bin/env python3
"""Resolve a merge conflict in docs/build/rule-status.csv row by row (gate only).

Each row is keyed by Rule ID. A row the lane changed since the merge base takes the lane's version; every other row keeps
main's. Rows added on either side are kept. If both sides changed the same row differently, the lane's row wins only when
main's row is unchanged from the base; otherwise the script prints the Rule IDs and exits 1 (a real conflict).
Usage: run inside a checkout with an unresolved merge of that file. Writes the file and stages it.
"""
import csv, io, subprocess, sys

PATH = "docs/build/rule-status.csv"

def stage(n):
    r = subprocess.run(["git", "show", f":{n}:{PATH}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""

def rows(text):
    rd = list(csv.reader(io.StringIO(text)))
    return (rd[0] if rd else []), {r[0]: r for r in rd[1:] if r}, [r[0] for r in rd[1:] if r]

def main():
    hb, base, _ = rows(stage(1))
    ho, ours, order = rows(stage(2))
    ht, theirs, torder = rows(stage(3))
    clash, out = [], {}
    for k in order + [k for k in torder if k not in ours]:
        b, o, t = base.get(k), ours.get(k), theirs.get(k)
        if t is None: out[k] = o; continue
        if o is None: out[k] = t; continue
        if t == b or t == o: out[k] = o
        elif o == b: out[k] = t
        else: clash.append(k)
    if clash:
        print("rule_status_merge: both sides changed " + ", ".join(clash)); return 1
    buf = io.StringIO(); w = csv.writer(buf, lineterminator="\n"); w.writerow(ho or ht)
    for k in order + [k for k in torder if k not in ours]:
        if out.get(k): w.writerow(out[k])
    open(PATH, "w").write(buf.getvalue()); subprocess.run(["git", "add", PATH], check=True)
    print(f"rule_status_merge: {len(out)} rows merged"); return 0

if __name__ == "__main__":
    sys.exit(main())
