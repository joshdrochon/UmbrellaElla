"""Every file under pipeline/art/reference/ has a row in pipeline/art/provenance.csv with author, origin and
licence filled (art-bible.md, Provenance). "unknown" is allowed for a reference only; it is never shipped."""
import csv
import io
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "pipeline", "art", "reference")
CSV = os.path.join(ROOT, "pipeline", "art", "provenance.csv")


def missing_rows(paths, csv_text):
    """Problems: each repo-relative path needs one row with author, origin and licence non-empty."""
    rows = {r["asset_path"]: r for r in csv.DictReader(io.StringIO(csv_text))}
    out = []
    for p in paths:
        r = rows.get(p)
        if r is None:
            out.append(f"{p}: no provenance row")
        else:
            out += [f"{p}: {k} is empty" for k in ("author", "origin", "licence") if not (r.get(k) or "").strip()]
    return out


def reference_files():
    out = []
    for d, _, fs in os.walk(REF):
        out += [os.path.relpath(os.path.join(d, f), ROOT).replace(os.sep, "/") for f in fs if not f.startswith(".")]
    return sorted(out)


class ProvenanceTests(unittest.TestCase):
    def test_repo(self):
        with open(CSV) as f:
            self.assertEqual(missing_rows(reference_files(), f.read()), [])

    def test_rule(self):
        head = "asset_path,author,origin,tool,model_version,prompt,seed,input_images,date,licence,attribution\n"
        row = "a.png,Rick,hand-made,,,,,,2026-11-06,CC0,\n"
        self.assertEqual(missing_rows(["a.png"], head + row), [])
        self.assertEqual(len(missing_rows(["a.png", "b.png"], head + row)), 1)
        self.assertEqual(len(missing_rows(["a.png"], head + row.replace("CC0", ""))), 1)


if __name__ == "__main__":
    unittest.main()
