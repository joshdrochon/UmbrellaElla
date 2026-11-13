#!/usr/bin/env python3
"""HAZ-16 agent play-tester (decision D-new-haz16-agent-playtest).

A fresh Claude Sonnet session per attempt plays the Broken Mill room from the rendered screen with natural input only:
it sees frames (the game window as the game wrote them) and the controls text, and answers with key presses. The game
side is Source/UmbrellaElla/Private/Smoke/AgentPlayHookSubsystem.cpp (workbench builds only): it presses the keys through
the normal input path, pauses between turns, and measures damage, hits, warnings and idle time itself. There is no
teleport, auto-aim, invulnerability or route driver on this path.

Per attempt it records what HAZ-16 lists: what the player expected to be solid / harmful / background (asked before any
play), the descent and reset plan (before any play), useful shots and hits, warning recognition (player's flags against the
game's warning events), damage, reset and idle time, the player's own words, and a boring yes/no verdict.

Usage:
  agent_play.py --rule HAZ-16 --res 1280x720 --health healthy --attempts 3 --out Saved/AgentPlay/run1
  agent_play.py --rule HAZ-16 --res 1280x720 --health both --profile comparison --after Saved/AgentPlay/run1
  agent_play.py --summarize Saved/AgentPlay/run1      (rebuild the log from the attempt records)
Resolutions: 1280x720 and 1728x1117 on this Mac (it clamps 1920x1080, even offscreen); 1920x1080 on the Windows check.
Profiles: natural = the 10 HP guard (first, always). comparison = the 20 HP guard, ONE changed variable, allowed only
after a natural log whose attempts the player understood and rejected as boring (GDD HAZ-16).
Output: <out>/haz16.log, lines the playtest checker reads (tools/build/playtest_check.py), plus attempt_NN/attempt.json.
"""
import argparse
import base64
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONTROLS = os.path.join(HERE, "agent_play_controls.txt")
MAC_SIZES = ("1280x720", "1728x1117")
ALL_SIZES = MAC_SIZES + ("1920x1080",)
MODEL = "claude-sonnet-5-5"
MAX_TURN_MS = 3000
MAX_LINES = 24
FRAMES_PER_TURN = 2
MAX_TURNS = 30
GAME_START_TIMEOUT_S = 300
TURN_TIMEOUT_S = 120
STOP_TIMEOUT_S = 15
POLL_S = 0.2
BORING_SHARE = 0.5  # more than this share of the attempts calling it boring rejects the group

# Default controls only. Mirrors AgentPlayRules.cpp (tests/test_agent_play.py compares the two tables).
KEYS = {
    "j": "J", "k": "K", "q": "Q", "e": "E", "w": "W", "a": "A", "s": "S", "d": "D",
    "space": "SpaceBar", "spacebar": "SpaceBar", "shift": "LeftShift", "leftshift": "LeftShift",
    "up": "Up", "down": "Down", "left": "Left", "right": "Right",
    "1": "One", "2": "Two", "3": "Three", "4": "Four",
    "[": "LeftBracket", "]": "RightBracket", "leftbracket": "LeftBracket", "rightbracket": "RightBracket",
    "leftmouse": "LeftMouseButton", "leftmousebutton": "LeftMouseButton",
    "rightmouse": "RightMouseButton", "rightmousebutton": "RightMouseButton",
}


# ---------------------------------------------------------------- turn scripts (mirror of AgentPlayRules::ParseTurn)

def validate_turn(text):
    """Errors of a turn script (empty list = the game will run it). Same rules as the game's parser."""
    errs, cursor, end, used = [], 0, 0, 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        used += 1
        if used > MAX_LINES:
            errs.append("more than %d lines" % MAX_LINES)
            break
        w = line.split()
        verb = w[0].lower()
        if verb == "wait":
            if len(w) != 2 or not w[1].isdigit() or int(w[1]) > MAX_TURN_MS:
                errs.append("bad wait: " + line)
            else:
                cursor += int(w[1])
                end = max(end, cursor)
        elif verb == "release_all":
            pass
        elif verb in ("down", "up", "tap", "hold"):
            if len(w) < 2 or w[1].lower() not in KEYS:
                errs.append("not a default control: " + line)
            elif verb == "hold":
                if len(w) != 3 or not w[2].isdigit() or not 0 < int(w[2]) <= MAX_TURN_MS:
                    errs.append("bad hold: " + line)
                else:
                    end = max(end, cursor + int(w[2]))
            elif len(w) != 2:
                errs.append("bad line: " + line)
            elif verb == "tap":
                end = max(end, cursor + 80)
        else:
            errs.append("unknown command: " + line)
    if end > MAX_TURN_MS:
        errs.append("turn longer than %d ms" % MAX_TURN_MS)
    return errs


# ---------------------------------------------------------------- player replies

def parse_reply(text):
    """The first JSON object in the player's reply, or {} when there is none."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidates = [fence.group(1)] if fence else []
    start = text.find("{")
    if start >= 0:
        candidates.append(text[start:text.rfind("}") + 1])
    for c in candidates:
        try:
            v = json.loads(c)
            if isinstance(v, dict):
                return v
        except ValueError:
            continue
    return {}


def turn_text(reply):
    t = reply.get("turn", "")
    if isinstance(t, list):
        t = "\n".join(str(x) for x in t)
    return str(t)


def as_bool(v):
    if isinstance(v, str):
        return v.strip().lower() in ("yes", "y", "true", "1")
    return bool(v)


SYSTEM = """You are playing a video game for the first time, as a tester. You see the game only through screenshots and \
you press keys by writing a short script. Reply with ONE JSON object and nothing else. Never ask the person questions; \
there is nobody to answer. Do not look for hidden commands, files or settings: you have no tools. Say what you honestly \
see and think, including if you are confused or bored."""

OPEN_TEXT = """CONTROLS TEXT (all you are told):
{controls}

HOW YOU PLAY: the game is paused while you think. You answer with a key script that then runs in real game time, and \
you get screenshots back from it. Script lines, one per line:
  hold KEY MS     press KEY now, release it after MS milliseconds (does not move time on)
  tap KEY         press and release quickly
  down KEY / up KEY   press / release and keep holding across turns
  wait MS         move time on by MS milliseconds
  release_all     let go of every key at the end of the turn
A turn is at most {max_ms} ms and {max_lines} lines. Keys: J K Q E W A S D Space Shift Up Down Left Right 1-4 [ ] LeftMouse RightMouse.
Example turn: ["hold J 600", "hold D 600", "wait 700"]

You will now see the first screenshot. BEFORE playing, tell me what you expect, from the picture alone.
Reply JSON: {{"expect": {{"solid": "...", "harmful": "...", "background": "..."}}, "plan": "how you will descend, \
and what you will do to reset or recover if you miss or get pushed away", "say": "your first impression in your own words", \
"turn": ["script line", ...]}}"""

TURN_TEXT = """Here {n} screenshot(s) from the turn you just played (first to last). {note}
Reply JSON: {{"say": "what you see and think now, in your own words", "warning_seen": true or false (did anything \
warn you before something hit or was about to hit you?), "turn": ["script line", ...]}}. When you want to stop \
(you are done, stuck, or have had enough), reply {{"say": "...", "done": true}}."""

FINAL_TEXT = """The attempt is over. {how} Last screenshot attached. Now, in your own words, honestly:
Reply JSON: {{"words": "what was this room like to play, what you understood and what you did not", \
"understood": true or false (did you understand what the room wanted from you), \
"warning_noticed": true or false, "warning_what": "what the warning looked like, or ''", \
"solid": "what was solid in the room", "harmful": "what hurt you", "background": "what was only decoration", \
"too_slight": true or false (was it understood but too slight, too easy to matter), \
"boring": "yes" or "no", "boring_why": "one sentence"}}"""


# ---------------------------------------------------------------- the player (one claude -p session per attempt)

class ClaudePlayer:
    """A fresh Sonnet session per attempt. No tools, no project files: stream-json input with images only."""

    def __init__(self, model=MODEL, workdir=None):
        self.model = model
        self.session = str(uuid.uuid4())
        self.started = False
        self.workdir = workdir or os.path.join("/tmp", "agent_play_player_" + self.session)
        os.makedirs(self.workdir, exist_ok=True)
        self.cost = 0.0

    def ask(self, text, images):
        content = [{"type": "text", "text": text}]
        for path in images:
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            ext = os.path.splitext(path)[1].lower()
            content.append({"type": "image", "source": {"type": "base64", "data": data,
                                                         "media_type": "image/png" if ext == ".png" else "image/jpeg"}})
        msg = json.dumps({"type": "user", "message": {"role": "user", "content": content}})
        cmd = ["claude", "-p", "--model", self.model, "--input-format", "stream-json", "--output-format", "stream-json",
               "--verbose", "--tools", "", "--setting-sources", "", "--disable-slash-commands"]
        cmd += ["--resume", self.session] if self.started else ["--session-id", self.session, "--system-prompt", SYSTEM]
        # cwd is an empty scratch folder so no CLAUDE.md or project file is in reach.
        p = subprocess.run(cmd, input=msg + "\n", capture_output=True, text=True, cwd=self.workdir, timeout=600)
        self.started = True
        result = ""
        for line in p.stdout.splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "result":
                result = d.get("result") or ""
                self.cost += float(d.get("total_cost_usd") or 0)
        if not result:
            raise RuntimeError("player returned nothing: " + (p.stderr or p.stdout)[-300:])
        return result


# ---------------------------------------------------------------- the game process

class Game:
    """The game under run_game.sh (editor -game, workbench). Files in `dir` are the whole protocol."""

    def __init__(self, dir, res, low, comparison, max_game_s, log_path):
        self.dir, self.res, self.low, self.comparison = dir, res, low, comparison
        self.max_game_s, self.log_path, self.proc = max_game_s, log_path, None

    def start(self):
        os.makedirs(self.dir, exist_ok=True)
        args = ["-AgentPlay=" + self.dir, "-AgentPlayMaxSeconds=%d" % self.max_game_s, "-log"]
        if self.low:
            args.append("-AgentPlayLow")
        if self.comparison:
            args.append("-MillGuardComparison")
        env = dict(os.environ, RUN_RES=self.res)
        cmd = [os.path.join(ROOT, "tools/build/ue_slot.sh"), os.path.join(ROOT, "tools/build/run_game.sh")] + args
        self.log = open(self.log_path, "w")
        self.proc = subprocess.Popen(cmd, env=env, stdout=self.log, stderr=subprocess.STDOUT, start_new_session=True)

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, 15)
                self.proc.wait(timeout=20)
            except Exception:
                try:
                    os.killpg(self.proc.pid, 9)
                except Exception:
                    pass
        if getattr(self, "log", None):
            self.log.close()


def read_status(d):
    try:
        with open(os.path.join(d, "status.json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def wait_for(d, states, turn=None, timeout=TURN_TIMEOUT_S, alive=lambda: True, sleep=time.sleep):
    """Block until status.json shows one of `states` (and, if given, turn >= turn)."""
    end = time.time() + timeout
    while time.time() < end:
        s = read_status(d)
        if s.get("state") in states and (turn is None or s.get("turn", 0) >= turn or s.get("state") == "ended"):
            return s
        if not alive() and s.get("state") != "ended":
            raise RuntimeError("game exited (state %s)" % s.get("state"))
        sleep(POLL_S)
    raise RuntimeError("timeout waiting for %s (last %s)" % (states, read_status(d)))


def frames(d):
    fd = os.path.join(d, "frames")
    try:
        names = sorted(n for n in os.listdir(fd) if re.fullmatch(r"f\d{6}\.jpg", n))
    except OSError:
        return []
    return [os.path.join(fd, n) for n in names]


def pick_frames(paths, n):
    """n frames from a list, first to last, evenly spaced (the last is always included)."""
    if not paths:
        return []
    if len(paths) <= n:
        return list(paths)
    if n == 1:
        return [paths[-1]]
    return [paths[round(i * (len(paths) - 1) / (n - 1))] for i in range(n)]


def write_turn(d, number, text):
    path = os.path.join(d, "turn_%04d.txt" % number)
    with open(path + ".tmp", "w") as f:
        f.write(text)
    os.replace(path + ".tmp", path)


# ---------------------------------------------------------------- one attempt

def play_attempt(game, player, d, max_turns=MAX_TURNS, sleep=time.sleep):
    """Play one attempt to its end. Returns the attempt record (the player's words and the game's measurements)."""
    with open(CONTROLS) as f:
        controls = f.read().strip()
    rec = {"turns": [], "refused": []}
    alive = game.alive
    wait_for(d, ("ready",), timeout=GAME_START_TIMEOUT_S, alive=alive, sleep=sleep)
    first = frames(d)
    seen = len(first)
    reply = parse_reply(player.ask(OPEN_TEXT.format(controls=controls, max_ms=MAX_TURN_MS, max_lines=MAX_LINES),
                                   pick_frames(first, 1)))
    rec["expect"] = reply.get("expect") or {}
    rec["plan"] = reply.get("plan", "")
    rec["first_impression"] = reply.get("say", "")
    number = 0
    warning_flags = 0
    end_how = ""
    for _ in range(max_turns):
        script = turn_text(reply)
        if reply.get("done") and not script.strip():
            end_how = "You chose to stop."
            break
        errs = validate_turn(script)
        number += 1
        rec["turns"].append({"n": number, "say": reply.get("say", ""), "script": script,
                             "warning_seen": as_bool(reply.get("warning_seen", False)), "errors": errs})
        warning_flags += 1 if as_bool(reply.get("warning_seen", False)) else 0
        note = ""
        if errs:
            # The game would refuse it too; the player is told, no game time passes.
            rec["refused"].append({"n": number, "errors": errs})
            note = "Your script was refused (%s); nothing happened. Try again." % "; ".join(errs)
            number -= 1
            ask_images = pick_frames(frames(d), 1)
        else:
            write_turn(d, number, script)
            st = wait_for(d, ("paused", "ended"), turn=number, alive=alive, sleep=sleep)
            all_frames = frames(d)
            ask_images = pick_frames(all_frames[seen:], FRAMES_PER_TURN) or pick_frames(all_frames, 1)
            seen = len(all_frames)
            if st.get("state") == "ended":
                end_how = "The attempt ended."
                break
        reply = parse_reply(player.ask(TURN_TEXT.format(n=len(ask_images), note=note), ask_images))
        if not reply:
            reply = {"done": True, "say": "(unreadable reply)"}
    else:
        end_how = "You ran out of turns."
    if read_status(d).get("state") != "ended":
        # The player stopped (or ran out of turns) before the game did: tell the game to end the attempt as 'stopped'.
        with open(os.path.join(d, "stop.txt"), "w") as f:
            f.write("stop\n")
    st = wait_for(d, ("ended",), timeout=STOP_TIMEOUT_S, alive=lambda: True, sleep=sleep)
    rec["end_state"] = st.get("state", "")
    final = parse_reply(player.ask(FINAL_TEXT.format(how=end_how or "The attempt ended."), pick_frames(frames(d), 1)))
    rec["final"] = final
    rec["warning_flags"] = warning_flags
    rec["player_cost_usd"] = round(getattr(player, "cost", 0.0), 4)
    return rec


def read_result(d, timeout=20, sleep=time.sleep):
    end = time.time() + timeout
    p = os.path.join(d, "result.json")
    while time.time() < end:
        try:
            with open(p) as f:
                return json.load(f)
        except (OSError, ValueError):
            sleep(0.5)
    return {}


# ---------------------------------------------------------------- the log

def attempt_line(i, a):
    r, f = a.get("result", {}), a.get("final", {})
    kv = [("n", i), ("outcome", r.get("outcome", "none")), ("res", r.get("res", "?")), ("health", r.get("health", "?")),
          ("profile", r.get("profile", "?")), ("turns", len(a.get("turns", []))), ("shots", r.get("shots", 0)),
          ("useful_hits", r.get("useful_hits", 0)), ("damage", r.get("damage", 0)), ("reset_s", r.get("reset_s", 0)),
          ("idle_s", r.get("idle_s", 0)), ("warnings", r.get("warnings", 0)),
          ("warning_flags", a.get("warning_flags", 0)), ("understood", int(as_bool(f.get("understood", False)))),
          ("boring", int(as_bool(f.get("boring", False))))]
    return "PLAYTEST_HAZ16_ATTEMPT " + " ".join("%s=%s" % (k, v) for k, v in kv)


def group_key(a):
    r = a.get("result", {})
    return (r.get("res", "?"), r.get("health", "?"), r.get("profile", "natural"))


def group_line(key, atts):
    """One PLAYTEST_HAZ16 line for the attempts of one (res, health, profile) cell."""
    res, health, profile = key
    n = len(atts)
    rs = [a.get("result", {}) for a in atts]
    fs = [a.get("final", {}) for a in atts]
    warned = any(int(r.get("warnings", 0)) > 0 for r in rs)
    # Recognised: in an attempt where the game showed a warning, the player said they saw one (turn flag or final).
    recognised = any(int(r.get("warnings", 0)) > 0 and (a.get("warning_flags", 0) > 0 or as_bool(f.get("warning_noticed", False)))
                     for a, r, f in zip(atts, rs, fs))
    boring = sum(1 for f in fs if as_bool(f.get("boring", False)))
    understood = sum(1 for f in fs if as_bool(f.get("understood", False)))
    tele = any(int(r.get("teleport", 0)) for r in rs)
    dbg = any(int(r.get("debug", 0)) for r in rs)
    cleared = sum(1 for r in rs if r.get("outcome") == "cleared")
    mean = lambda k: round(sum(float(r.get(k, 0)) for r in rs) / max(n, 1), 2)
    kv = [("res", res), ("debug", int(dbg)), ("health", health), ("profile", profile), ("source", "agent"),
          ("attempts", n), ("shots", sum(int(r.get("shots", 0)) for r in rs)),
          ("useful_hits", sum(int(r.get("useful_hits", 0)) for r in rs)), ("damage", mean("damage")),
          ("reset_s", mean("reset_s")), ("idle_s", mean("idle_s")), ("warned", int(warned)),
          ("warning_recognised", int(recognised)), ("autoaim", 0), ("invuln", 0), ("teleport", int(tele)),
          ("understood", int(understood > n / 2)), ("too_slight", int(sum(1 for f in fs if as_bool(f.get("too_slight", False))) > n / 2)),
          ("boring", int(boring > n * BORING_SHARE)), ("cleared", int(cleared > 0)), ("cleared_n", cleared),
          ("words", int(all(str(f.get("words", "")).strip() for f in fs))),
          ("plan", int(all(str(a.get("plan", "")).strip() for a in atts))),
          ("expect", int(all(all(str((a.get("expect") or {}).get(k, "")).strip() for k in ("solid", "harmful", "background")) for a in atts))),
          ("relay", 0)]
    return "PLAYTEST_HAZ16 " + " ".join("%s=%s" % (k, v) for k, v in kv)


def build_log(attempts, header):
    lines = ["# " + header]
    groups = {}
    for i, a in enumerate(attempts, 1):
        lines.append(attempt_line(i, a))
        groups.setdefault(group_key(a), []).append(a)
    for key in sorted(groups):
        lines.append(group_line(key, groups[key]))
    return "\n".join(lines) + "\n"


def load_attempts(out):
    atts = []
    for name in sorted(os.listdir(out)):
        p = os.path.join(out, name, "attempt.json")
        if name.startswith("attempt_") and os.path.exists(p):
            with open(p) as f:
                atts.append(json.load(f))
    return atts


def comparison_allowed(natural_dir):
    """The 20 HP comparison is allowed only after natural attempts the player understood and rejected as boring."""
    atts = [a for a in load_attempts(natural_dir) if a.get("result", {}).get("profile") == "natural"]
    if not atts:
        return False, "no natural 10 HP attempts in " + natural_dir
    bad = [i for i, a in enumerate(atts, 1) if not (as_bool(a.get("final", {}).get("understood")) and as_bool(a.get("final", {}).get("boring")))]
    if bad:
        return False, "natural attempts %s were not 'understood but boring'; the 10 HP room is not rejected" % bad
    return True, ""


def header_line(res):
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return "commit=%s engine=5.8.4 config=Development host=%s run=Standalone res=%s player=%s" % (
        sha, "mac" if sys.platform == "darwin" else "win", res, MODEL)


# ---------------------------------------------------------------- main

def main(argv=None, game_factory=None, player_factory=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rule", default="HAZ-16")
    ap.add_argument("--res", default="1280x720")
    ap.add_argument("--health", default="healthy", choices=("healthy", "low", "both"))
    ap.add_argument("--profile", default="natural", choices=("natural", "comparison"))
    ap.add_argument("--after", help="natural run folder (required for --profile comparison)")
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--max-turns", type=int, default=MAX_TURNS)
    ap.add_argument("--max-game-s", type=int, default=90)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--out", default=os.path.join(ROOT, "Saved", "AgentPlay", time.strftime("%Y%m%d-%H%M%S")))
    ap.add_argument("--summarize", metavar="DIR")
    a = ap.parse_args(argv)

    if a.summarize:
        atts = load_attempts(a.summarize)
        text = build_log(atts, header_line("mixed"))
        with open(os.path.join(a.summarize, "haz16.log"), "w") as f:
            f.write(text)
        print(text)
        return 0
    if a.rule != "HAZ-16":
        print("agent_play: only --rule HAZ-16 is defined", file=sys.stderr)
        return 2
    if a.res not in ALL_SIZES:
        print("agent_play: --res must be one of %s" % ", ".join(ALL_SIZES), file=sys.stderr)
        return 2
    if a.res == "1920x1080" and sys.platform == "darwin":
        print("agent_play: this Mac clamps 1920x1080; run it in the Windows check (docs/build/windows-check.md)", file=sys.stderr)
        return 2
    if a.profile == "comparison":
        if not a.after:
            print("agent_play: --profile comparison needs --after <natural run folder>", file=sys.stderr)
            return 2
        ok, why = comparison_allowed(a.after)
        if not ok:
            print("agent_play: the 20 HP comparison is not allowed: " + why, file=sys.stderr)
            return 2
    game_factory = game_factory or Game
    player_factory = player_factory or (lambda: ClaudePlayer(a.model))
    os.makedirs(a.out, exist_ok=True)
    start = len(load_attempts(a.out))
    for health in (("healthy", "low") if a.health == "both" else (a.health,)):
        for k in range(a.attempts):
            idx = start + 1
            ad = os.path.join(a.out, "attempt_%02d" % idx)
            os.makedirs(ad, exist_ok=True)
            game = game_factory(ad, a.res, health == "low", a.profile == "comparison", a.max_game_s, os.path.join(ad, "game.log"))
            game.start()
            try:
                rec = play_attempt(game, player_factory(), ad, a.max_turns)
                rec["result"] = read_result(ad)
            except Exception as e:  # a crashed attempt is recorded, never hidden
                rec = {"error": str(e), "result": read_result(ad, timeout=1), "turns": [], "final": {}}
            finally:
                game.stop()
            rec["result"].setdefault("res", a.res)
            rec["result"].setdefault("health", health)
            rec["result"].setdefault("profile", a.profile)
            with open(os.path.join(ad, "attempt.json"), "w") as f:
                json.dump(rec, f, indent=1)
            start = idx
            print("attempt %d: %s" % (idx, attempt_line(idx, rec)))
    text = build_log(load_attempts(a.out), header_line(a.res))
    with open(os.path.join(a.out, "haz16.log"), "w") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
