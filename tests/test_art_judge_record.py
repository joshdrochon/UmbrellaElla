"""The LLM art judge has a calibration run on record before its verdicts count
(evals/art-judge/README.md, "Run record"). Skips while no anchor exists."""
import csv
import io
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUDGE = os.path.join(ROOT, "evals", "art-judge")
COLS = ["date", "pair_id", "seed", "model", "prompt_version", "rubric_version", "judge_closer",
        "judge_rows_x", "judge_rows_y", "order_stable", "expected_closer", "note"]
COLS_RE = re.compile(r"`(date,[a-z_,]+)`")


def record_problems(text):
    """Problems with an agreement.csv body; [] when it is a valid run at 100% agreement.
    A row agrees when judge_closer equals expected_closer and order_stable is yes (no human verdict: the
    calibration set from the team's key art is the ground truth)."""
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return ["no rows"]
    if list(rows[0].keys()) != COLS:
        return [f"columns {list(rows[0].keys())}, want {COLS}"]
    return [f"{r['pair_id']}: judge {r['judge_closer']} vs expected {r['expected_closer']}, "
            f"order_stable={r['order_stable']}"
            for r in rows if r["judge_closer"].strip() != r["expected_closer"].strip()
            or r["order_stable"].strip().lower() != "yes"]


def schema_problems(*docs):
    """Each doc lists the agreement.csv columns exactly once, and they equal COLS."""
    out = []
    for name, text in docs:
        found = COLS_RE.findall(text.replace("\n", ""))
        if len(found) != 1:
            out.append(f"{name}: lists the agreement.csv columns {len(found)} times, want 1")
        elif found[0].split(",") != COLS:
            out.append(f"{name}: columns {found[0]}, want {','.join(COLS)}")
    return out


PIN_RE = re.compile(r"^Judge pin: model `([^`]+)`, prompt `([^`]+)`, rubric `([^`]+)`\.$", re.M)
PROMPT_RE = re.compile(r"Prompt version: `([^`]+)`\. Rubric version: `([^`]+)`")


def pin_problems(readme, prompt, agreement=None):
    """Problems with the judge pin: README names one model, its versions match the prompt file,
    and every recorded row used that model. [] when all hold."""
    pins = PIN_RE.findall(readme)
    if len(pins) != 1:
        return [f"README needs exactly one 'Judge pin:' line, found {len(pins)}"]
    model, pv, rv = pins[0]
    out = []
    head = PROMPT_RE.search(prompt)
    if not head or head.groups() != (pv, rv):
        out.append(f"pin says {pv}/{rv}, tools/art_judge_prompt.md says {head.groups() if head else None}")
    if agreement:
        out += [f"{r.get('pair_id')}: model {r.get('model')} is not the pinned {model}"
                for r in csv.DictReader(io.StringIO(agreement)) if r.get("model") != model]
    return out


def row(**kw):
    """One agreement.csv row; X is the anchor and the right answer unless changed."""
    r = dict(date="2026-11-08", pair_id="G2-vs-B1", seed="1", model="m", prompt_version="art-judge-xy/2",
             rubric_version="rubric/2", judge_closer="X", judge_rows_x="all", judge_rows_y="R1",
             order_stable="yes", expected_closer="X", note="calibration")
    r.update(kw)
    return ",".join(r[c] for c in COLS) + "\n"


class PinTests(unittest.TestCase):
    def test_repo(self):
        agree = os.path.join(JUDGE, "agreement.csv")
        with open(os.path.join(JUDGE, "README.md")) as r, open(os.path.join(ROOT, "tools", "art_judge_prompt.md")) as p:
            self.assertEqual(pin_problems(r.read(), p.read(),
                                          open(agree).read() if os.path.isfile(agree) else None), [])

    def test_rule(self):
        readme = "Judge pin: model `m1`, prompt `art-judge-xy/2`, rubric `rubric/2`.\n"
        prompt = "Prompt version: `art-judge-xy/2`. Rubric version: `rubric/2`"
        head = ",".join(COLS) + "\n"
        self.assertEqual(pin_problems(readme, prompt, head + row(model="m1")), [])
        self.assertEqual(len(pin_problems("no pin here", prompt)), 1)
        self.assertEqual(len(pin_problems(readme, prompt.replace("rubric/2", "rubric/3"))), 1)
        self.assertEqual(len(pin_problems(readme, prompt, head + row(model="m2"))), 1)


class RecordTests(unittest.TestCase):
    def test_detector(self):
        head = ",".join(COLS) + "\n"
        self.assertEqual(record_problems(head + row()), [])
        self.assertTrue(record_problems(head + row(judge_closer="Y")))  # judge picked the bad image
        self.assertTrue(record_problems(head + row(order_stable="no")))  # flipped when X/Y swapped
        self.assertTrue(record_problems(head))
        self.assertTrue(record_problems("date,judge_model,prompt_version,image,expected,verdict,agree\n"
                                        "d,m,p,B1,r,r,yes\n"))  # the old 7-column schema

    def test_both_docs_list_one_schema(self):
        docs = []
        for n in ("README.md", "blind_pairwise.md"):
            with open(os.path.join(JUDGE, n)) as fh:
                docs.append((n, fh.read()))
        self.assertEqual(schema_problems(*docs), [])

    def test_schema_rule(self):
        good = "`" + ",".join(COLS) + "`"
        self.assertEqual(schema_problems(("a", good), ("b", "cols:\n" + good)), [])
        old = "`date,judge_model,prompt_version,image,expected,verdict,agree`"
        self.assertEqual(len(schema_problems(("a", good), ("b", old))), 1)
        self.assertEqual(len(schema_problems(("a", "no columns here"))), 1)

    def test_anchors_need_a_recorded_run(self):
        anchors = os.path.join(JUDGE, "anchors")
        if not (os.path.isdir(anchors) and any(not f.startswith(".") for f in os.listdir(anchors))):
            self.skipTest("no anchor frames yet (card 0.10)")
        path = os.path.join(JUDGE, "agreement.csv")
        self.assertTrue(os.path.isfile(path), "anchors exist but evals/art-judge/agreement.csv does not")
        with open(path) as f:
            self.assertEqual(record_problems(f.read()), [])


if __name__ == "__main__":
    unittest.main()
