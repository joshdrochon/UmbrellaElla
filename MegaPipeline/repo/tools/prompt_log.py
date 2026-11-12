#!/usr/bin/env python3
"""Read the agent action log that pipeline/agent-ops/hook.py writes to Saved/agent-log/*.jsonl.

Commands:
  summary   one row per card: sessions, roles, tool calls, blocked calls, prompts, tokens
  status    the spend line, then the whole AGENT-OPS line the Producer pastes on the tracker:
            AGENT-OPS day=D secrets=<n> settings=<ok|n> blocked=<n> asked=<n> cap=<...> REVIEW=<cards|none|n/a> stuck=<cards|none>
            secrets = problems from secrets_check rules secret,secretfile,gitignore,mcp; settings = rules settings,agents.
            REVIEW: a card whose tokens (or tool calls when no token totals exist) are more than 2x the
            median card. Needs 3 cards or more. stuck: a card with the same build failure twice.
            Exits 1 when secrets or settings has a problem, a machine passed gates.json daily_token_cap
            (cap=OVER:<host>) or a card is stuck. --strict also exits 1 on REVIEW. --skip-repo skips the two repo checks
  suggest-cap  --sessions-per-day N: the daily_token_cap to write in gates.json, 3x the largest session in
            the log times N. Exits 1 when the log has no token totals (nothing measured)
  blocked   list blocked calls, blocked settings changes and calls that asked a human (ASK: push to main,
            merge, bulk delete, editor Python). --expect TEXT (repeatable) exits 1 unless one of those rows'
            reason or command contains each TEXT (the Day-0 rehearsal proof)
  attempts  --card N: failed tools/ue/build.* calls on that card. Exits 1 when the same failure
            (same error lines, numbers ignored) is in the log twice: AGENTS.md section 6 "Same
            failure twice: stop"
  export    write the day's prompts per card as Markdown, secrets redacted, for prompts/log/.
            --check --day D exits 1 when a host in this log has no prompts/log/D-<host>.md

Usage: python3 tools/prompt_log.py summary|status|blocked|attempts|export|suggest-cap [--log DIR] [--day YYYY-MM-DD] [...]
Exit 0 = fine, 1 = a check failed, 2 = no log found.
"""
import argparse
import glob
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import secrets_check  # noqa: E402

REVIEW_FACTOR = 2.0
MIN_CARDS = 3
SAME_FAILURE_STOP = 2  # AGENTS.md section 6
CAP_HEADROOM = 3  # suggest-cap: 3x the largest measured session
REPO_SECRET_RULES = ["secret", "secretfile", "gitignore", "mcp"]
REPO_CONFIG_RULES = ["settings", "agents"]
PROMPTS_DIR = os.path.join(ROOT, "prompts", "log")
GATES = os.path.join(ROOT, "pipeline", "agent-ops", "gates.json")


def stop_total(r):
    t = r.get("tokens") or {}
    return int(t.get("input", 0)) + int(t.get("output", 0)) + int(t.get("cache_write", 0))


def per_host_day(recs):
    """{(day, host): tokens}. Stop totals are cumulative per session, so the last (largest) one counts."""
    last = {}
    for r in recs:
        if r.get("event") == "stop":
            k = ((r.get("ts") or "")[:10], r.get("host") or "unknown", r.get("session"))
            last[k] = max(stop_total(r), last.get(k, 0))
    out = {}
    for (day, host, _s), total in last.items():
        out[(day, host)] = out.get((day, host), 0) + total
    return out


def cap_field(recs, cap):
    """(text for the status line, over list). No token totals at all -> n/a (the cap cannot be checked)."""
    totals = per_host_day(recs)
    if not cap:
        return "cap=n/a(no daily_token_cap)", []
    if not any(totals.values()):
        return "cap=n/a(no token totals)", []
    over = sorted((k, v) for k, v in totals.items() if v > cap)
    if not over:
        return f"cap=ok(max {max(totals.values()):,}/{cap:,})", []
    return "cap=OVER:" + ",".join(f"{h}@{d} {v:,}/{cap:,}" for (d, h), v in over), over


def load(log_dir, day=None):
    pattern = os.path.join(log_dir, (day or "*") + ".jsonl")
    recs = []
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    recs.append(json.loads(line))
                except ValueError:
                    continue
    return recs


def per_card(recs):
    cards = {}
    stop_tokens = {}  # session -> last cumulative token total (Stop fires many times)
    for r in recs:
        card = r.get("card") or "none"
        c = cards.setdefault(card, {"sessions": set(), "roles": set(), "calls": 0, "blocked": 0, "prompts": 0, "tokens": 0})
        if r.get("session"):
            c["sessions"].add(r["session"])
        if r.get("role"):
            c["roles"].add(r["role"])
        ev = r.get("event")
        if ev == "tool":
            c["calls"] += 1
        elif ev == "blocked":
            c["blocked"] += 1
        elif ev == "prompt":
            c["prompts"] += 1
        elif ev == "stop":
            total = stop_total(r)
            stop_tokens[(card, r.get("session"))] = max(total, stop_tokens.get((card, r.get("session")), 0))
    for (card, _s), total in stop_tokens.items():
        cards[card]["tokens"] += total
    return cards


def flagged(cards):
    """Cards over REVIEW_FACTOR x the median. Uses tokens if any card has them, else tool calls."""
    real = {k: v for k, v in cards.items() if k != "none"}
    if len(real) < MIN_CARDS:
        return "calls", None, []
    metric = "tokens" if any(v["tokens"] for v in real.values()) else "calls"
    med = statistics.median(v[metric] for v in real.values())
    if med <= 0:
        return metric, med, []
    over = sorted(((k, v[metric] / med) for k, v in real.items() if v[metric] > REVIEW_FACTOR * med), key=lambda x: -x[1])
    return metric, med, over


def cmd_summary(cards):
    print("card | sessions | roles | calls | blocked | prompts | tokens")
    for k in sorted(cards):
        v = cards[k]
        print(f"{k} | {len(v['sessions'])} | {', '.join(sorted(v['roles'])) or '-'} | {v['calls']} | {v['blocked']} | {v['prompts']} | {v['tokens']}")
    return 0


def stuck_cards(recs):
    """Cards whose log holds the same build failure SAME_FAILURE_STOP times or more."""
    counts = {}
    for r in recs:
        if r.get("build") and not r.get("build_ok"):
            k = (str(r.get("card") or "none"), r.get("error_sha256"))
            counts[k] = counts.get(k, 0) + 1
    return sorted({c for (c, _e), n in counts.items() if n >= SAME_FAILURE_STOP})


def repo_fields(root):
    """(secrets problem count, settings problem count, problem lines) from tools/secrets_check.py."""
    sec = secrets_check.run(root, REPO_SECRET_RULES)
    conf = secrets_check.run(root, REPO_CONFIG_RULES)
    return len(sec), len(conf), [f"[{k}] {w}: {m}" for k, w, m in sec + conf]


def cmd_status(cards, day, strict, recs=(), cap=None, root=None):
    metric, med, over = flagged(cards)
    blocked = sum(v["blocked"] for v in cards.values())
    asked = sum(1 for r in recs if r.get("event") == "ask")
    cap_text, cap_over = cap_field(recs, cap)
    if cap_over:
        print(f"CAP: a machine passed daily_token_cap ({cap:,} tokens). It starts no new agent session today until the Producer human posts OK on the tracker.")
    n_cards = len([k for k in cards if k != "none"])
    if med is None:
        review = "n/a"
        print(f"spend day={day or 'all'} cards={n_cards} blocked={blocked} {cap_text} review=n/a (fewer than {MIN_CARDS} cards)")
    else:
        review = ",".join(f"#{k}" for k, _x in over) or "none"
        flags = ", ".join(f"#{k} {x:.1f}x" for k, x in over) or "none"
        print(f"spend day={day or 'all'} cards={n_cards} median_{metric}={med:g} blocked={blocked} {cap_text} REVIEW(>{REVIEW_FACTOR:g}x median): {flags}")
    stuck = stuck_cards(recs)
    if root:
        n_sec, n_conf, lines = repo_fields(root)
        for ln in lines:
            print(ln)
        sec_text, conf_text = str(n_sec), ("ok" if not n_conf else str(n_conf))
    else:
        n_sec = n_conf = 0
        sec_text = conf_text = "skipped"
    print(f"AGENT-OPS day={day or 'all'} secrets={sec_text} settings={conf_text} blocked={blocked} asked={asked} {cap_text} "
          f"REVIEW={review} stuck={','.join('#' + c for c in stuck) or 'none'}")
    return 1 if (cap_over or stuck or n_sec or n_conf or (strict and over)) else 0


def cmd_suggest_cap(recs, sessions_per_day):
    """3x the largest measured session times the sessions one machine runs per day."""
    per_session = {}
    for r in recs:
        if r.get("event") == "stop":
            k = r.get("session")
            per_session[k] = max(stop_total(r), per_session.get(k, 0))
    measured = {k: v for k, v in per_session.items() if v > 0}
    if not measured:
        print("suggest-cap: no session in the log has token totals; run one real card session first ([VERIFY on 0.18] usage fields)")
        return 1
    top = max(measured.values())
    cap = CAP_HEADROOM * top * sessions_per_day
    print(f"suggest-cap sessions={len(measured)} max_session_tokens={top} sessions_per_day={sessions_per_day} "
          f"headroom={CAP_HEADROOM}x daily_token_cap={cap}")
    return 0


def load_cap(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return int(json.load(fh).get("daily_token_cap") or 0) or None
    except (OSError, ValueError, TypeError):
        return None


def cmd_blocked(recs, expect):
    rows = [r for r in recs if r.get("event") == "blocked"]
    rows += [dict(r, tool="ConfigChange", reason=f"settings change blocked ({r.get('source')})", command=r.get("file_path"))
             for r in recs if r.get("event") == "config" and r.get("blocked")]
    asks = [r for r in recs if r.get("event") == "ask"]
    for r in rows + asks:
        tag = "ASK " if r.get("event") == "ask" else ""
        print(f"{tag}{r.get('ts')} card={r.get('card') or '-'} role={r.get('role') or '-'} tool={r.get('tool')} :: {r.get('reason')}")
    missing = [e for e in (expect or []) if not any(e in (r.get("reason") or "") + " " + str(r.get("command") or "") for r in rows + asks)]
    for e in missing:
        print(f"MISSING: no blocked or asked call mentions '{e}'")
    print(f"blocked: {len(rows)} call(s), asked: {len(asks)} call(s)")
    return 1 if missing else 0


def cmd_attempts(recs, card):
    builds = [r for r in recs if r.get("build") and str(r.get("card")) == str(card)]
    failed = [r for r in builds if not r.get("build_ok")]
    counts = {}
    for r in failed:
        counts[r.get("error_sha256")] = counts.get(r.get("error_sha256"), 0) + 1
    same = max(counts.values()) if counts else 0
    print(f"attempts card={card} builds={len(builds)} failed={len(failed)} same_failure_max={same}")
    if same >= SAME_FAILURE_STOP:
        print(f"STOP: the same build failure is in the log {same} times. Set the card blocked (AGENTS.md section 6).")
        return 1
    return 0


def cmd_export_check(recs, day, prompts_dir):
    hosts = sorted({r.get("host") for r in recs if r.get("host")})
    no_host = sum(1 for r in recs if not r.get("host"))
    missing = [h for h in hosts if not os.path.exists(os.path.join(prompts_dir, f"{day}-{h}.md"))]
    for h in missing:
        print(f"MISSING: prompts/log/{day}-{h}.md (host {h} ran agents on {day})")
    if no_host:
        print(f"MISSING: {no_host} record(s) have no host; the hook is older than the template")
    print(f"export check day={day} hosts={len(hosts)} missing={len(missing)}")
    return 1 if (missing or no_host) else 0


def cmd_export(recs, day, out):
    lines = [f"# Agent prompts {day or 'all days'}", "", "Exported by `tools/prompt_log.py export`. Secrets redacted by `tools/secrets_check.py`.", ""]
    by_card = {}
    for r in recs:
        if r.get("event") == "prompt":
            by_card.setdefault(r.get("card") or "none", []).append(r)
    for card in sorted(by_card):
        lines += [f"## Card {card}", ""]
        for r in by_card[card]:
            text = secrets_check.redact(r.get("prompt") or "").strip()
            lines += [f"- {r.get('ts')} role={r.get('role') or '-'} session={str(r.get('session') or '-')[:8]}", "", "```text", text.replace("```", "'''"), "```", ""]
    body = "\n".join(lines)
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"wrote {out}: {sum(len(v) for v in by_card.values())} prompt(s)")
    else:
        sys.stdout.write(body)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["summary", "status", "blocked", "attempts", "export", "suggest-cap"])
    ap.add_argument("--log", default=os.path.join(ROOT, "Saved", "agent-log"))
    ap.add_argument("--day", help="YYYY-MM-DD (default: every day in the log)")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--expect", action="append")
    ap.add_argument("--out")
    ap.add_argument("--card", help="attempts: the card number, e.g. 12 or 0.4a")
    ap.add_argument("--check", action="store_true", help="export: check the files exist instead of writing")
    ap.add_argument("--prompts", default=PROMPTS_DIR, help="export --check: folder of exports")
    ap.add_argument("--gates", default=GATES, help="status: gates.json with daily_token_cap")
    ap.add_argument("--root", default=ROOT, help="status: repo to run secrets_check on")
    ap.add_argument("--skip-repo", action="store_true", help="status: skip the secrets and settings checks")
    ap.add_argument("--sessions-per-day", type=int, help="suggest-cap: agent sessions one machine runs per day")
    a = ap.parse_args(argv)
    if a.command == "attempts" and not a.card:
        ap.error("attempts needs --card")
    if a.check and not a.day:
        ap.error("export --check needs --day")
    if a.command == "suggest-cap" and not (a.sessions_per_day and a.sessions_per_day > 0):
        ap.error("suggest-cap needs --sessions-per-day N (N >= 1)")
    recs = load(a.log, a.day)
    if not recs:
        print(f"prompt_log: no records in {a.log} for day={a.day or 'all'}")
        return 2
    if a.command == "summary":
        return cmd_summary(per_card(recs))
    if a.command == "status":
        return cmd_status(per_card(recs), a.day, a.strict, recs, load_cap(a.gates), None if a.skip_repo else a.root)
    if a.command == "blocked":
        return cmd_blocked(recs, a.expect)
    if a.command == "attempts":
        return cmd_attempts(recs, a.card)
    if a.command == "suggest-cap":
        return cmd_suggest_cap(recs, a.sessions_per_day)
    if a.check:
        return cmd_export_check(recs, a.day, a.prompts)
    return cmd_export(recs, a.day, a.out)


if __name__ == "__main__":
    sys.exit(main())
