#!/usr/bin/env python3
"""Blind story critic by batches of lines, with a per-line record.
  story_critic_batch.py run [--batch N] [--sessions 3] [--only ID,ID]   judge lines, write pipeline/story/critic-results.csv
  story_critic_batch.py count                                          PASSED=<n>/<total> from the record
A line passes when every session answers S1..S8 true for it, on the current bible and text (hash recorded).
Sessions are fresh `claude -p` runs in an empty folder with only the packet (no Bash/Edit/Write)."""
import argparse, csv, hashlib, json, os, random, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINES, RES = "pipeline/story/lines.csv", "pipeline/story/critic-results.csv"
H = lambda s: hashlib.sha256(s.encode()).hexdigest()[:8]
ROW = re.compile(r"^[ \t>*-]*(?P<id>[A-Za-z0-9_.:-]+): (?P<rest>S1 .*)$", re.M)

def shipped():
    return [r for r in csv.DictReader(open(LINES)) if r.get("text") and (r.get("ship") or "").strip().lower() != "no"]

def packet(rows):
    p = open("tools/story_critic_prompt.md").read().split("---", 1)[-1]
    sj = json.load(open("pipeline/story/story.json"))
    sc = subprocess.run([sys.executable, "tools/story_check.py"], capture_output=True, text=True)
    p = p.replace("{story_bible}", open("pipeline/story/story-bible.md").read())
    p = p.replace("{story_json_surfaces_deny_banned}", json.dumps({k: sj[k] for k in sj if k in ("surfaces", "deny", "banned", "banned_words")}, indent=1))
    p = p.replace("{story_check_output}", (sc.stdout + sc.stderr).strip())
    rows = list(rows); random.shuffle(rows)
    return p + "\n\nLines to judge (id | surface | text), cycle=1, builder=area-worker:\n" + "\n".join(
        f"{r['id']} | {r['surface']} | {r['text']}" for r in rows)

def ask(pk):
    with tempfile.TemporaryDirectory() as w:
        env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
        r = subprocess.run(["claude", "-p", pk, "--permission-mode", "bypassPermissions", "--disallowedTools", "Bash", "Edit", "Write",
                            "--model", os.environ.get("CRITIC_MODEL", "claude-sonnet-5-5")], cwd=w, env=env, capture_output=True, text=True)
        return r.stdout

def judge(rows, sessions):
    pk = packet(rows)
    with ThreadPoolExecutor(sessions) as ex:
        outs = list(ex.map(lambda _: ask(pk), range(sessions)))
    res = {}
    for r in rows:
        gaps, seen = [], 0
        for o in outs:
            m = [x for x in ROW.finditer(o) if x.group("id") == r["id"]]
            if not m: gaps.append("no answer"); continue
            seen += 1
            rest = m[-1].group("rest")
            if re.search(r"\bS[1-8] false", rest): gaps.append(rest)
        res[r["id"]] = ("pass" if not gaps and seen == sessions else "fail", " || ".join(gaps))
    return res

def load():
    return {r["id"]: r for r in csv.DictReader(open(RES))} if os.path.exists(RES) else {}

def save(d):
    with open(RES, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "verdict", "text_hash", "bible_hash", "gaps"])
        for i, r in sorted(d.items()): w.writerow([i, r["verdict"], r["text_hash"], r["bible_hash"], r["gaps"]])

def count():
    bh = H(open("pipeline/story/story-bible.md").read()); d = load(); rows = shipped()
    n = sum(1 for r in rows if d.get(r["id"], {}).get("verdict") == "pass" and d[r["id"]]["text_hash"] == H(r["text"]) and d[r["id"]]["bible_hash"] == bh)
    return n, len(rows)

if __name__ == "__main__":
    os.chdir(ROOT)
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--sessions", type=int, default=3); ap.add_argument("--only", default="")
    a = ap.parse_args()
    if a.cmd == "count":
        n, t = count(); print(f"PASSED={n}/{t}"); sys.exit(0)
    bh = H(open("pipeline/story/story-bible.md").read()); d = load(); rows = shipped()
    if a.only: rows = [r for r in rows if r["id"] in a.only.split(",")]
    batches = [rows[i:i + a.batch] for i in range(0, len(rows), a.batch)]
    with ThreadPoolExecutor(3) as ex:
        for b, res in zip(batches, ex.map(lambda b: judge(b, a.sessions), batches)):
            for r in b:
                v, g = res[r["id"]]
                d[r["id"]] = dict(verdict=v, text_hash=H(r["text"]), bible_hash=bh, gaps=g)
            save(d); print(f"batch done: {sum(1 for r in b if res[r['id']][0]=='pass')}/{len(b)} pass", flush=True)
    n, t = count(); print(f"PASSED={n}/{t}")
