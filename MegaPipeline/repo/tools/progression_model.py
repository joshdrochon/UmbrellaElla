#!/usr/bin/env python3
"""Reference model of the GDD SH1.0 health, progression and retry rules. Stdlib only.

The engine code (Gameplay Dev cards) must agree with this model; tests/test_progression_model.py checks the model
against the numbers docs/feature-manifest.json approved_parameters copies from the GDD. Every number here is read from
the manifest, so a new GDD revision changes the model without editing this file. All of it is adjustable prototype
tuning (GDD SH1.0: "approved starting values for playtesting, not proof of final balance").

  health   FLOW-33 / SURV-05 / SURV-07: 3 ordinary hits per life, 3 lives; incoming damage 1 / 1.25 / 1.5 health
           (former 8 / 10 / 12 divided by 8); defense ranks 0 / 10 / 20 / 30 %; damage overflows into the next life;
           lift = min_lift + (1 - min_lift) x clamp(active / capacity); yellow heals 0.5 + 0.3 x recovery rank,
           active life first, then a spent reserve (one active-life capacity per reserve, a derived default)
  xp       FLOW-15: next level from L costs xp_curve_base + floor((L - 1) / 2); one stat point per level; cap 62
  scaling  FLOW-05 / FLOW-06: completed runs C scale enemy HP, ordinary cadence and count; Final Hour replaces them
  retry    FLOW-07 / FLOW-09 / FLOW-13 / FLOW-20: a level-checkpoint death retry keeps XP and levels; a boss-checkpoint
           retry restores the checkpoint's XP, points and unlocks; every death retry gives exactly 3 current lives and
           a full active life; normal checkpoint passage never heals

Usage: python3 tools/progression_model.py   prints the XP milestones and the run-scaling table
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = "docs/feature-manifest.json"
# The seven three-rank tracks other than recovery (SURV-06, SURV-07): damage reduction, suction range, suction cone and
# four spell-damage tracks, each ranked 1 / 2 / 3 points.
OTHER_TRACKS = 7
OTHER_RANK_COSTS = (1, 2, 3)
RECOVERY_RANKS = 3
DEFENSE_RANKS = (0.0, 0.10, 0.20, 0.30)   # SURV-07 ordinary damage reduction 0 / 10 / 20 / 30 %
UNLOCKS = {"Small Blasts": 1}             # FLOW-16; the other three come from the manifest


def values(root=ROOT):
    with open(os.path.join(root, MANIFEST), encoding="utf-8") as fh:
        vals = json.load(fh)["approved_parameters"]["values"]
    return {k: v["start"] for k, v in vals.items()}


# ---------------------------------------------------------------- XP and points (FLOW-15, FLOW-16, SURV-06)
def level_cost(v, level):
    return v["FLOW-15.xp_curve_base"] + (level - 1) // 2


def cumulative_xp(v, level):
    """XP needed to reach `level` from level 1 with zero partial XP."""
    return sum(level_cost(v, lv) for lv in range(1, level))


def level_for_xp(v, xp):
    """(level, partial XP toward the next level); surplus carries across gains; MAX at the cap."""
    level = 1
    while level < v["FLOW-15.level_cap"] and xp >= level_cost(v, level):
        xp -= level_cost(v, level)
        level += 1
    return level, (0 if level == v["FLOW-15.level_cap"] else xp)


def max_track_cost(v):
    hits = v["FLOW-15.max_hits_per_life"] - v["FLOW-15.start_hits_per_life"]
    lives = v["FLOW-15.max_lives"] - v["FLOW-15.start_lives"]
    return hits + lives + OTHER_TRACKS * sum(OTHER_RANK_COSTS) + RECOVERY_RANKS


def unlocked(v, level):
    u = dict(UNLOCKS, **{"Streamed Blast": v["FLOW-16.unlock_level_streamed"], "Twin Stars": v["FLOW-16.unlock_level_twin"],
                         "Needle Spell": v["FLOW-16.unlock_level_needle"]})
    return sorted(name for name, at in u.items() if level >= at)


# ---------------------------------------------------------------- health (FLOW-33, SURV-05, SURV-07, UMB-05)
class Health:
    def __init__(self, v, capacity=None, max_lives=None, defense_rank=0, recovery_rank=0):
        self.v = v
        self.capacity = capacity or v["FLOW-15.start_hits_per_life"]
        self.max_lives = max_lives or v["FLOW-15.start_lives"]
        self.defense = DEFENSE_RANKS[defense_rank]
        self.recovery_rank = recovery_rank
        self.lives = self.max_lives       # current lives, the active one included
        self.active = float(self.capacity)
        self.reserve_progress = 0.0
        self.defeated = False

    def hit(self, damage):
        """Resolve one incoming hit now; leftover damage carries into the next life (FLOW-33 overflow default)."""
        left = damage * (1 - self.defense)
        while left > 1e-12 and not self.defeated:
            take = min(left, self.active)
            self.active -= take
            left -= take
            if self.active <= 1e-12:
                if self.lives > 1:
                    self.lives -= 1
                    self.active = float(self.capacity)
                else:
                    self.active, self.defeated = 0.0, True
        return self

    def heal_per_yellow(self):
        return self.v["UMB-05.heal_per_yellow"] + self.v["UMB-05.heal_per_recovery_rank"] * self.recovery_rank

    def absorb_yellow(self):
        """Active life first; the same shot's surplus rebuilds a spent reserve, never past max lives; no revival."""
        if self.defeated:
            return self
        heal = self.heal_per_yellow()
        room = self.capacity - self.active
        self.active += min(heal, room)
        heal -= min(heal, room)
        while heal > 1e-12 and self.lives < self.max_lives:
            need = self.capacity - self.reserve_progress
            step = min(heal, need)
            self.reserve_progress += step
            heal -= step
            if self.reserve_progress >= self.capacity - 1e-12:
                self.lives += 1
                self.reserve_progress = 0.0
        return self

    def lift(self):
        m = self.v["SURV-05.min_lift"]
        return m + (1 - m) * max(0.0, min(1.0, self.active / self.capacity))

    def death_retry(self):
        """FLOW-09: exactly 3 current lives and a full active life at the current capacity; maxima unchanged."""
        self.lives = min(self.v["FLOW-15.start_lives"], self.max_lives)
        self.active = float(self.capacity)
        self.reserve_progress = 0.0
        self.defeated = False
        return self


# ---------------------------------------------------------------- run scaling (FLOW-05, FLOW-06)
def run_scaling(v, completed_runs, final_hour=False):
    """{'hp', 'cadence', 'count'} multipliers for the next run. Final Hour replaces, never compounds."""
    if final_hour:
        return {"hp": v["FLOW-06.final_hour_hp_multiplier"], "cadence": v["FLOW-06.final_hour_cadence_multiplier"],
                "count": v["FLOW-06.final_hour_count_multiplier"]}
    c = completed_runs
    return {"hp": min(v["FLOW-05.hp_multiplier_cap"], 1 + v["FLOW-05.hp_multiplier_step"] * c),
            "cadence": min(v["FLOW-05.cadence_multiplier_cap"], 1 + v["FLOW-05.cadence_multiplier_step"] * c),
            "count": min(v["FLOW-05.count_multiplier_cap"], 1 + v["FLOW-05.count_multiplier_step"] * c)}


def enemy_count(v, base, completed_runs, legal_slots, final_hour=False):
    """round(base x count multiplier), never more than the legal authored slots (the shortfall is recorded)."""
    want = int(math.floor(base * run_scaling(v, completed_runs, final_hour)["count"] + 0.5))
    return min(want, legal_slots), max(0, want - legal_slots)


# ---------------------------------------------------------------- checkpoints and retries (FLOW-07..FLOW-13, FLOW-20)
class Progress:
    """Earned XP and spent points for one Director's Cut run, with checkpoint snapshots."""

    def __init__(self, v, xp=0, spent=0):
        self.v, self.xp, self.spent = v, xp, spent
        self.snapshot = None

    @property
    def level(self):
        return level_for_xp(self.v, self.xp)[0]

    @property
    def points(self):
        return self.level - 1 - self.spent

    def kill(self, xp):
        self.xp += xp

    def reach_checkpoint(self, kind):
        """kind 'level' or 'boss'. Passage awards no XP and never heals (FLOW-19, FLOW-28)."""
        self.snapshot = (kind, self.xp, self.spent)

    def death_retry(self):
        kind, xp, spent = self.snapshot
        if kind == "boss":            # FLOW-07, FLOW-13: restore XP, points and unlocks coherently
            self.xp, self.spent = xp, spent
        # a level checkpoint keeps earned XP and levels (FLOW-07); enemies there give XP again (FLOW-12)
        return self

    def quit_reload(self):
        _, xp, spent = self.snapshot   # FLOW-08: the last checkpoint's XP and upgrades
        self.xp, self.spent = xp, spent
        return self


def main(argv=None):
    v = values()
    print("xp: " + ", ".join(f"level {lv} = {cumulative_xp(v, lv)}" for lv in (10, 20, 30, int(v["FLOW-15.level_cap"]))))
    runs = math.ceil(cumulative_xp(v, int(v["FLOW-15.level_cap"])) / v["FLOW-15.target_xp_per_run"])
    print(f"runs to the cap at {v['FLOW-15.target_xp_per_run']} XP per run: {runs}")
    print(f"points at the cap: {int(v['FLOW-15.level_cap']) - 1}; cost to max every track: {max_track_cost(v)}")
    for c in (0, 1, 5, 10, 20):
        print(f"completed runs {c}: {run_scaling(v, c)}")
    print(f"final hour: {run_scaling(v, 0, final_hour=True)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
