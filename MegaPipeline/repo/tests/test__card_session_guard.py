"""A card session never runs the full suite (Josh, 12 Nov: a docs card took over an hour of unit tests).

`unittest discover` imports every test module before it runs one; this module sorts first, so inside a kickoff card
session (JAM_KICKOFF=1 and JAM_ROLE set) a full discover stops here with one line. Codex sessions have no deny list,
so this is their stop; Claude sessions also have kickoff's CLAUDE_DENY. A targeted run
(`python3 -m unittest tests.test_x`), CI and a person (no JAM_KICKOFF) are unaffected.
Tests: tests/test_affected_tests.py (SessionGuard)."""
import os
import sys
import unittest

MESSAGE = "card sessions run tools/affected_tests.py, not the full suite"
VALUE_OPTS = {"-k", "-s", "-p", "-t", "--start-directory", "--pattern", "--top-level-directory"}


def in_card_session(env):
    return env.get("JAM_KICKOFF") == "1" and bool(env.get("JAM_ROLE"))


def is_full_discover(argv):
    """True for `python -m unittest` with no test names, or `... discover ...`."""
    if not argv or not os.path.basename(argv[0].split()[-1] if argv[0] else "").startswith(("unittest", "__main__")):
        return False
    names, skip = [], False
    for a in argv[1:]:
        if skip:
            skip = False
        elif a in VALUE_OPTS:
            skip = True
        elif not a.startswith("-"):
            names.append(a)
    return not names or names[0] == "discover"


if in_card_session(os.environ) and is_full_discover(sys.argv):
    sys.stderr.write(MESSAGE + "\n")
    sys.stderr.flush()
    os._exit(2)


class Guard(unittest.TestCase):
    def test_outside_a_card_session_it_lets_discover_run(self):
        self.assertFalse(in_card_session({}))
