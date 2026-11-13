import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "build"))
import art_scheduler as S

INV = "visual,source,piece,owner,passed,slot,drawn_by\n" + "".join(
    f"v{i},s,{p},{o},{ok},x,y\n" for i, (p, o, ok) in enumerate([
        ("vfx-a", "artfx", "no"), ("vfx-b", "artfx", "no"), ("vfx-c", "artfx", "no"), ("ui-a", "artui", "no"),
        ("ui-b", "artui", "yes"), ("ui-c", "artui", "yes"), ("owl", "artkeeper", "no")]))


class Grouping(unittest.TestCase):
    def test_inventory_piece_passes_only_if_every_row_does(self):
        inv = S.parse_inventory(INV)
        inv2 = S.parse_inventory(INV + "x,s,ui-d,artui,no,x,y\nx,s,ui-d,artui,yes,x,y\n")
        self.assertFalse(inv2["ui-d"]["passed"])
        self.assertTrue(inv["ui-b"]["passed"])
        self.assertEqual(inv["owl"]["owner"], "artkeeper")

    def test_chunks_are_3_to_8_balanced_by_family(self):
        ps = [f"vfx-{i:02d}" for i in range(10)] + ["ui-a", "ui-b", "ui-c"]
        ch = S.chunk_owner_pieces(ps)
        self.assertTrue(all(S.MIN_LOOP <= len(c) <= S.MAX_LOOP for c in ch), ch)
        self.assertEqual(sorted(sum(ch, [])), sorted(ps))

    def test_small_remainder_merges(self):
        ch = S.chunk_owner_pieces([f"a-{i}" for i in range(9)] + ["b-1"])
        self.assertEqual(sorted(len(c) for c in ch), [5, 5])

    def test_unowned_pieces_get_owner_numbered_lanes_and_one_owner_each(self):
        inv = S.parse_inventory("visual,source,piece,owner,passed,slot,drawn_by\n" + "".join(
            f"v,s,vfx-{i:02d},artfx,no,x,y\n" for i in range(20)))
        existing = S.parse_groups("artfx|vfx-00 vfx-01 vfx-02\nartfx2|artfx|vfx-02 vfx-03 vfx-04\n")
        groups, new, notes = S.assign(existing, inv)
        self.assertEqual([g.lane for g in new], ["artfx3", "artfx4"])
        owned = [p for g in groups for p in g.pieces]
        self.assertEqual(len(owned), len(set(owned)))
        self.assertEqual(set(owned), set(inv))
        self.assertTrue(any("DUPLICATE piece=vfx-02" in n for n in notes))
        self.assertEqual(new[0].line().split("|")[1], "artfx")

    def test_passed_pieces_are_not_grouped(self):
        groups, new, _ = S.assign([], S.parse_inventory(INV))
        self.assertEqual(sorted(g.lane for g in new), ["artfx", "artkeeper", "artui"])
        self.assertNotIn("ui-b", sum((g.pieces for g in new), []))


class Capacity(unittest.TestCase):
    def test_memory_thresholds_match_ue_slot(self):
        self.assertEqual([S.ue_slots(x) for x in (30, 40, 50, 57)], [4, 3, 2, 0])
        self.assertEqual(S.capacity(5, 30, 100)[0], 16)
        self.assertEqual(S.capacity(5, 40, 100)[0], 14)
        self.assertEqual(S.capacity(9, 50, 100)[0], 9)    # hold: running loops stay, none start

    def test_spend_limits_new_loops_and_no_cap_means_none(self):
        self.assertEqual(S.capacity(10, 30, 1.2)[0], 12)
        self.assertEqual(S.capacity(10, 30, 0.0)[0], 10)
        self.assertEqual(S.capacity(10, 30, None)[0], 10)

    def test_never_below_running(self):
        self.assertEqual(S.capacity(15, 60, -3)[0], 15)


class Handoff(unittest.TestCase):
    G = [S.Group("a", "", ["p1", "p2", "p3"]), S.Group("b", "", ["p4", "p5", "p6"]), S.Group("c", "", ["p7", "p8", "p9"])]

    def acts(self, passed, running, state=None, cap=2):
        return {l: a for a, l, _ in S.plan(self.G, passed, running, state or {}, cap)}

    def test_start_up_to_capacity_in_file_order(self):
        a = self.acts({}, set())
        self.assertEqual((a["a"], a["b"], a["c"]), ("START", "START", "HOLD"))

    def test_loop_that_passes_is_stopped_and_slot_goes_to_next_group(self):
        done = {"a": {"p1", "p2", "p3"}}
        a = self.acts(done, {"a", "b"})
        self.assertEqual(a["a"], "STOP")
        self.assertEqual(a["c"], "START")

    def test_finished_group_is_never_restarted(self):
        a = self.acts({"a": {"p1", "p2", "p3"}}, set())
        self.assertEqual(a["a"], "DONE")

    def test_exit_with_work_left_restarts_then_gives_up(self):
        st = {"a": {"restarts": 1, "left": 3, "last": 1}}
        self.assertEqual(self.acts({}, {"b"}, st)["a"], "RESTART")
        st["a"]["restarts"] = 8
        self.assertEqual(self.acts({}, {"b"}, st)["a"], "GIVE_UP")

    def test_progress_resets_restart_count(self):
        st = {"a": {"restarts": 8, "left": 3, "last": 1}}
        self.assertEqual(self.acts({"a": {"p1"}}, {"b"}, st)["a"], "RESTART")


if __name__ == "__main__":
    unittest.main()
