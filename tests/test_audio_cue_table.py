"""The cue subsystem plays every live sound-list row: the generated table (UmbrellaCueData.h) has a row for each,
its concurrency and class assets exist in audio-rules.json, and a row whose take passed the blind critic is routed."""
import csv, json, os, re, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "pipeline", "audio", "build"))
import audio_check  # noqa: E402
import cue_table  # noqa: E402

TABLE = os.path.join(ROOT, "Source", "UmbrellaElla", "Public", "Feedback", "Audio", "UmbrellaCueData.h")
ROW = re.compile(r'\{TEXT\("(\w+)"\), EUmbrellaEventType::(\w+), EUmbrellaCueMatch::(\w+), TEXT\("([\w]*)"\), '
                 r'EUmbrellaCueClass::(\w+), TEXT\("(\w*)"\), (true|false), (\d+), ([\d.]+)f, TEXT\("(\w*)"\)\}')
EVENTS = re.findall(r"^\t(\w+),?\s*$", open(os.path.join(ROOT, "Source", "UmbrellaElla", "Public", "Core", "UmbrellaEvent.h"),
                                            encoding="utf-8").read().split("enum class EUmbrellaEventType")[1].split("};")[0], re.M)


def table():
    return [m.groups() for m in ROW.finditer(open(TABLE, encoding="utf-8").read())]


class CueTable(unittest.TestCase):
    def test_committed_table_is_what_the_generator_writes(self):
        self.assertEqual(cue_table.main(["check"]), 0)

    def test_every_live_row_has_a_cue_mapping(self):
        ids = {r[0] for r in table()}
        for r in cue_table.rows():
            self.assertIn(r["id"], ids, "%s is a live sound-list row with no cue mapping" % r["id"])

    def test_every_sound_with_a_passing_take_is_routed_to_a_bus_event_or_played_by_name(self):
        rows = audio_check.load_list()
        by_id = {}
        for g in table():
            by_id.setdefault(g[0], []).append(g)
        src = os.path.join(ROOT, "Audio", "Source")
        for r in rows:
            folder = os.path.join(src, r["id"])
            if r["tier"] == "cut" or not os.path.isdir(folder):
                continue
            takes = sorted(os.path.join(folder, n) for n in os.listdir(folder) if n.endswith(".wav"))
            if not takes or audio_check.critic_verdict(r["id"], takes) is False:
                continue
            self.assertIn(r["id"], by_id, "%s has a take and no cue mapping" % r["id"])

    def test_events_exist_and_matches_carry_a_value(self):
        for sid, ev, match, value, *_ in table():
            self.assertTrue(ev in EVENTS or ev == "Count", "%s: unknown event %s" % (sid, ev))
            self.assertEqual(bool(value), match != "Any", "%s: match %s with value %r" % (sid, match, value))

    def test_class_concurrency_and_loop_match_the_rules(self):
        rules = audio_check.load_rules()
        by_id = {r["id"]: r for r in cue_table.rows()}
        for sid, _ev, _m, _v, klass, con, loop, takes, _j, _g in table():
            row = by_id[sid]
            self.assertEqual(klass, row["class"], sid)
            self.assertEqual(con, audio_check.concurrency_for(row, rules) or "", sid)
            self.assertEqual(loop == "true", row["kind"] == "loop", sid)
            self.assertEqual(int(takes), int(row["takes"]), sid)

    def test_a_sound_is_routed_to_something_that_can_happen(self):
        """Event vocabulary check: bus events with a route are in the manifest."""
        manifest = set(audio_check.manifest().get("events") or [])
        for sid, ev, *_ in table():
            if ev != "Count":
                self.assertIn(ev, manifest, "%s listens to %s, which is not a manifest event" % (sid, ev))


if __name__ == "__main__":
    unittest.main()
