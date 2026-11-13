#!/usr/bin/env python3
"""Art scheduler (Josh, Nov 12): every unpassed art piece has exactly one owning art-loop session; the number of
loops follows the work and the machine. Replaces ../UmbrellaElla-areas/art_keepalive.sh. Stdlib only.

  art_scheduler.py run [--once]    loop forever (or one cycle): group, count capacity, start/stop loops
  art_scheduler.py plan            one cycle, no side effects: print the decisions it would take
  art_scheduler.py groups          print the group file after grouping any unowned piece (writes nothing)

Inputs
  docs/build/art-inventory.csv on main (git show): piece, owner lane, passed.
  pass records: pipeline/art/critic/ on main and in each loop's own worktree, checked with tools/build/art_pass_verify.py
                (a piece passed on a loop's branch counts for that loop before the lead merges it).
  <areas>/art_groups.txt   lane|pieces   or   lane|parent|pieces   (parent = lane whose branch is merged first).
                           A piece no group names is grouped here (same owner, same family, 3-8 per loop) and the
                           new lines are appended. Lane names: <owner>, <owner>2, <owner>3 ...
  <areas>/art_models.txt   optional  lane|model  (a loop keeps its model; escalation is the lead's call).
Capacity (loops running at once) is the lowest of
  ART_MAX_LOOPS (default 6; Josh capped Unreal-heavy jobs machine-wide)
  load:   1-minute load average above ART_MAX_LOAD (20): no new loop starts
  memory: same thresholds as tools/build/ue_slot.sh. used < 36 GB: all; < 44 GB: 14; otherwise no new loop starts.
  spend:  remaining image budget (smallest of IMAGE_SPEND_CAP_USD, logs/image-cap-usd.txt and the counter's cap_usd,
          minus spent) / ART_MIN_USD_PER_LOOP (0.5); no cap known = no new loop.
A running loop is never killed for capacity; capacity only gates new starts.
A loop whose pieces all pass (verified) is stopped (touch .stop-<lane>, then SIGTERM) and its slot goes to the next
group without a session. A loop whose session exited with pieces left is restarted, at most ART_MAX_RESTARTS (8)
times in a row without a piece passing in between; after that it is left and the log says GIVE_UP.
Log: <areas>/logs/art-scheduler.log, one line per decision.
"""
import csv
import io
import json
import math
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

INVENTORY = "docs/build/art-inventory.csv"
MIN_LOOP, MAX_LOOP = 3, 8
MEM_FULL_GB, MEM_MID_GB, MEM_STOP_GB = 36.0, 44.0, 56.0
PS_RE = re.compile(r"^claude -p You are the '([A-Za-z0-9_]+)' area worker")

BRIEF = ("Lead: you are an art loop (no human review: loop to the bar). Your scope is EXACTLY these pieces: {pieces}. "
         "Do not work on any other piece; another loop owns it. First merge {merges}. Paint (Spend OK, shared "
         "cap; check the counter), judge every pair through tools/art_loop.py only, context capture per "
         "docs/build/art-image-model.md (merge origin/area/artslots for your slot once it has it). Commit after each "
         "round and keep docs/build/areas/{lane}-status.md current. Stop only when every piece in your scope passes, or "
         "a real blocker only the lead can fix (write it in docs/build/requests/{lane}.md).")


# ---------------------------------------------------------------- groups

class Group:
    def __init__(self, lane, parent, pieces):
        self.lane, self.parent, self.pieces = lane, parent, list(pieces)

    def line(self):
        head = self.lane if not self.parent else f"{self.lane}|{self.parent}"
        return f"{head}|{' '.join(self.pieces)}"


def parse_groups(text):
    out = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) == 2:
            out.append(Group(parts[0], "", parts[1].split()))
        elif len(parts) >= 3:
            out.append(Group(parts[0], parts[1], parts[2].split()))
    return out


def parse_inventory(text):
    """{piece: {"owner": lane, "passed": bool}}; a piece passes when every visual that names it passes."""
    inv = {}
    for row in csv.DictReader(io.StringIO(text)):
        p = row.get("piece", "").strip()
        if not p:
            continue
        e = inv.setdefault(p, {"owner": row.get("owner", "").strip(), "passed": True})
        e["passed"] = e["passed"] and row.get("passed", "").strip().lower() == "yes"
    return inv


def family(piece):
    return piece.split("-", 1)[0]


def chunk_owner_pieces(pieces):
    """Split one owner's pieces into loops of 3-8, keeping a piece family together where it fits."""
    fams = {}
    for p in sorted(pieces):
        fams.setdefault(family(p), []).append(p)
    chunks, cur = [], []
    for f in sorted(fams):
        ps = fams[f]
        if len(ps) > MAX_LOOP:   # a family bigger than a loop: split it evenly
            if cur:
                chunks.append(cur)
                cur = []
            k = math.ceil(len(ps) / MAX_LOOP)
            size = math.ceil(len(ps) / k)
            chunks += [ps[i:i + size] for i in range(0, len(ps), size)]
            continue
        if len(cur) + len(ps) > MAX_LOOP:
            chunks.append(cur)
            cur = []
        cur += ps
    if cur:
        chunks.append(cur)
    merged = []   # a loop under 3 pieces joins its neighbour when the sum fits
    for c in chunks:
        if merged and (len(c) < MIN_LOOP or len(merged[-1]) < MIN_LOOP) and len(merged[-1]) + len(c) <= MAX_LOOP:
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    return merged


def assign(groups, inv):
    """Dedupe (one owner per piece), then group every unpassed piece no group names.
    Returns (groups, new_groups, notes)."""
    notes, seen, out = [], {}, []
    for g in groups:
        keep = []
        for p in g.pieces:
            if p in seen:
                notes.append(f"DUPLICATE piece={p} kept_in={seen[p]} dropped_from={g.lane}")
            else:
                seen[p] = g.lane
                keep.append(p)
        out.append(Group(g.lane, g.parent, keep))
    used = {g.lane for g in out}
    unowned = {}
    for p, e in inv.items():
        if not e["passed"] and p not in seen and e["owner"]:
            unowned.setdefault(e["owner"], []).append(p)
    new = []
    for owner in sorted(unowned):
        for ch in chunk_owner_pieces(unowned[owner]):
            lane, n = owner, 1
            while lane in used:
                n += 1
                lane = f"{owner}{n}"
            used.add(lane)
            new.append(Group(lane, "" if lane == owner else owner, ch))
    return out + new, new, notes


# ---------------------------------------------------------------- capacity

def ue_slots(used_gb, forced=None):
    """Same thresholds as tools/build/ue_slot.sh."""
    if forced:
        return int(forced)
    if used_gb >= MEM_STOP_GB:
        return 0
    return 4 if used_gb < MEM_FULL_GB else 3 if used_gb < MEM_MID_GB else 2


def capacity(running, used_gb, remaining_usd, max_loops=6, min_usd=0.5, forced_slots=None, load=None, max_load=20.0):
    """(loops allowed to run at once, why). Never below `running`: capacity only gates new starts."""
    slots = ue_slots(used_gb, forced_slots)
    mem_cap = max_loops if slots >= 4 else min(max_loops, 14) if slots == 3 else running
    if remaining_usd is None:
        spend_cap, why = running, "no image cap known"
    else:
        spend_cap = running + int(max(0.0, remaining_usd) // min_usd)
        why = f"${max(0.0, remaining_usd):.2f} left"
    busy = load is not None and load > max_load
    cap = max(running, 0 if busy else min(max_loops, mem_cap, spend_cap))
    if busy:
        which = "load"
    elif mem_cap < min(max_loops, spend_cap):
        which = "memory"
    elif spend_cap < max_loops:
        which = "spend"
    else:
        which = "max"
    ld = "" if load is None else f", load1={load:.1f}"
    return cap, f"cap={cap} by {which} (ue_slots={slots}, used={used_gb:.1f}GB{ld}, {why})"


def load1():
    try:
        return os.getloadavg()[0]
    except (OSError, AttributeError):
        return None


def used_gb():
    mw = os.environ.get("UE_MEMWATCH") or os.path.expanduser("~/.umbrella-ella-memwatch")
    try:
        if time.time() - os.stat(mw).st_mtime < 180:
            m = re.search(r"used=([0-9.]+)GB", open(mw).read())
            if m:
                return float(m.group(1))
    except OSError:
        pass
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
        ps = int(subprocess.run(["pagesize"], capture_output=True, text=True).stdout.strip() or 16384)
        v = lambda pat: int(re.search(pat + r".*?(\d+)\.", out).group(1))
        return (v("Pages active") + v("Pages wired down") + v("occupied by compressor")) * ps / 1073741824
    except Exception:
        return MEM_STOP_GB   # unknown memory: start nothing new


def remaining_usd(base):
    """Image budget left: smallest cap of the env, the lead's cap file and the counter, minus spent. None = no cap."""
    caps = []
    for src in (os.environ.get("IMAGE_SPEND_CAP_USD"), _read(os.path.join(base, "logs", "image-cap-usd.txt"))):
        try:
            caps.append(float(str(src).strip()))
        except (TypeError, ValueError):
            pass
    spent = 0.0
    try:
        with open(os.environ.get("IMAGE_SPEND_FILE") or os.path.join(base, "logs", "image-spend.json")) as fh:
            d = json.load(fh)
        spent = float(d.get("spent_usd", 0))
        if d.get("cap_usd") is not None:
            caps.append(float(d["cap_usd"]))
    except (OSError, ValueError):
        pass
    return min(caps) - spent if caps else None


def _read(path):
    try:
        with open(path) as fh:
            return fh.read()
    except OSError:
        return None


# ---------------------------------------------------------------- plan

def plan(groups, passed_by_lane, running, state, cap, max_restarts=8):
    """Pure decision step. groups: [Group]; passed_by_lane: {lane: set(passed pieces)}; running: set of lanes with a
    live session; state: {lane: {"restarts": n, "left": k}}. Returns [(action, lane, detail)]:
    STOP (all pass), START (new), RESTART (session exited with work left), GIVE_UP, HOLD (no capacity), DONE."""
    acts, live = [], len(running)
    todo = []
    for g in groups:
        left = [p for p in g.pieces if p not in passed_by_lane.get(g.lane, set())]
        if not left:
            acts.append(("STOP" if g.lane in running else "DONE", g.lane, f"all {len(g.pieces)} pieces pass"))
            if g.lane in running:
                live -= 1
        else:
            todo.append((g, left))
    for g, left in todo:
        if g.lane in running:
            continue
        st = state.get(g.lane, {})
        restart = "last" in st or "restarts" in st
        n = st.get("restarts", 0) if st.get("left") == len(left) else 0
        if restart and n >= max_restarts:
            acts.append(("GIVE_UP", g.lane, f"{n} restarts with {len(left)} pieces left and none passing"))
            continue
        if live >= cap:
            acts.append(("HOLD", g.lane, f"{len(left)} pieces left, no capacity ({live}/{cap})"))
            continue
        live += 1
        acts.append(("RESTART" if restart else "START", g.lane,
                     f"pieces={len(left)}/{len(g.pieces)} restarts={n}" if restart else f"pieces={len(left)} unowned"))
    return acts


# ---------------------------------------------------------------- effects

class Scheduler:
    def __init__(self, repo=ROOT, base=None, dry=False, now=time.time):
        if os.path.basename(os.path.dirname(repo)) == "UmbrellaElla-areas":   # run from an area worktree
            repo = os.path.join(os.path.dirname(os.path.dirname(repo)), "UmbrellaElla")
        self.repo = os.environ.get("ART_REPO", repo)
        self.base = base or os.environ.get("ART_AREAS") or os.path.join(os.path.dirname(self.repo), "UmbrellaElla-areas")
        self.dry, self.now = dry, now
        self.groups_file = os.path.join(self.base, "art_groups.txt")
        self.state_file = os.path.join(self.base, ".art-scheduler.json")
        self.log_file = os.path.join(self.base, "logs", "art-scheduler.log")
        self.max_loops = int(os.environ.get("ART_MAX_LOOPS", "6"))
        self.max_restarts = int(os.environ.get("ART_MAX_RESTARTS", "8"))
        self.min_usd = float(os.environ.get("ART_MIN_USD_PER_LOOP", "0.5"))
        self._last = {}

    def log(self, msg, key=None):
        if key is not None:   # repeated identical decisions are written once
            if self._last.get(key) == msg:
                return
            self._last[key] = msg
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(self.now()))} {msg}"
        print(line, flush=True)
        if not self.dry:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, "a") as fh:
                fh.write(line + "\n")

    def inventory_text(self):
        p = subprocess.run(["git", "-C", self.repo, "show", f"main:{INVENTORY}"], capture_output=True, text=True)
        return p.stdout if p.returncode == 0 else (_read(os.path.join(self.repo, INVENTORY)) or "")

    def verified(self, root):
        try:
            import art_pass_verify
            return art_pass_verify.verified_pieces(root) if os.path.isdir(root) else set()
        except Exception as e:   # a broken verifier must never read as a pass
            self.log(f"WARN verifier failed for {root}: {e}", key=("warn", root))
            return set()

    def running(self):
        out = subprocess.run(["ps", "-ax", "-o", "pid=,command="], capture_output=True, text=True).stdout
        res = {}
        for ln in out.splitlines():
            pid, _, cmd = ln.strip().partition(" ")
            m = PS_RE.match(cmd)
            if m:
                res.setdefault(m.group(1), []).append(int(pid))
        return res

    def state(self):
        try:
            return json.load(open(self.state_file))
        except (OSError, ValueError):
            return {}

    def save_state(self, st):
        if not self.dry:
            with open(self.state_file, "w") as fh:
                json.dump(st, fh, indent=1, sort_keys=True)

    def models(self):
        out = {}
        for ln in (_read(os.path.join(self.base, "art_models.txt")) or "").splitlines():
            if "|" in ln and not ln.startswith("#"):
                a, _, m = ln.partition("|")
                out[a.strip()] = m.strip()
        return out

    def has_branch(self, name):
        return subprocess.run(["git", "-C", self.repo, "show-ref", "--verify", "--quiet",
                               f"refs/remotes/origin/area/{name}"]).returncode == 0

    def start(self, g, left, model):
        """True if start_area.sh succeeded. Names origin/area/<x> to merge only when that branch exists."""
        x = g.parent or g.lane
        merges = f"origin/area/{x} and main" if self.has_branch(x) else "main only (no origin/area branch for you yet)"
        brief = BRIEF.format(pieces=" ".join(left), merges=merges, lane=g.lane)
        env = dict(os.environ, WORKER_MODEL=model or "")
        p = subprocess.run([os.path.join(self.repo, "tools", "build", "start_area.sh"), g.lane, brief], cwd=self.repo,
                           env=env, capture_output=True, text=True)
        if p.returncode != 0:
            self.log(f"START_FAILED {g.lane} rc={p.returncode}: {(p.stderr or p.stdout).strip()[-300:]}")
        return p.returncode == 0

    def stop(self, lane, pids):
        open(os.path.join(self.base, f".stop-{lane}"), "w").close()   # start_area's wrapper does not resume after this
        for pid in pids:
            try:
                os.kill(pid, 15)
            except OSError:
                pass

    def cycle(self):
        inv = parse_inventory(self.inventory_text())
        if not inv:
            self.log("SKIP no inventory on main", key="inv")
            return []
        groups, new, notes = assign(parse_groups(_read(self.groups_file) or ""), inv)
        for n in notes:
            self.log(n, key=n)
        if new:
            self.log("GROUP " + "; ".join(f"{g.lane}={len(g.pieces)} pieces ({g.pieces[0]}..)" for g in new))
            if not self.dry:
                with open(self.groups_file, "a") as fh:
                    fh.write("".join(g.line() + "\n" for g in new))
        main_ok = {p for p, e in inv.items() if e["passed"]} | self.verified(self.repo)
        passed = {}
        for g in groups:   # a piece passed on the loop's own branch counts before the lead merges it
            passed[g.lane] = main_ok | self.verified(os.path.join(self.base, g.lane))
        run = self.running()
        st = self.state()
        lanes = {g.lane: g for g in groups}
        for lane in sorted(set(run) - set(lanes)):
            self.log(f"ORPHAN {lane} has a session but no group; left running", key=("orphan", lane))
        cap, why = capacity(len(run), used_gb(), remaining_usd(self.base), self.max_loops, self.min_usd,
                            os.environ.get("UE_SLOTS"), load1(),
                            float(os.environ.get("ART_MAX_LOAD", "20")))
        acts = plan(groups, passed, set(run), st, cap, self.max_restarts)
        models = self.models()
        for act, lane, detail in acts:
            g = lanes[lane]
            left = [p for p in g.pieces if p not in passed[lane]]
            if act == "STOP":
                self.log(f"STOP {lane} {detail}")
                if not self.dry:
                    self.stop(lane, run[lane])
            elif act in ("START", "RESTART"):
                rec = st.get(lane, {})
                n = rec.get("restarts", 0) if rec.get("left") == len(left) else 0
                self.log(f"{act} {lane} {detail} model={models.get(lane, 'default')} ({why})")
                if not self.dry:
                    if not self.start(g, left, models.get(lane, "")):
                        continue   # nothing is running: record nothing, so the next cycle starts it again
                    st[lane] = {"restarts": n + (1 if act == "RESTART" else 0), "left": len(left),
                                "last": int(self.now()), "last_act": act}
            elif act == "HOLD":
                self.log(f"HOLD {lane} {detail} ({why})", key=("hold", lane))
            elif act == "GIVE_UP":
                self.log(f"GIVE_UP {lane} {detail}; lead call (triage, model)", key=("giveup", lane))
        done = sum(1 for a in acts if a[0] in ("DONE", "STOP"))
        self.log(f"STATUS loops={len(groups)} running={len(run)} done={done} pieces_left="
                 f"{sum(1 for g in groups for p in g.pieces if p not in passed[g.lane])} {why}", key="status")
        self.save_state(st)
        return acts

    def run(self, once=False, interval=60):
        while True:
            try:
                self.cycle()
            except Exception as e:
                self.log(f"ERROR cycle failed: {type(e).__name__}: {e}", key="err")
            if once:
                return
            time.sleep(interval)


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    cmd = a[0] if a else "run"
    if cmd == "run":
        Scheduler().run(once="--once" in a)
    elif cmd == "plan":
        Scheduler(dry=True).cycle()
    elif cmd == "groups":
        s = Scheduler(dry=True)
        groups, _, _ = assign(parse_groups(_read(s.groups_file) or ""), parse_inventory(s.inventory_text()))
        print("".join(g.line() + "\n" for g in groups), end="")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
