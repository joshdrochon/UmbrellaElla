#!/usr/bin/env python3
"""Spend log: one row per agent session with its tokens and cost, by role and card. Stdlib only.

Rows go to .pipeline/spend.csv (git-ignored; SPEND_CSV overrides the path and SPEND_AGENT_LOG the agent log
directory, for tests). Prices are USD per million
tokens from pipeline/agent-ops/model-prices.json (SPEND_PRICES overrides). A price the file lists as provisional
makes that row's cost provisional; summary prints it with a leading ~.

Sessions log it at handoff: tools/agent.sh and agent.ps1 run `log --from-agent-log` after the agent CLI exits,
which reads the Stop records pipeline/agent-ops/hook.py writes to Saved/agent-log/*.jsonl (cumulative per
session: the largest total counts). A session already in the CSV is not logged twice.

Commands:
  log      --role R --card C --model M [--session S] [--input N --output N --cache-read N --cache-write N]
           [--note "..."]   one row. --model must be a key of the prices file, or `unknown` (no cost)
  log      --from-agent-log [--log DIR] [--since ISO] [--session S] --role R --card C --model M
           one row per session in the agent log (Stop records at or after --since, for that session if given)
  summary  [--by role|card|day]   sessions, tokens and USD per group, then a total line (all three groups when
           --by is not given)

Role, card and model default to $JAM_ROLE, $JAM_CARD, $JAM_MODEL. Notes and session IDs are redacted with the
secret patterns in tools/secrets_check.py before they are stored.
Exit 0 = ok, 1 = nothing to log (no Stop record found), 2 = usage error, bad number, unknown model, bad CSV row.
"""
import argparse
import csv
import datetime as dt
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from secrets_check import redact  # noqa: E402
from journal import norm_card  # noqa: E402

PRICES = os.path.join(ROOT, "pipeline", "agent-ops", "model-prices.json")
GATES = os.path.join(ROOT, "pipeline", "agent-ops", "gates.json")
COLUMNS = ["utc", "day", "session", "role", "card", "model", "input", "output", "cache_read", "cache_write",
           "usd", "provisional", "note"]
TOKEN_FIELDS = ["input", "output", "cache_read", "cache_write"]
CARD_OK = re.compile(r"^(UE-\d+(?:\.\d+)?[a-z]?|#\d+)$")
UNKNOWN = "unknown"


class Usage(Exception):
    pass


def csv_path():
    return os.environ.get("SPEND_CSV") or os.path.join(ROOT, ".pipeline", "spend.csv")


def load_prices(path=None):
    with open(path or os.environ.get("SPEND_PRICES") or PRICES, encoding="utf-8") as fh:
        return json.load(fh)["models"]


def roles():
    try:
        with open(GATES, encoding="utf-8") as fh:
            return set(json.load(fh)["roles"])
    except (OSError, ValueError, KeyError):
        return None


def tokens_of(value, name):
    try:
        n = int(str(value))
    except (TypeError, ValueError):
        raise Usage(f"{name} must be a whole number of tokens, got {value!r}")
    if n < 0:
        raise Usage(f"{name} must not be negative, got {n}")
    return n


def cost(model, toks, prices):
    """(usd or None, provisional) for one row."""
    if model == UNKNOWN:
        return None, False
    p = prices[model]
    prov = set(p.get("provisional") or [])
    usd = sum(toks[f] * float(p[f]) for f in TOKEN_FIELDS) / 1e6
    return round(usd, 6), any(toks[f] and f in prov for f in TOKEN_FIELDS)


def check_ident(role, card, model, prices):
    if not role:
        raise Usage("no role: pass --role or set JAM_ROLE")
    known = roles()
    if known is not None and role not in known:
        raise Usage(f"unknown role {role!r}; use a key of roles in pipeline/agent-ops/gates.json")
    card = norm_card(card)
    if not CARD_OK.match(card):
        raise Usage(f"bad card {card or '(none)'!r}: pass --card UE-<id> or #<issue>, or set JAM_CARD")
    if not model:
        raise Usage("no model: pass --model or set JAM_MODEL (use 'unknown' if it is not known)")
    if model != UNKNOWN and model not in prices:
        raise Usage(f"unknown model {model!r}; known: {', '.join(sorted(prices))} or 'unknown'")
    return card


def read_rows(path):
    """All rows; a malformed row raises Usage with its line number."""
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.reader(fh)
        header = next(r, None)
        if header != COLUMNS:
            raise Usage(f"{path}: header is not {','.join(COLUMNS)}")
        for i, row in enumerate(r, start=2):
            if not row:
                continue
            if len(row) != len(COLUMNS):
                raise Usage(f"{path} line {i}: {len(row)} fields, expected {len(COLUMNS)}")
            rec = dict(zip(COLUMNS, row))
            try:
                for f in TOKEN_FIELDS:
                    rec[f] = tokens_of(rec[f], f)
                rec["usd"] = None if rec["usd"] == "" else float(rec["usd"])
            except (Usage, ValueError) as e:
                raise Usage(f"{path} line {i}: {e}")
            if rec["provisional"] not in ("yes", "no"):
                raise Usage(f"{path} line {i}: provisional must be yes or no")
            out.append(rec)
    return out


def append_row(path, rec):
    new = not os.path.isfile(path) or os.path.getsize(path) == 0
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(COLUMNS)
        w.writerow([rec[c] for c in COLUMNS])


def make_row(role, card, model, session, toks, note, prices, utc=None):
    usd, prov = cost(model, toks, prices)
    utc = utc or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    return {"utc": utc, "day": utc[:10], "session": redact(session or ""), "role": role, "card": card,
            "model": model, **toks, "usd": "" if usd is None else f"{usd:.6f}",
            "provisional": "yes" if prov else "no", "note": redact(note or "")}


def agent_log_sessions(log_dir, since=None, session=None):
    """{session: (ts, tokens)} from Stop records; the largest cumulative total per session."""
    best = {}
    for path in sorted(glob.glob(os.path.join(log_dir, "*.jsonl"))):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("event") != "stop" or not isinstance(r.get("tokens"), dict):
                    continue
                if since and (r.get("ts") or "") < since:
                    continue
                sid = r.get("session") or ""
                if session and sid != session:
                    continue
                t = {f: int(r["tokens"].get(f) or 0) for f in TOKEN_FIELDS}
                total = t["input"] + t["output"] + t["cache_write"]
                if sid not in best or total >= sum(best[sid][1][f] for f in ("input", "output", "cache_write")):
                    best[sid] = (r.get("ts"), t)
    return best


def do_log(a):
    prices = load_prices()
    role = a.role or os.environ.get("JAM_ROLE") or ""
    card = check_ident(role, a.card or os.environ.get("JAM_CARD") or "",
                       a.model or os.environ.get("JAM_MODEL") or "", prices)
    model = a.model or os.environ.get("JAM_MODEL")
    path = csv_path()
    have = {r["session"] for r in read_rows(path) if r["session"]}
    if a.from_agent_log:
        log_dir = a.log or os.environ.get("SPEND_AGENT_LOG") or os.path.join(ROOT, "Saved", "agent-log")
        found = agent_log_sessions(log_dir, a.since, a.session)
        if not found:
            print("spend_log: no Stop record in the agent log for this session; nothing logged", file=sys.stderr)
            return 1
        n = 0
        for sid, (_ts, toks) in sorted(found.items()):
            if redact(sid) in have:
                print(f"spend_log: session {sid} already logged; skipped")
                continue
            rec = make_row(role, card, model, sid, toks, a.note, prices)
            append_row(path, rec)
            print(line_for(rec))
            n += 1
        return 0
    toks = {f: tokens_of(getattr(a, f), "--" + f.replace("_", "-")) for f in TOKEN_FIELDS}
    if a.session and redact(a.session) in have:
        print(f"spend_log: session {a.session} already logged; skipped")
        return 0
    rec = make_row(role, card, model, a.session, toks, a.note, prices)
    append_row(path, rec)
    print(line_for(rec))
    return 0


def fmt_usd(usd, prov, unknown=False):
    s = f"{'~' if prov else ''}${usd:.2f}"
    return s + (" (+unpriced)" if unknown else "")


def line_for(rec):
    toks = sum(int(rec[f]) for f in TOKEN_FIELDS)
    usd = "unpriced" if rec["usd"] == "" else fmt_usd(float(rec["usd"]), rec["provisional"] == "yes")
    return f"SPEND role={rec['role']} card={rec['card']} model={rec['model']} tokens={toks} usd={usd}"


def summarize(rows, by):
    groups = {}
    for r in rows:
        g = groups.setdefault(r[by], {"sessions": 0, "tokens": 0, "usd": 0.0, "prov": False, "unpriced": False})
        g["sessions"] += 1
        g["tokens"] += sum(r[f] for f in TOKEN_FIELDS)
        if r["usd"] is None:
            g["unpriced"] = True
        else:
            g["usd"] += r["usd"]
        g["prov"] = g["prov"] or r["provisional"] == "yes"
    return groups


def do_summary(a):
    rows = read_rows(csv_path())
    if not rows:
        print("spend_log: no sessions logged")
        return 0
    for by in [a.by] if a.by else ["role", "card", "day"]:
        print(f"## by {by}")
        for k, g in sorted(summarize(rows, by).items()):
            print(f"{by}={k} sessions={g['sessions']} tokens={g['tokens']} "
                  f"usd={fmt_usd(g['usd'], g['prov'], g['unpriced'])}")
    t = summarize(rows, "model")
    tot_usd = sum(g["usd"] for g in t.values())
    prov = any(g["prov"] for g in t.values())
    unpriced = any(g["unpriced"] for g in t.values())
    print(f"TOTAL sessions={len(rows)} tokens={sum(g['tokens'] for g in t.values())} "
          f"usd={fmt_usd(tot_usd, prov, unpriced)}")
    return 0


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    lg = sub.add_parser("log")
    lg.add_argument("--role")
    lg.add_argument("--card")
    lg.add_argument("--model")
    lg.add_argument("--session")
    lg.add_argument("--note")
    for f in TOKEN_FIELDS:
        lg.add_argument("--" + f.replace("_", "-"), dest=f, default="0")
    lg.add_argument("--from-agent-log", action="store_true")
    lg.add_argument("--log")
    lg.add_argument("--since")
    sm = sub.add_parser("summary")
    sm.add_argument("--by", choices=["role", "card", "day"])
    return p


def main(argv=None):
    try:
        a = parser().parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        return do_log(a) if a.cmd == "log" else do_summary(a)
    except Usage as e:
        print(f"spend_log: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
