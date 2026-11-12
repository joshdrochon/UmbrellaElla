import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import run_reviewer_eval as r  # noqa: E402


class ExtractJsonTests(unittest.TestCase):
    def test_json_then_prose_with_braces(self):
        text = '{"verdict": "request_changes", "findings": []}\nKeep unchanged: the {bOpen} state and FFoo{}.'
        self.assertEqual(r.extract_json(text)["verdict"], "request_changes")

    def test_leading_prose_with_braces_is_skipped(self):
        text = 'Note {x}.\n{"verdict": "approve", "findings": []}'
        self.assertEqual(r.extract_json(text)["verdict"], "approve")

    def test_no_json_is_invalid(self):
        self.assertEqual(r.extract_json("no json here {oops")["verdict"], "invalid")

    def test_object_without_verdict_is_not_accepted(self):
        self.assertEqual(r.extract_json('{"a": 1}')["verdict"], "invalid")


if __name__ == "__main__":
    unittest.main()
