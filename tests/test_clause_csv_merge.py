"""clause_csv_merge: union of rows by key; a proven row wins a clash (Nov 13)."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "build"))
import clause_csv_merge as m  # noqa: E402

A = "docs/build/clause-audit.csv"
P = "docs/build/clause-proof.csv"
H = "rule,clause,tag,lane\n"


def rows(text):
    return [l for l in text.strip().split("\n")[1:]]


class ClauseCsvMerge(unittest.TestCase):
    def test_union_of_both_sides_new_rows(self):
        base = H + "R-1,a,i,x\n"
        main = H + "R-1,a,i,x\nR-2,b,ii,y\n"
        lane = H + "R-1,a,i,x\nR-3,c,i,z\n"
        self.assertEqual(sorted(rows(m.merge(A, base, main, lane))), ["R-1,a,i,x", "R-2,b,ii,y", "R-3,c,i,z"])

    def test_proven_wins_a_clash_either_side(self):
        base = H + "R-1,a,i,x\n"
        self.assertEqual(rows(m.merge(A, base, H + "R-1,a,proven,x\n", H + "R-1,a,ii,x\n")), ["R-1,a,proven,x"])
        self.assertEqual(rows(m.merge(A, base, H + "R-1,a,ii,x\n", H + "R-1,a,proven,x\n")), ["R-1,a,proven,x"])

    def test_proof_rows_keyed_by_proof_and_status(self):
        h = "rule,clause,proof,status\n"
        base = h
        main = h + "R-1,a,test:T.A,test only, not break-checked\n"
        lane = h + "R-1,a,test:T.A,proven\nR-1,a,test:T.B,proven\n"
        out = m.merge(P, base, main, lane)
        self.assertIn("R-1,a,test:T.A,proven", out)
        self.assertIn("R-1,a,test:T.B,proven", out)
        self.assertNotIn("not break-checked", out)

    def test_a_row_one_side_removed_stays_removed(self):
        base = H + "R-1,a,i,x\nR-2,b,i,y\n"
        main = H + "R-1,a,i,x\n"   # main removed R-2
        lane = H + "R-1,a,i,x\nR-2,b,i,y\n"
        self.assertEqual(rows(m.merge(A, base, main, lane)), ["R-1,a,i,x"])


if __name__ == "__main__":
    unittest.main()
