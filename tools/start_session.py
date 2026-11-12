#!/usr/bin/env python3
"""One-command launcher: a fresh agent session for one role on one card. A human runs it, from a plain terminal.

  tools/start_session.sh <role> <card> [--dry-run] [--tier "Quick checks"|Critic|Building|"Hard calls"]
                         [extra claude args...]    (Windows: tools\\start_session.ps1)

It checks the role (a key of roles in pipeline/agent-ops/gates.json) and the card (UE-<id>, <id>, 0.4a, #<issue>),
reads the role's model from pipeline/agent-ops/model-tiers.md (role table -> tier -> the first model ID in backticks;
--tier picks another row, e.g. "Quick checks" (Haiku 5.5) for a read-only lookup),
builds the first prompt from the card (a Day-0 card's row in pipeline/day0-cards.md; otherwise the GitHub issue
through `gh`, when gh is installed and logged in) and `journal.py resume`, then runs
`tools/agent.sh <role> <card> claude --model <id> [extra...] "<prompt>"`, so JAM_ROLE, JAM_CARD and the journal are
set the usual way. JAM_MODEL is set too, for the spend log. --dry-run prints the command and runs nothing.
Before launch it writes a run record (tools/journal.py runs: the exact prompt, pipeline version, model, GDD revision).

It refuses to run inside an agent session (CLAUDECODE or JAM_ROLE already set): agents never start agents
(AGENTS.md section 4.7: humans start sessions).
Exit 2 = usage error (missing argument, unknown role, bad card, no model for the role, inside an agent session);
otherwise the agent CLI's exit code.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATES = os.path.join(ROOT, "pipeline", "agent-ops", "gates.json")
TIERS = os.path.join(ROOT, "pipeline", "agent-ops", "model-tiers.md")
DAY0 = os.path.join(ROOT, "pipeline", "day0-cards.md")
CARD = re.compile(r"^(?:(?i:ue-)?(\d+(?:\.\d+)?[a-z]?)|#(\d+))$")
AGENT_ENV = ("CLAUDECODE", "JAM_ROLE")
USAGE = "usage: tools/start_session.sh <role> <card> [--dry-run] [--tier <tier>] [extra claude args...]"


class Usage(Exception):
    pass


def norm_card(raw):
    m = CARD.match((raw or "").strip())
    if not m:
        raise Usage(f"bad card {raw!r}: use UE-<id> (UE-12, UE-0.4a), <id> or #<issue>")
    return "UE-" + m.group(1) if m.group(1) else "#" + m.group(2)


def check_role(role, gates=GATES):
    with open(gates, encoding="utf-8") as fh:
        known = json.load(fh)["roles"]
    if role not in known:
        raise Usage(f"unknown role {role!r}; use a key of roles in pipeline/agent-ops/gates.json")


def table_rows(text):
    """Markdown table rows as lists of stripped cells, header and separator rows included."""
    for ln in text.splitlines():
        if ln.startswith("|") and ln.rstrip().endswith("|"):
            yield [c.strip() for c in ln.strip().strip("|").split("|")]


def tier_models(path=TIERS):
    """{tier: the first Claude model ID in backticks in its Model cell} from model-tiers.md."""
    with open(path, encoding="utf-8") as fh:
        rows = list(table_rows(fh.read()))
    out = {}
    for cells in rows:
        if len(cells) >= 3 and cells[0] not in ("Tier", "Role (`gates.json` key)") and not set(cells[0]) <= set("-: "):
            m = re.search(r"`([\w.-]+)`", cells[2])
            if m:
                out[cells[0]] = m.group(1)
    return out


def model_for(role, path=TIERS, tier=None):
    """(tier, model id) for a gates.json role key, from model-tiers.md; `tier` overrides the role's tier."""
    with open(path, encoding="utf-8") as fh:
        rows = list(table_rows(fh.read()))
    tier_model, role_tier = {}, {}
    for cells in rows:
        if len(cells) >= 3 and cells[0] not in ("Tier", "Role (`gates.json` key)") and not set(cells[0]) <= set("-: "):
            m = re.search(r"`([\w.-]+)`", cells[2])
            if m:
                tier_model[cells[0]] = m.group(1)
        if len(cells) == 2 and re.fullmatch(r"[a-z][a-z-]*", cells[0]):
            role_tier[cells[0]] = re.sub(r"\s*\(.*?\)\s*$", "", cells[1]).strip()
    tier = tier or role_tier.get(role)
    if not tier:
        raise Usage(f"{role} has no tier in pipeline/agent-ops/model-tiers.md")
    if tier not in tier_model:
        raise Usage(f"tier {tier!r} for {role} names no model ID in backticks in pipeline/agent-ops/model-tiers.md")
    return tier, tier_model[tier]


def day0_row(card, path=DAY0):
    if not card.startswith("UE-0."):
        return None
    cid = card[3:]
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            if ln.startswith(f"| {cid} |"):
                return ln.strip().replace("<br>", "\n  ")
    return None


def gh_card(card):
    """The issue text, or None when gh is missing, logged out or finds nothing. Never fails."""
    if not shutil.which("gh") or os.environ.get("START_SESSION_NO_GH"):
        return None
    try:
        if card.startswith("#"):
            cmd = ["gh", "issue", "view", card[1:], "--json", "number,title,body"]
        else:
            cmd = ["gh", "issue", "list", "--state", "all", "--search", f"{card} in:title", "--limit", "1",
                   "--json", "number,title,body"]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=20)
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout or "null")
        data = data[0] if isinstance(data, list) and data else data
        if not isinstance(data, dict):
            return None
        return f"#{data.get('number')} {data.get('title')}\n{data.get('body') or ''}".strip()
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def journal_resume(card):
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "journal.py"), "resume", "--card", card],
                           cwd=ROOT, capture_output=True, text=True, timeout=20)
        return (r.stdout or r.stderr).strip() or "(no journal entries)"
    except (OSError, subprocess.SubprocessError):
        return "(journal.py resume did not run)"


def first_prompt(role, card, card_text, resume):
    return "\n".join([
        f"ROLE: {role}. Your card is {card}. Follow AGENTS.md section 1 read order; your role card is "
        f"pipeline/roles/{role}.md.",
        "Card context (re-read the card and its PR comments on GitHub; this is a starting copy):",
        card_text or f"(card text not loaded: open {card} on GitHub)",
        "Journal on this machine (python3 tools/journal.py resume):",
        resume,
    ])


def build(argv, env=None):
    """(argv to run, env additions, summary line). Raises Usage."""
    env = os.environ if env is None else env
    inside = [k for k in AGENT_ENV if env.get(k)]
    if inside:
        raise Usage(f"{'/'.join(inside)} is set: this looks like an agent session. A human starts sessions "
                    "from a plain terminal (AGENTS.md section 4)")
    args = list(argv)
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    want = None
    for i, x in enumerate(args):
        if x == "--tier" or x.startswith("--tier="):
            want = x.split("=", 1)[1] if "=" in x else (args[i + 1] if i + 1 < len(args) else "")
            args = args[:i] + args[i + (1 if "=" in x else 2):]
            break
    if want is not None and want not in tier_models():
        raise Usage(f"unknown --tier {want!r}; use one of {', '.join(tier_models())} (pipeline/agent-ops/model-tiers.md)")
    if len(args) < 2:
        raise Usage(USAGE)
    role, card, extra = args[0], args[1], args[2:]
    check_role(role)
    card = norm_card(card)
    tier, model = model_for(role, tier=want)
    if any(a == "--model" or a.startswith("--model=") for a in extra):
        raise Usage(f"--model comes from pipeline/agent-ops/model-tiers.md ({tier}: {model}); do not pass it")
    text = day0_row(card) or (None if dry else gh_card(card))
    prompt = first_prompt(role, card, text, journal_resume(card))
    if os.name == "nt":   # Bypass as ue_run.py does: a Restricted policy or a zip-downloaded copy still runs
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(HERE, "agent.ps1")]
    else:
        cmd = ["sh", os.path.join(HERE, "agent.sh")]
    cmd += [role, card, "claude", "--model", model, *extra, prompt]
    add = {"JAM_ROLE": role, "JAM_CARD": card, "JAM_MODEL": model}
    summary = f"START role={role} card={card} tier={tier} model={model}"
    return cmd, add, summary, dry


def main(argv=None):
    try:
        cmd, add, summary, dry = build(sys.argv[1:] if argv is None else argv)
    except Usage as e:
        print(f"start_session: {e}", file=sys.stderr)
        return 2
    print(summary)
    if dry:
        print(" ".join(f"{k}={shlex.quote(v)}" for k, v in add.items()) + " " + " ".join(shlex.quote(c) for c in cmd))
        return 0
    run_id = record_run(add, cmd[-1])
    rc = subprocess.call(cmd, cwd=ROOT, env=dict(os.environ, **add))
    record_end(run_id, rc)
    return rc


def record_run(add, prompt):
    """The run record (tools/journal.py runs): exact prompt, pipeline version, agent, model, GDD revision."""
    try:
        sys.path.insert(0, HERE)
        import journal
        con = journal.connect()
        try:
            rid = journal.start_run(con, "session", "claude", add["JAM_MODEL"], None,
                                    f"start_session role={add['JAM_ROLE']} card={add['JAM_CARD']}", ROOT)
            journal.add_run_prompt(con, rid, add["JAM_CARD"], add["JAM_ROLE"], add["JAM_MODEL"], prompt)
        finally:
            con.close()
        print(f"RUN #{rid}: pipeline {journal.pipeline_version(ROOT)['string']} | GDD {journal.gdd_revision(ROOT)}")
        return rid
    except Exception as e:  # never block a session on its record
        print(f"start_session: run record not written ({e})", file=sys.stderr)
        return None


def record_end(run_id, rc):
    if run_id is None:
        return
    try:
        import journal
        con = journal.connect()
        try:
            journal.add_run_outcome(con, run_id, "session", exit_code=rc)
            journal.add_run_outcome(con, run_id, "end", outcome="exit", note=f"exit {rc}")
        finally:
            con.close()
    except Exception:
        pass


if __name__ == "__main__":
    sys.exit(main())
