#!/usr/bin/env python3
"""Claude Code hooks that keep tools/journal.py up to date, so an agent that never reads AGENTS.md still
leaves an exact local record. Stdlib only. Wired by pipeline/agent-ops/settings.json:

  session-start  SessionStart. Prints `journal.py resume` for $JAM_CARD (stdout becomes session context).
                 No JAM_CARD: prints a WARNING and falls back to the ue-<id>- branch name.
  bash           PostToolUse and PostToolUseFailure on Bash. Records the command as a step: exit 0 on
                 PostToolUse, the "Exit code N" in the error on PostToolUseFailure (1 if none), and the last
                 40 lines of stdout+stderr (redacted). Commands that call journal.py are skipped (they journal
                 themselves). [VERIFY on 0.18: Bash tool_response fields stdout / stderr]
  stop           Stop. Writes a checkpoint that carries the last note and next step forward, only when steps
                 were recorded since the last checkpoint.

Never blocks: always exits 0, whatever goes wrong.
Usage: python3 pipeline/agent-ops/journal_hook.py session-start|bash|stop   (hook JSON on stdin)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools")


def load():
    sys.path.insert(0, TOOLS)
    import journal  # noqa: E402
    return journal


def read_input():
    try:
        data = json.loads(sys.stdin.read() or "{}")
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


def exit_code(data):
    import re
    if data.get("hook_event_name") != "PostToolUseFailure" and not data.get("error"):
        resp = data.get("tool_response")
        if isinstance(resp, dict):
            for k in ("exit_code", "exitCode", "returnCode"):
                if isinstance(resp.get(k), int):
                    return resp[k]
        return 0
    m = re.search(r"[Ee]xit code (-?\d+)", str(data.get("error") or ""))
    return int(m.group(1)) if m else 1


def output_of(data):
    resp = data.get("tool_response")
    if isinstance(resp, dict):
        text = "\n".join(str(resp.get(k) or "") for k in ("stdout", "stderr") if resp.get(k))
    else:
        text = str(resp or "")
    if data.get("error"):
        text = (text + "\n" + str(data["error"])).strip()
    return text


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    data = read_input()
    j = load()
    card = j.norm_card(os.environ.get("JAM_CARD") or "")
    if not card:
        card = j.resolve_card(None)
        if mode == "session-start":
            print("WARNING: JAM_CARD is not set, so the journal does not know your card. Start agents with "
                  "tools/agent.sh <role> <card> <cli> (tools\\agent.ps1 on Windows)."
                  + (f" Using {card} from the branch name." if card else ""))
    if not card:
        return 0
    con = j.connect()
    try:
        if mode == "session-start":
            print(j.resume_text(con, card, j.db_path(), j.git("rev-parse", "HEAD"),
                                j.git("rev-parse", "--abbrev-ref", "HEAD")))
        elif mode == "bash":
            cmd = ((data.get("tool_input") or {}).get("command") or "").strip()
            if cmd and "journal.py" not in cmd:
                j.add(con, card, "step", command=cmd, exit_code=exit_code(data), output_tail=j.tail(output_of(data)),
                      note="hook")
        elif mode == "stop":
            evs = j.events(con, card)
            mark = j.last_mark(evs)
            since = [e for e in evs if e["kind"] == "step" and (mark is None or e["id"] > mark["id"])]
            if since:
                prev = (mark or {}).get("note") or ""
                if prev.startswith("auto (Stop hook"):
                    prev = prev.split("last note: ", 1)[-1]
                j.add(con, card, "checkpoint", note=f"auto (Stop hook, {len(since)} steps); last note: {prev}"[:500],
                      next_step=j.last_value(con, card, "next_step"))
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    try:
        main(sys.argv)
    except Exception as e:  # a journal problem must never block the agent
        print(f"journal_hook: {e}", file=sys.stderr)
    sys.exit(0)
