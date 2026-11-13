"""Sandbox for the kickoff end-to-end tests: a copy of the repo's tools and docs (no game files) in a fresh git repo
with a bare origin, the People table filled, the fake gh (tests/fixtures/kickoff/fake_gh.py) and the stub agent
(tests/fixtures/kickoff/stub_agent.py). `human_round` plays the humans: it answers every needs-human ask the way the
checkpoint says (merge a PR kickoff could not merge, apply a gate patch, reply to a physical step) and removes the
label."""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

import hermetic

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIX = os.path.join(HERE, "fixtures", "kickoff")
GAME_PATHS = ("Source/", "Content/", "Config/", "Plugins/", "UmbrellaElla.uproject", "pipeline/qa/baked.json",
              "Packaged", "Saved/", ".github/workflows/clock.yml", ".pipeline-practice",
              "docs/build/MODE")   # build mode: these sandboxes test the card flow
PY = sys.executable


def fill_people(path, people_md):
    with open(path, encoding="utf-8") as fh:
        t = fh.read()
    i = t.index("## People")
    j = t.index("\n## ", t.index("## Team hours") + 3) + 1
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(t[:i] + people_md + t[j:])


class KickoffSandbox:
    def __init__(self, people_md, origin_url=None):
        self.base = tempfile.mkdtemp(prefix="kickoff-")
        self.repo = os.path.join(self.base, "repo")
        self.origin = os.path.join(self.base, "origin.git")
        files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT, capture_output=True,
                               text=True, check=True).stdout.split("\0")
        for f in files:
            src = os.path.join(ROOT, f)
            if f and os.path.isfile(src) and not f.startswith(GAME_PATHS) and not hermetic.lfs_pointer(src):
                dst = os.path.join(self.repo, f)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        hermetic.reference_stand_ins(ROOT, self.repo)   # pointer checkout (CI runner): drawn stand-ins, not pointers
        fill_people(os.path.join(self.repo, "docs", "jam-brief.md"), people_md)
        os.makedirs(os.path.join(self.repo, "docs", "build"), exist_ok=True)
        with open(os.path.join(self.repo, "docs", "build", "MODE"), "w", encoding="utf-8") as fh:
            fh.write("cards\n")   # these sandboxes test the card flow (no MODE file = direct)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@t")
        self.git("config", "user.name", "t")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "pre-jam")
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", self.origin], check=True)
        self.git("remote", "add", "origin", origin_url or self.origin)
        if not origin_url:
            self.git("push", "-q", "origin", "main")
        self.state = os.path.join(self.base, "gh.json")
        self.stub_state = os.path.join(self.base, "stub-state")
        os.makedirs(self.stub_state)
        self.log = os.path.join(self.base, "stub.log")

    def close(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def git(self, *args, cwd=None):
        p = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=cwd or self.repo, capture_output=True,
                           text=True, env=dict(os.environ, GIT_LFS_SKIP_SMUDGE="1"))
        assert p.returncode == 0, p.stderr
        return p.stdout.strip()

    def env(self, **extra):
        e = {k: v for k, v in os.environ.items()
             if k not in ("CLAUDECODE", "JAM_ROLE", "JAM_CARD", "JAM_HUMAN", "JAM_KICKOFF", "CODEX_SANDBOX",
                          "CODEX_THREAD_ID", "OPENAI_API_KEY", "ELEVENLABS_API_KEY", "STABILITY_API_KEY")}
        e.update(FAKE_GH_STATE=self.state, FAKE_GH_ORIGIN=self.origin, KICKOFF_GH=os.path.join(FIX, "fake_gh.py"),
                 KICKOFF_AGENT_CMD=shlex.join([PY, os.path.join(FIX, "stub_agent.py")]), KICKOFF_NOW="2026-11-09T12:00Z",
                 KICKOFF_SKIP_CHECK="1", KICKOFF_CLAIM_SETTLE="0", KICKOFF_PACKAGING_MACHINE="1", KICKOFF_MAC_MACHINE="1", JOURNAL_DB=os.path.join(self.base, "journal.db"), STUB_LOG=self.log,
                 STUB_STATE=self.stub_state, KEYS_NO_KEYCHAIN="1", PYTHONDONTWRITEBYTECODE="1")
        e.update(extra)
        return e

    def kickoff(self, *args, stdin_text="", **extra):
        p = subprocess.run([PY, "tools/kickoff.py", *args], cwd=self.repo, capture_output=True, text=True,
                           env=self.env(**extra), timeout=1200, input=stdin_text)
        return p.returncode, p.stdout + p.stderr

    def second_machine(self, name):
        """A clone of the same origin for a second kickoff machine (its own checkout, journal and stub state; the
        same fake GitHub and origin). The LFS objects come along, as a teammate's `git lfs pull` would fetch them."""
        repo = os.path.join(self.base, name)
        env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1")
        subprocess.run(["git", "clone", "-q", self.origin, repo], check=True, env=env, capture_output=True)
        self.git("config", "user.email", f"{name}@t", cwd=repo)
        self.git("config", "user.name", name, cwd=repo)
        lfs = os.path.join(self.repo, ".git", "lfs", "objects")
        if os.path.isdir(lfs):
            shutil.copytree(lfs, os.path.join(repo, ".git", "lfs", "objects"), dirs_exist_ok=True)
        subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "checkout", "-f", "HEAD", "--", "."], cwd=repo,
                       check=True, capture_output=True)
        return repo

    def machine_env(self, name, **extra):
        """env() for one of several kickoff machines: its own journal, stub log and stub state, KICKOFF_MACHINE=name."""
        d = os.path.join(self.base, "machine-" + name)
        os.makedirs(os.path.join(d, "stub"), exist_ok=True)
        return self.env(KICKOFF_MACHINE=name, JOURNAL_DB=os.path.join(d, "journal.db"),
                        STUB_LOG=os.path.join(d, "stub.log"), STUB_STATE=os.path.join(d, "stub"), **extra)

    def machine_sessions(self, name):
        p = os.path.join(self.base, "machine-" + name, "stub.log")
        if not os.path.exists(p):
            return []
        with open(p, encoding="utf-8") as fh:
            return [json.loads(ln) for ln in fh if ln.strip()]

    def gh(self):
        with open(self.state, encoding="utf-8") as fh:
            return json.load(fh)

    def save(self, s):
        with open(self.state, "w", encoding="utf-8") as fh:
            json.dump(s, fh, indent=1)

    def sessions(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return [json.loads(ln) for ln in fh if ln.strip()]

    def merge(self, pr):
        """The human squash-merges an approved PR into origin main."""
        work = os.path.join(self.base, "merge")
        if not os.path.isdir(work):
            self.git("clone", "-q", self.origin, work, cwd=self.base)
            self.git("config", "user.email", "h@h", cwd=work)
            self.git("config", "user.name", "human", cwd=work)
        self.git("checkout", "-q", "main", cwd=work)
        self.git("pull", "-q", "origin", "main", cwd=work)
        self.git("fetch", "-q", "origin", pr["headRefName"], cwd=work)
        self.git("merge", "--squash", "-q", "FETCH_HEAD", cwd=work)
        self.git("commit", "-q", "-m", f"{pr['title']} (#{pr['number']})", cwd=work)
        self.git("push", "-q", "origin", "main", cwd=work)
        pr["state"] = "MERGED"

    def human_round(self, stop_at="close G"):
        """Answer every open needs-human ask. Returns (answered, asks seen, the stop ask if one was reached)."""
        s = self.gh()
        answered, stop = [], None
        prs = {p["number"]: p for p in s["prs"]}
        for it in s["issues"]:
            if it["state"] != "OPEN" or "needs-human" not in it["labels"]:
                continue
            ask = [c["body"] for c in it["comments"] if "NEEDS HUMAN:" in c["body"]][-1]
            line = ask.split("NEEDS HUMAN:", 1)[1].strip()
            if stop_at and stop_at in line:
                stop = line
                continue
            if "merge PR #" in line:
                n = int(re.match(r"\d+", line.split("merge PR #", 1)[1]).group(0))
                self.merge(prs[n])
                it["state"] = "CLOSED"
            elif any(w in line for w in ("check and close card", "make the gate or binary edit", "unblock card",
                                         "apply the gate patch")):   # the checkpoint step, then the card closes
                it["state"] = "CLOSED"
            elif "review PR #" in line:   # a Human-only reviewer reads the PR and posts the verdict
                n = int(re.match(r"\d+", line.split("review PR #", 1)[1]).group(0))
                prs[n]["comments"].append({"body": f"Reviewed by the card's human\nVERDICT: approve"})
            it["comments"].append({"body": f"Done by the human: {line[:60]}"})
            it["labels"] = [x for x in it["labels"] if x not in ("needs-human", "doing", "review", "todo", "blocked")]
            answered.append(line)
        self.save(s)
        return answered, stop
