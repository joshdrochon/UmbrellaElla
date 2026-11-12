"""GDD SH1.0 health, XP and retry rules (Ricky's import audit points 2-4), on tools/progression_model.py.

The numbers are adjustable prototype tuning; these tests pin the arithmetic the GDD prints and the rules it states, so
a code card and a balance pass both have an oracle. Each rule has a passing case and a case that breaks it."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import progression_model as pm  # noqa: E402

V = pm.values(ROOT)


class Health(unittest.TestCase):
    def test_three_health_per_life_replaces_8_10_12(self):
        """Audit point 2: incoming damage is the former 8 / 10 / 12 divided by 8; outgoing damage and enemy HP stay."""
        d = V["FLOW-33.old_damage_divisor"]
        self.assertEqual((V["FLOW-33.projectile_damage"], V["FLOW-33.chain_damage"], V["FLOW-33.talon_damage"]),
                         (8 / d, 10 / d, 12 / d))
        self.assertEqual(V["FLOW-33.trap_damage"], 1)
        self.assertEqual(V["COM-06.damage"], 10, "outgoing Small Blasts damage is not rescaled")
        self.assertEqual(V["OWL-08.clock_hp"], 320, "boss HP is not rescaled")
        h = pm.Health(V)
        self.assertEqual((h.capacity, h.lives), (3, 3))
        for _ in range(3):
            h.hit(V["FLOW-33.projectile_damage"])
        self.assertEqual((h.lives, h.active), (2, 3.0), "three ordinary hits empty one life")

    def test_keeper_attacks_use_the_new_scale(self):
        """Every incoming damage number in the shipped Keeper preset is one of the SH1.0 values."""
        with open(os.path.join(ROOT, "pipeline", "level", "encounter.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        presets = data["encounter_presets"]["presets"]
        base = presets[data["encounter_presets"]["default"]]
        allowed = {V["FLOW-33.projectile_damage"], V["FLOW-33.chain_damage"], V["FLOW-33.talon_damage"]}
        got = {a["id"]: a["effect"]["damage"] for a in base["attacks"]}
        self.assertTrue(got)
        for aid, dmg in got.items():
            self.assertIn(dmg, allowed, aid)
        self.assertNotIn(8, got.values())
        self.assertNotIn(34, got.values(), "no 1.3 / 100 HP damage left in the shipped fight")

    def test_overflow_defense_lift_and_no_revival(self):
        h = pm.Health(V, defense_rank=3)
        h.hit(1)
        self.assertAlmostEqual(h.active, 2.3, msg="defense 30 % applies once, no per-hit rounding")
        h = pm.Health(V)
        h.hit(2.5).hit(1.5)            # 4 damage: the 1 past the first life carries into the next
        self.assertEqual(h.lives, 2)
        self.assertAlmostEqual(h.active, 2.0)
        self.assertAlmostEqual(pm.Health(V).lift(), 1.0)
        low = pm.Health(V)
        low.active = 0.0
        self.assertAlmostEqual(low.lift(), V["SURV-05.min_lift"])
        dead = pm.Health(V)
        for _ in range(9):
            dead.hit(1)
        self.assertTrue(dead.defeated)
        dead.absorb_yellow()
        self.assertTrue(dead.defeated, "healing never revives")

    def test_healing_ranks_and_reserve_rebuild(self):
        heals = [round(pm.Health(V, recovery_rank=r).heal_per_yellow(), 6) for r in range(4)]
        self.assertEqual(heals, [0.5, 0.8, 1.1, 1.4])
        self.assertAlmostEqual(0.5 / 3, 0.1667, places=3)
        h = pm.Health(V)
        h.hit(3)                        # one life spent
        self.assertEqual(h.lives, 2)
        h.active = 2.8
        h.absorb_yellow()               # 0.2 fills the active life, 0.3 starts the reserve
        self.assertEqual(h.active, 3.0)
        self.assertAlmostEqual(h.reserve_progress, 0.3)
        for _ in range(6):
            h.absorb_yellow()
        self.assertEqual(h.lives, 3, "one active-life capacity rebuilds one reserve")
        h.absorb_yellow()
        self.assertEqual(h.lives, 3, "never past maximum lives")


class Xp(unittest.TestCase):
    def test_level_62_curve_and_ten_run_target(self):
        """Audit point 4: 100 + floor((L-1)/2); 916 / 1981 / 3096 / 7000 at 10 / 20 / 30 / 62; about 10 runs of 700."""
        for lv in (10, 20, 30, 62):
            self.assertEqual(pm.cumulative_xp(V, lv), V[f"FLOW-15.cumulative_xp_level_{lv}"], lv)
        runs = pm.cumulative_xp(V, 62) / V["FLOW-15.target_xp_per_run"]
        self.assertEqual(runs, V["FLOW-15.target_completed_runs"])
        for xp in (600 * 10, 800 * 10):  # the GDD's 600-800 XP measuring band: 8.75 to 11.7 runs, still "around 10"
            self.assertTrue(8 <= pm.cumulative_xp(V, 62) / (xp / 10) <= 12)
        self.assertEqual(pm.level_for_xp(V, 916), (10, 0))
        self.assertEqual(pm.level_for_xp(V, 920), (10, 4), "surplus carries")
        self.assertEqual(pm.level_for_xp(V, 10 ** 6), (62, 0), "MAX at the cap")

    def test_61_points_max_every_track(self):
        self.assertEqual(V["FLOW-15.level_cap"] - 1, V["FLOW-15.earned_points_at_cap"])
        self.assertEqual(pm.max_track_cost(V), V["FLOW-15.earned_points_at_cap"])

    def test_unlocks_cost_no_points(self):
        self.assertEqual(pm.unlocked(V, 9), ["Small Blasts"])
        self.assertEqual(pm.unlocked(V, 10), ["Small Blasts", "Streamed Blast"])
        self.assertEqual(len(pm.unlocked(V, 30)), 4)
        self.assertEqual(len(pm.unlocked(V, 62)), 4, "no fifth weapon")


class Scaling(unittest.TestCase):
    def test_completed_runs_raise_health_attack_speed_and_count(self):
        """Audit point 4: each completed run raises all three levers, up to the caps; Final Hour replaces them."""
        prev = pm.run_scaling(V, 0)
        self.assertEqual(prev, {"hp": 1, "cadence": 1, "count": 1})
        for c in range(1, 25):
            cur = pm.run_scaling(V, c)
            for k in cur:
                self.assertGreaterEqual(cur[k], prev[k], (c, k))
            prev = cur
        self.assertEqual(pm.run_scaling(V, 10), {"hp": 2, "cadence": 1.3, "count": 2})
        self.assertEqual(pm.run_scaling(V, 1)["hp"], 1.1)
        fh = pm.run_scaling(V, 10, final_hour=True)
        self.assertEqual(fh, {"hp": 2, "cadence": 1.35, "count": 2}, "replaces, never compounds (2 x 2 = 4 would)")

    def test_more_enemies_only_in_legal_slots(self):
        self.assertEqual(pm.enemy_count(V, 5, 10, legal_slots=20), (10, 0))
        self.assertEqual(pm.enemy_count(V, 5, 10, legal_slots=7), (7, 3), "fewer placed, shortfall recorded")


class Retry(unittest.TestCase):
    def test_level_checkpoint_keeps_boss_checkpoint_rolls_back(self):
        """Audit point 3."""
        p = pm.Progress(V, xp=900)
        p.reach_checkpoint("level")
        p.kill(V["FLOW-19.xp_floodstrider"])
        self.assertEqual(p.level, 10)
        p.death_retry()
        self.assertEqual((p.xp, p.level), (920, 10), "level checkpoint: earned XP and levels kept")
        p.kill(V["FLOW-19.xp_floodstrider"])
        self.assertEqual(p.xp, 940, "the same enemy gives XP again after the retry")
        b = pm.Progress(V, xp=900)
        b.reach_checkpoint("boss")
        b.kill(V["FLOW-19.xp_wings"])
        b.spent = 9                     # spent the level-10 point after the checkpoint
        b.death_retry()
        self.assertEqual((b.xp, b.level, b.spent, b.points), (900, 9, 0, 8), "boss checkpoint: XP, level, points back")
        q = pm.Progress(V, xp=500)
        q.reach_checkpoint("level")
        q.kill(100)
        q.quit_reload()
        self.assertEqual(q.xp, 500, "quit reloads the last checkpoint")

    def test_death_retry_gives_three_lives_and_full_health(self):
        h = pm.Health(V, capacity=5, max_lives=6)
        for _ in range(4):
            h.hit(5)
        self.assertEqual(h.lives, 2)
        h.death_retry()
        self.assertEqual((h.lives, h.active, h.max_lives, h.capacity), (3, 5.0, 6, 5),
                         "exactly 3 current lives, full at the purchased capacity, maxima unchanged")


if __name__ == "__main__":
    unittest.main()
