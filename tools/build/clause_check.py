#!/usr/bin/env python3
"""clause_check (Nov 13, Josh): a merge may set a docs/build/rule-status.csv row to `built` only when every GDD clause of
that rule is proven. Proof lives in docs/build/clause-proof.csv (rule, clause, proof): each clause names either a test
(`test:UmbrellaElla.Area.Name` for an automation test in Source, `py:tests/test_x.py` for a Python test file) or a GDD
number binding (`gdd:<key>` in docs/build/gdd-bindings.json, which gdd_check measures). Every clause the audit listed for
that rule in docs/build/clause-audit.csv must appear in clause-proof.csv with a proof that exists.

The rows already `built` on the base are the baseline (Josh: the team count stays at 150); the check applies only to
rows that become `built` in this merge. Tests named here must also pass: the gate's own test run fails the merge
otherwise, and an automation test named in a proof must be one this tree defines.

  clause_check.py BASE    exit 0 = pass, 1 = fail (prints `clause_check: FAIL <rule>: <why>` lines)"""
import csv, io, json, os, re, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STATUS, AUDIT, PROOF, BINDINGS = ("docs/build/rule-status.csv", "docs/build/clause-audit.csv",
                                  "docs/build/clause-proof.csv", "docs/build/gdd-bindings.json")


def read_csv(text):
    return list(csv.DictReader(io.StringIO(text or "")))


def at(root, ref, path):
    if ref is None:
        p = os.path.join(root, path)
        return open(p, encoding="utf-8").read() if os.path.isfile(p) else ""
    return subprocess.run(["git", "-C", root, "show", f"{ref}:{path}"], capture_output=True, text=True).stdout


def automation_tests(root):
    names = set()
    for d, _, fs in os.walk(os.path.join(root, "Source")):
        for f in fs:
            if f.endswith(".cpp"):
                try:
                    names.update(re.findall(r'AUTOMATION_TEST\(\s*\w+\s*,\s*"([^"]+)"', open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()))
                except OSError:
                    pass
    return names


def proof_problem(root, proof, tests, bindings):
    kind, _, name = proof.partition(":")
    name = name.strip()
    if kind == "test":
        return None if name in tests else f"test {name} is not defined in Source"
    if kind == "py":
        return None if os.path.isfile(os.path.join(root, name)) else f"python test {name} does not exist"
    if kind == "gdd":
        return None if name in bindings else f"gdd binding {name} is not in {BINDINGS}"
    return f"proof '{proof}' is not test:/py:/gdd:"


def check(root, base):
    old = {r["id"]: r for r in read_csv(at(root, base, STATUS))}
    new = {r["id"]: r for r in read_csv(at(root, None, STATUS))}
    became = [i for i, r in new.items() if (r.get("status") or "").strip() == "built"
              and (old.get(i, {}).get("status") or "").strip() != "built"]
    if not became:
        return []
    audit = read_csv(at(root, None, AUDIT))
    proof = read_csv(at(root, None, PROOF))
    try:
        bindings = set(json.loads(at(root, None, BINDINGS) or "{}"))
    except ValueError:
        bindings = set()
    tests = automation_tests(root)
    out = []
    for rid in sorted(became):
        mine = [p for p in proof if p.get("rule") == rid]
        if not mine:
            out.append(f"clause_check: FAIL {rid}: set to built but has no clause proof in {PROOF}")
            continue
        proven = {(p.get("clause") or "").strip() for p in mine}
        for a in audit:
            if a.get("rule") == rid and (a.get("clause") or "").strip() not in proven:
                out.append(f"clause_check: FAIL {rid}: clause not proven: {a['clause']}")
        for p in mine:
            why = proof_problem(root, (p.get("proof") or "").strip(), tests, bindings)
            if why:
                out.append(f"clause_check: FAIL {rid}: clause '{p.get('clause')}': {why}")
    return out


def proof_tests(root, base):
    """(automation test names, python test files) proving the rows that become built in this merge: the gate runs them."""
    old = {r["id"]: r for r in read_csv(at(root, base, STATUS))}
    new = {r["id"]: r for r in read_csv(at(root, None, STATUS))}
    became = {i for i, r in new.items() if (r.get("status") or "").strip() == "built"
              and (old.get(i, {}).get("status") or "").strip() != "built"}
    ue, py = set(), set()
    for p in read_csv(at(root, None, PROOF)):
        if p.get("rule") in became:
            kind, _, name = (p.get("proof") or "").partition(":")
            (ue if kind == "test" else py if kind == "py" else set()).add(name.strip())
    return sorted(ue), sorted(py)


def main(argv):
    if len(argv) >= 3 and argv[1] == "tests":   # clause_check.py tests BASE -> 'UE <name>' / 'PY <file>' lines for the gate
        ue, py = proof_tests(ROOT, argv[2])
        print("\n".join([f"UE {n}" for n in ue] + [f"PY {n}" for n in py]))
        return 0
    if len(argv) < 2:
        print(__doc__)
        return 2
    probs = check(ROOT, argv[1])
    for p in probs:
        print(p)
    print("clause_check: PASS" if not probs else f"clause_check: FAIL {len(probs)} problem(s)")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
