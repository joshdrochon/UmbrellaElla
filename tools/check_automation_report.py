#!/usr/bin/env python3
"""Read Unreal's automation report (Saved/Automation/index.json) and decide pass/fail.

The editor's exit code alone does not prove tests ran. This fails when:
  - the report is missing or unreadable
  - zero tests ran
  - only placeholder tests ran (`UmbrellaElla.Bootstrap.*`) or no `UmbrellaElla.` test ran at all
  - any test failed, or any test did not run (state other than Success)
  - fewer tests ran than the baseline (tests were deleted or not discovered)
  - a test name required by the task card is absent (--require UmbrellaElla.Umbrella.OpenRises)
  - a test name from a `merged` row of pipeline/qa/test-map.md is absent (--test-map FILE). Rows still
    `planned` are not required, so the daily build does not go red for tests no merged card has made yet.
    A test-map row with an unknown Status, or `merged` without a `#<n>` Card, fails too.
  - a rule test took longer than --max-rule-seconds (default 1.0; 0 = off). A rule test is any `UmbrellaElla.`
    test without a `.World.` name segment and not marked `(world)` in the test map (--test-map FILE, or
    --world-map FILE for the marks alone, which test.sh / test.ps1 pass by default: final-10 A H4; the
    marker counts on every row, planned or merged, because a planned test that exists is still timed). It reads each test's `duration` (seconds) [VERIFY field on 5.8.4]
    and always prints the total suite time and the slowest test. While the limit is on, a rule test with no
    `duration` fails too: a missing measurement never counts as a pass.
--list-test-map FILE prints the required names of merged rows, one per line (for the gate isolation loop).

--bootstrap is for Day-0 card 0.3 only (pipeline/day0-cards.md): the skeleton has no gameplay tests yet,
so its run passes when at least one test ran, every test passed, and none is a real `UmbrellaElla.` test
(only the placeholder `UmbrellaElla.Bootstrap.*` or engine smoke tests). It refuses --baseline/--require/--test-map, and it fails as soon as a real
`UmbrellaElla.` test exists, so it cannot be used to skip checks later. "Zero tests" fails in both modes.

The result line names the commit it ran on (`PASS  tests=<n> failed=0  commit=<sha>`; --commit, default the repo's
HEAD), so tools/check_pr.py can tell a line from an earlier push (final-7 dry run B H7).

Usage: python3 tools/check_automation_report.py Saved/Automation/index.json [--baseline N] [--require NAME ...]
                                                [--test-map pipeline/qa/test-map.md] [--bootstrap] [--max-rule-seconds S]
       python3 tools/check_automation_report.py --list-test-map pipeline/qa/test-map.md
Exit 0 = pass, 1 = fail, 2 = report missing/unreadable or bad arguments.
"""
import argparse
import json
import os
import re
import sys

PROJECT = "UmbrellaElla."
BOOTSTRAP = "UmbrellaElla.Bootstrap."
STATUSES = ("planned", "merged")
MAX_RULE_SECONDS = 1.0


def name_of(t):
    return t.get("fullTestPath") or t.get("testDisplayName") or ""


def is_bootstrap(n):
    return n.startswith(BOOTSTRAP) or ("." + BOOTSTRAP) in n


def is_project(n):
    return (n.startswith(PROJECT) or ("." + PROJECT) in n) and not is_bootstrap(n)


def is_world(n, world=()):
    return ".World." in n or any(n == w or n.endswith("." + w) for w in world)


def duration_of(t):
    try:
        return float(t.get("duration"))
    except (TypeError, ValueError):
        return None


TEST_NAME = r"UmbrellaElla(?:\.\w+){2,}"
WORLD_MARK = re.compile(r"`?(" + TEST_NAME + r")`?\s*\(world\)")


def test_map_world(text):
    """Names marked `(world)` anywhere in the test-map table: held to no rule-test time limit."""
    return [n for ln in text.splitlines() if ln.strip().startswith("|") for n in WORLD_MARK.findall(ln)]


def test_map_requirements(text):
    """Return (required names from merged rows, problems) from pipeline/qa/test-map.md text."""
    names, problems, header = [], [], None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        row = dict(zip(header, cells))
        if "status" not in row or "required tests" not in row:
            problems.append("test-map table needs 'Required tests', 'Card' and 'Status' columns")
            break
        status = row["status"].strip("` ").lower()
        tests = re.findall(TEST_NAME, row["required tests"])
        if status not in STATUSES:
            problems.append(f"test-map row {row.get('qa', row.get('mvp', '?'))}: Status '{row['status']}' is not planned or merged")
            continue
        if status == "merged":
            if not re.search(r"#\d+", row.get("card", "")):
                problems.append(f"test-map row {row.get('qa', row.get('mvp', '?'))}: Status merged but no '#<issue>' in the Card column")
            names += tests
    if header is None:
        problems.append("test-map has no table")
    return names, problems


def evaluate(report, baseline=0, required=(), bootstrap=False, max_rule_seconds=0, world=()):
    tests = report.get("tests", []) or []
    names = {name_of(t) for t in tests}
    failed = [name_of(t) for t in tests if str(t.get("state", "")).lower() in ("fail", "failed", "error")]
    not_run = [name_of(t) for t in tests
               if str(t.get("state", "")).lower() not in ("success", "fail", "failed", "error")]
    failed_count = max(int(report.get("failed", 0) or 0), len(failed))
    total = len(tests)
    project = [n for n in names if is_project(n)]
    problems = []
    if total == 0:
        problems.append("no tests ran")
    elif bootstrap:
        if project:
            problems.append(f"--bootstrap is for card 0.3 only, but {len(project)} UmbrellaElla test(s) exist "
                            f"(e.g. {sorted(project)[0]}); drop the flag")
        if baseline or required:
            problems.append("--bootstrap takes no --baseline, --require or --test-map")
    elif not project:
        problems.append(f"no UmbrellaElla gameplay test ran ({total} placeholder or engine test(s) only); "
                        "only card 0.3 may pass this way, with --bootstrap")
    if failed_count:
        problems.append(f"{failed_count} test(s) failed: {', '.join(n for n in failed if n)[:500]}")
    if not_run or int(report.get("notRun", 0) or 0):
        problems.append(f"{max(len(not_run), int(report.get('notRun', 0) or 0))} test(s) did not run: {', '.join(n for n in not_run if n)[:300]}")
    if total < baseline:
        problems.append(f"{total} tests ran, baseline is {baseline}")
    for r in required:
        if not any(n and (n == r or n.endswith("." + r)) for n in names):
            problems.append(f"required test not found: {r}")
    timed = [(duration_of(t), name_of(t)) for t in tests if duration_of(t) is not None]
    if max_rule_seconds:
        slow = sorted((d, n) for d, n in timed if is_project(n) and not is_world(n, world) and d > max_rule_seconds)
        if slow:
            problems.append(f"{len(slow)} rule test(s) over {max_rule_seconds:g} s: "
                            + ", ".join(f"{n} ({d:.2f} s)" for d, n in reversed(slow))[:500])
        untimed = sorted(name_of(t) for t in tests
                         if duration_of(t) is None and is_project(name_of(t)) and not is_world(name_of(t), world))
        if untimed:
            problems.append(f"{len(untimed)} rule test(s) have no duration in the report, so the "
                            f"{max_rule_seconds:g} s limit checked nothing (pass --max-rule-seconds 0 to turn it off "
                            f"on purpose): {', '.join(untimed)[:300]} [VERIFY field name on 5.8.4]")
    return {"total": total, "failed": failed_count, "problems": problems, "pass": not problems,
            "bootstrap": bootstrap, "seconds": sum(d for d, _ in timed), "timed": len(timed),
            "slowest": max(timed) if timed else None}


def head_commit():
    import subprocess
    try:
        p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           capture_output=True, text=True)
    except OSError:
        return "unknown"
    return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("report", nargs="?")
    ap.add_argument("--baseline", type=int, default=0)
    ap.add_argument("--require", nargs="*", default=[])
    ap.add_argument("--test-map", help="pipeline/qa/test-map.md: require the tests of every merged row")
    ap.add_argument("--bootstrap", action="store_true", help="Day-0 card 0.3 only: placeholder tests pass")
    ap.add_argument("--world-map", metavar="FILE", help="read only the (world) marks of this test map: the 1 s rule "
                    "then knows the same world tests test.sh, the daily and the test map know (final-10 A H4). "
                    "test.sh / test.ps1 pass pipeline/qa/test-map.md by default")
    ap.add_argument("--max-rule-seconds", type=float, default=MAX_RULE_SECONDS,
                    help="fail a rule test (no .World. segment, no (world) mark in --test-map) slower than this; 0 = off")
    ap.add_argument("--list-test-map", metavar="FILE", help="print the required names of merged rows and exit")
    ap.add_argument("--commit", help="commit the tests ran on (default: git HEAD of this repo)")
    a = ap.parse_args(argv)
    if a.list_test_map:
        try:
            with open(a.list_test_map, encoding="utf-8") as fh:
                names, problems = test_map_requirements(fh.read())
        except OSError as e:
            print(f"FAIL test map unreadable: {e}", file=sys.stderr)
            return 2
        for n in names:
            print(n)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1 if problems else 0
    if not a.report:
        ap.error("the report path is required")
    required = list(a.require)
    map_problems, world = [], []
    if a.test_map:
        try:
            with open(a.test_map, encoding="utf-8") as fh:
                text = fh.read()
                names, map_problems = test_map_requirements(text)
                world = test_map_world(text)
        except OSError as e:
            print(f"FAIL test map unreadable: {e}")
            return 2
        required += [n for n in names if n not in required]
        print(f"test-map: {len(names)} required test name(s) from merged rows, {len(world)} marked (world)")
    if a.world_map and not a.test_map:
        try:
            with open(a.world_map, encoding="utf-8") as fh:
                world = test_map_world(fh.read())
        except OSError:
            world = []   # no test map yet: only `.World.` names are world tests
    try:
        with open(a.report, encoding="utf-8-sig") as fh:
            report = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL report missing or unreadable: {e}")
        return 2
    r = evaluate(report, a.baseline, required, a.bootstrap, a.max_rule_seconds, world)
    if a.bootstrap and a.test_map and "--bootstrap takes no --baseline, --require or --test-map" not in r["problems"]:
        r["problems"].append("--bootstrap takes no --baseline, --require or --test-map")
    r["problems"] += map_problems
    r["pass"] = not r["problems"]
    label = " (bootstrap: placeholder tests only, card 0.3)" if a.bootstrap else ""
    commit = a.commit or head_commit()
    print(("PASS" if r["pass"] else "FAIL") + f"  tests={r['total']} failed={r['failed']}  commit={commit}" + label)
    if r["timed"]:
        d, n = r["slowest"]
        print(f"  time: suite {r['seconds']:.1f} s over {r['timed']} test(s); slowest {n} ({d:.2f} s)")
    elif r["total"]:
        print("  time: no test has a duration in the report [VERIFY field name on 5.8.4]")
    for p in r["problems"]:
        print("  - " + p)
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
