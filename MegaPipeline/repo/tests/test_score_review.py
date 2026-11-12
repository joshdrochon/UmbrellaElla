"""score_review must pass a perfect reviewer and fail lazy ones (approve-all, miss a blocker)."""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import score_review as sr  # noqa: E402

CASES = os.path.join(ROOT, "evals", "reviewer", "cases")


def write_run(fn):
    d = tempfile.mkdtemp()
    for c in os.listdir(CASES):
        exp_p = os.path.join(CASES, c, "expected.json")
        if not os.path.isfile(exp_p):
            continue
        with open(exp_p) as fh:
            exp = json.load(fh)
        with open(os.path.join(d, c + ".json"), "w") as fh:
            json.dump(fn(c, exp), fh)
    return d


def perfect(_, exp):
    seen = {"build": "pass", "tests": "pass", "package": "n/a"}
    if exp["clean"]:
        return {"verdict": "approve", "findings": [], "checks_seen": seen}
    for key, val in (exp.get("checks") or {}).items():
        seen[key] = val
    return {"verdict": "request_changes", "checks_seen": seen, "findings": [
        {"file": x["file"], "line": x["lines"][0], "severity": x["severity"], "summary": x["keywords"][0]} for x in exp["defects"]]}


def evidence_cases():
    out = []
    for c in sorted(os.listdir(CASES)):
        with open(os.path.join(CASES, c, "expected.json")) as fh:
            if json.load(fh).get("checks"):
                out.append(c)
    return out


class ScoreReviewTests(unittest.TestCase):
    def check(self, fn):
        d = write_run(fn)
        try:
            return sr.summarize(sr.score(CASES, d))
        finally:
            shutil.rmtree(d)

    def test_cases_are_well_formed(self):
        n_clean = n_dirty = n_evidence = 0
        for c in os.listdir(CASES):
            with open(os.path.join(CASES, c, "expected.json")) as fh:
                exp = json.load(fh)
            self.assertTrue(os.path.isfile(os.path.join(CASES, c, "change.diff")))
            with open(os.path.join(CASES, c, "change.diff")) as fh:
                diff = fh.read()
            checks = exp.get("checks") or {}
            for key, val in checks.items():
                self.assertIn(key, ("build", "tests", "module_check", "package"), c)
                self.assertIn(val, ("missing", "fail"), c)
            if exp["clean"]:
                self.assertEqual((exp["defects"], checks), ([], {}), c)
            else:
                self.assertTrue(exp["defects"] or checks, c)
            for d in exp["defects"]:
                self.assertIn(d["severity"], ("blocker", "high", "med", "low"), c)
                for place in [d] + d.get("also", []):
                    self.assertIn("+++ b/" + place["file"], diff, c)
                    self.assertLessEqual(place["lines"][0], place["lines"][1], c)
            n_clean += exp["clean"]
            n_dirty += not exp["clean"]
            n_evidence += bool(checks)
        self.assertGreaterEqual(n_dirty, 10)
        self.assertGreaterEqual(n_clean, 3)
        self.assertGreaterEqual(n_evidence, 1)

    def test_evidence_cases_ship_their_evidence(self):
        # An evidence defect lives in evidence.txt; without it the case would get the default "all pass" block.
        for c in evidence_cases():
            self.assertTrue(os.path.isfile(os.path.join(CASES, c, "evidence.txt")), c)

    def test_reviewer_saying_pass_for_missing_tests_is_not_caught(self):
        def expects_missing(case):
            with open(os.path.join(CASES, case, "expected.json")) as fh:
                return "missing" in json.load(fh)["checks"].values()
        c = next(c for c in evidence_cases() if expects_missing(c))
        def says_pass(case, e):
            r = perfect(case, e)
            if case == c:
                r["checks_seen"] = {"build": "pass", "tests": "pass", "package": "n/a"}
            return r
        s = self.check(says_pass)
        self.assertFalse(s["pass"])
        self.assertTrue(any(m.startswith(c + ":checks.") for m in s["missed"]), s["missed"])

    def test_check_needs_request_changes(self):
        item = {"id": "checks.tests", "severity": "blocker", "check": "tests", "expect": "missing"}
        self.assertTrue(sr.check_caught(item, {"verdict": "request_changes", "checks_seen": {"tests": "missing"}}))
        self.assertTrue(sr.check_caught(item, {"verdict": "request_changes", "checks_seen": {"tests": "FAIL"}}))
        self.assertFalse(sr.check_caught(item, {"verdict": "approve", "checks_seen": {"tests": "missing"}}))
        self.assertFalse(sr.check_caught(item, {"verdict": "request_changes", "checks_seen": {"tests": "pass"}}))
        self.assertFalse(sr.check_caught(item, {"verdict": "request_changes", "checks_seen": {}}))
        self.assertFalse(sr.check_caught(item, {"verdict": "request_changes"}))

    def test_blocking_evidence_cases_for_the_wrong_reason_still_misses(self):
        # request_changes on every evidence case, but checks_seen copied from the default "all pass" block.
        def wrong_reason(case, e):
            r = perfect(case, e)
            if e.get("checks"):
                r["checks_seen"] = {"build": "pass", "tests": "pass", "package": "n/a"}
            return r
        s = self.check(wrong_reason)
        self.assertFalse(s["pass"])
        self.assertEqual(sum(m.split(":")[1].startswith("checks.") for m in s["missed"]), len(evidence_cases()))

    def test_also_location_counts(self):
        d = {"id": "x", "severity": "high", "file": "Public/A.h", "lines": [8, 9], "keywords": ["channel"],
             "also": [{"file": "Config/DefaultEngine.ini", "lines": [19, 20]}]}
        self.assertTrue(sr.caught(d, [{"file": "Config/DefaultEngine.ini", "line": 20, "summary": "Channel order differs"}]))
        self.assertTrue(sr.caught(d, [{"file": "A.h", "line": 8, "summary": "channel mismatch"}]))
        self.assertFalse(sr.caught(d, [{"file": "Config/DefaultEngine.ini", "line": 8, "summary": "channel"}]))
        self.assertFalse(sr.caught(d, [{"file": "Other.cpp", "line": 19, "summary": "channel"}]))

    def test_perfect_reviewer_passes(self):
        self.assertTrue(self.check(perfect)["pass"])

    def test_approve_everything_fails(self):
        s = self.check(lambda c, e: {"verdict": "approve", "findings": []})
        self.assertFalse(s["pass"])
        self.assertEqual(s["recall"], 0.0)

    def test_block_everything_fails(self):
        s = self.check(lambda c, e: {"verdict": "request_changes", "findings": perfect(c, e)["findings"]})
        self.assertFalse(s["pass"])

    def test_missing_one_blocker_fails(self):
        def miss_attack(c, e):
            r = perfect(c, e)
            if c.startswith("04-"):
                r["findings"] = []
            return r
        s = self.check(miss_attack)
        self.assertFalse(s["pass"])
        self.assertIn("04-attack-while-open:attack-gating", s["missed"])

    def test_zero_cases_fails(self):
        self.assertFalse(sr.summarize([])["pass"])

    def test_clean_cases_do_not_reveal_themselves(self):
        # Every case's task.md must state test evidence, so "evidence present" cannot tell a clean case apart.
        for c in os.listdir(CASES):
            with open(os.path.join(CASES, c, "task.md")) as fh:
                self.assertIn("Tests in this PR", fh.read(), c)

    def test_must_catch_cases_exist_and_a_miss_fails_the_run(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import run_reviewer_eval as rre
        for c in rre.MUST_CATCH:
            self.assertTrue(os.path.isdir(os.path.join(CASES, c)), c)
        rows = [{"case": rre.MUST_CATCH[0], "defects": [{"id": "x"}], "hits": []},
                {"case": "13-clean-open-umbrella", "defects": [], "hits": []}]
        self.assertEqual(rre.must_catch_missed(rows), [rre.MUST_CATCH[0]])
        rows[0]["hits"] = [{"id": "x"}]
        self.assertEqual(rre.must_catch_missed(rows), [])

    def test_wrong_line_does_not_count(self):
        def wrong_line(c, e):
            r = perfect(c, e)
            for f in r["findings"]:
                f["line"] += 40
            return r
        self.assertFalse(self.check(wrong_line)["pass"])


if __name__ == "__main__":
    unittest.main()
