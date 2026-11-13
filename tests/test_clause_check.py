"""clause_check: a row may become `built` only when every audited clause has an existing proof (Nov 13)."""
import os, shutil, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "build"))
import clause_check  # noqa: E402

HEAD = "id,area,status,evidence,note,owner\n"


class ClauseCheck(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        os.makedirs(os.path.join(self.d, "docs", "build"))
        os.makedirs(os.path.join(self.d, "Source", "T"))
        self.write("Source/T/Tests.cpp", 'IMPLEMENT_SIMPLE_AUTOMATION_TEST(FA, "UmbrellaElla.Flow.TitleMusicAtLaunch", 0)\n')
        self.write("docs/build/gdd-bindings.json", '{"FLOW-34.volume": {}}')
        self.write("docs/build/rule-status.csv", HEAD + "FLOW-34,flow,partial,,,\nFLOW-01,flow,built,x,,\n")
        self.write("docs/build/clause-audit.csv", "rule,clause,tag,lane\nFLOW-34,Start screen plays music,ii,flow\n")
        g = lambda *a: subprocess.run(["git", "-C", self.d] + list(a), check=True, capture_output=True)
        g("init", "-q"); g("add", "-A"); g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")

    def write(self, rel, text):
        with open(os.path.join(self.d, rel), "w") as fh:
            fh.write(text)

    def set_built(self):
        self.write("docs/build/rule-status.csv", HEAD + "FLOW-34,flow,built,y,,\nFLOW-01,flow,built,x,,\n")

    def test_baseline_rows_are_not_checked(self):
        self.assertEqual(clause_check.check(self.d, "HEAD"), [])

    def test_new_built_without_proof_fails(self):
        self.set_built()
        self.assertTrue(any("no clause proof" in p for p in clause_check.check(self.d, "HEAD")))

    def test_unproven_audited_clause_fails(self):
        self.set_built()
        self.write("docs/build/clause-proof.csv", "rule,clause,proof\nFLOW-34,Music volume applies,gdd:FLOW-34.volume\n")
        self.assertTrue(any("clause not proven: Start screen plays music" in p for p in clause_check.check(self.d, "HEAD")))

    def test_missing_test_fails_and_full_proof_passes(self):
        self.set_built()
        self.write("docs/build/clause-proof.csv", "rule,clause,proof\nFLOW-34,Start screen plays music,test:UmbrellaElla.Flow.Nope\n")
        self.assertTrue(any("not defined in Source" in p for p in clause_check.check(self.d, "HEAD")))
        self.write("docs/build/clause-proof.csv", "rule,clause,proof\nFLOW-34,Start screen plays music,test:UmbrellaElla.Flow.TitleMusicAtLaunch\n")
        self.assertEqual(clause_check.check(self.d, "HEAD"), [])


if __name__ == "__main__":
    unittest.main()
