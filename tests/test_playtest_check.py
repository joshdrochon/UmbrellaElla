import importlib.util, pathlib, unittest
p = pathlib.Path(__file__).resolve().parents[1] / "tools/build/playtest_check.py"
s = importlib.util.spec_from_file_location("playtest_check", p)
pc = importlib.util.module_from_spec(s); s.loader.exec_module(pc)

GOOD = """
PLAYTEST_CAM04 profile=v1 health=full env_min=0 env_max=500 vert_disp=300 qualified=1
PLAYTEST_CAM04 profile=v1 health=min env_min=0 env_max=500 vert_disp=250 qualified=1
PLAYTEST_FLOW25 drawn_width=200 usable_width=198 tol=5 lead_left_ok=1 lead_right_ok=1 stages_total=4 stages_covered=4
PLAYTEST_CAM07 decision_height=900 reopen_height=300 required_current_active=1 challenge_clear=0
PLAYTEST_FLOW28 health_before=6 health_after=6 max=10 threats=0 framing_settled=1 boss_began=1
PLAYTEST_HAZ16 res=1280x720 debug=0 health=healthy autoaim=0 invuln=0 teleport=0 boring=0 cleared=1
PLAYTEST_HAZ16 res=1920x1080 debug=0 health=low autoaim=0 invuln=0 teleport=0 boring=0 cleared=1
"""

class T(unittest.TestCase):
    def test_good(self):
        r = pc.evaluate(GOOD)
        self.assertTrue(all(v["pass"] for v in r.values()), r)

    def test_missing_is_fail(self):
        self.assertFalse(pc.evaluate("")["CAM-04"]["pass"])

    def test_free_heal_fails(self):
        r = pc.evaluate(GOOD.replace("health_after=6", "health_after=8"))
        self.assertFalse(r["FLOW-28"]["pass"])

    def test_current_gone_early_fails(self):
        r = pc.evaluate(GOOD.replace("required_current_active=1", "required_current_active=0"))
        self.assertFalse(r["CAM-07"]["pass"])

    def test_teleport_fails(self):
        r = pc.evaluate(GOOD.replace("teleport=0", "teleport=1", 1))
        self.assertFalse(r["HAZ-16"]["pass"])

    def test_missing_background_fails(self):
        r = pc.evaluate(GOOD.replace("stages_covered=4", "stages_covered=3"))
        self.assertFalse(r["FLOW-25"]["pass"])

if __name__ == "__main__":
    unittest.main()
