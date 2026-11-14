"""tools/build/approved_art_guard.py: approved art cannot leave the build without a new approval (lead order, Nov 13 20:05).

Each test builds a small git repo shaped like ours (approvals.json, standins.json, art-inventory.csv, a uasset whose
embedded import record names the source file's md5, as Unreal writes it) and checks one merge base..head.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import approved_art_guard as guard  # noqa: E402

APPROVED = b"\x89PNG approved ella idle grid" + bytes(range(64))
SILHOUETTE = b"\x89PNG dark warm-rim silhouette" + bytes(range(64, 128))
OWL = b"\x89PNG approved keeper owl grid" + bytes(range(128, 192))
COPY = "pipeline/art/proof/standins/ella-up-open/Ella_idle_N24_grid.png"
OWL_FILE = "pipeline/art/proof/artkeeper/keeper-idle/fixed/Keeper_idle_N24_grid.png"
IDLE_PH = "Content/UmbrellaElla/Art/Ella/T_Ella_Idle_PH.uasset"
IDLE_PASSED = "Content/UmbrellaElla/Art/Ella/T_Ella_Idle.uasset"
OWL_PH = "Content/UmbrellaElla/Art/Keeper/T_Keeper_Owl_PH.uasset"
PRESENTER = "Source/UmbrellaElla/Private/Feedback/Anim/EllaAnimPresenterComponent.cpp"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def uasset(src, stamp):
    """Bytes shaped like an imported texture: the AssetImportData record carries the source file's md5."""
    rec = '[{ "RelativeFilename" : "../../src.png", "Timestamp" : "%d", "FileMD5" : "%s" }]' % (stamp, hashlib.md5(src).hexdigest())
    return b"\xc1\x83\x2a\x9e header " + rec.encode() + b" bulk " + hashlib.sha512(src + str(stamp).encode()).digest()


def approval(piece, path, data):
    return {"piece": piece, "approver": "Josh", "file": path, "sha256": sha(data)}


class GuardRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.invalid"); self.git("config", "user.name", "t")
        self.write(COPY, APPROVED)
        self.write(OWL_FILE, OWL)
        self.write(guard.APPROVALS, json.dumps({"approvals": [approval("ella-up-open", COPY, APPROVED),
                                                              approval("keeper-idle", OWL_FILE, OWL)]}))
        self.write(guard.STANDINS, json.dumps({"slots": {"ella-state:Idle": {"piece": "ella-up-open", "copy": COPY, "sha256": sha(APPROVED)}}}))
        self.write(guard.INVENTORY, "visual,source,piece,owner,passed,slot,drawn_by\n"
                   "ella-state:Idle,x,ella-up-open,artella,yes,/Game/UmbrellaElla/Art/Ella/T_Ella_Idle,UEllaAnimPresenterComponent\n"
                   "keeper:body-hover-flap,x,owl,artkeeper,no,/Game/UmbrellaElla/Art/Keeper/T_Keeper_Owl,UKeeperPresenterSubsystem\n")
        self.write(IDLE_PH, uasset(APPROVED, 1))
        self.write(OWL_PH, uasset(OWL, 1))
        self.write(PRESENTER, "void Draw()\n{\n\tApplyArt(TEXT(\"T_Ella_Idle\"));\n}\n")
        self.base = self.commit("base")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", self.root] + list(args), check=True, capture_output=True).stdout.decode()

    def write(self, rel, data):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data.encode() if isinstance(data, str) else data)

    def commit(self, msg):
        self.git("add", "-A"); self.git("commit", "-q", "--allow-empty", "-m", msg)
        return self.git("rev-parse", "HEAD").strip()

    def run_check(self):
        return guard.check(self.root, self.base, self.commit("head"))[1]

    def assertFails(self, needle):
        problems = self.run_check()
        self.assertTrue(any(needle in p for p in problems), problems)

    # --- the two cases the lead named ---
    def test_replacement_like_d550580c_fails(self):
        self.write("pipeline/art/proof/artella/silhouette/ella-idle_N24_grid.png", SILHOUETTE)
        self.write(IDLE_PH, uasset(SILHOUETTE, 2))
        self.assertFails(IDLE_PH)

    def test_reimport_of_approved_bytes_passes(self):
        self.write(IDLE_PH, uasset(APPROVED, 3))   # new timestamp, new uasset bytes, same approved source
        self.assertEqual(self.run_check(), [])

    # --- the rest of the rule ---
    def test_delete_fails(self):
        os.remove(os.path.join(self.root, IDLE_PH))
        self.assertFails("deletes")

    def test_passed_name_with_other_bytes_fails(self):
        self.write(IDLE_PASSED, uasset(SILHOUETTE, 2))   # the passed name wins over _PH in the game: a swap
        self.assertFails(IDLE_PASSED)

    def test_new_approval_for_new_bytes_passes(self):
        path = "pipeline/art/proof/artella/ella-idle-v2.png"
        self.write(path, SILHOUETTE)
        self.write(IDLE_PH, uasset(SILHOUETTE, 2))
        self.write(guard.APPROVALS, json.dumps({"approvals": [approval("ella-up-open", path, SILHOUETTE),
                                                              approval("keeper-idle", OWL_FILE, OWL)]}))
        self.assertEqual(self.run_check(), [])

    def test_keeper_alias_slot_is_guarded(self):
        self.write(OWL_PH, uasset(SILHOUETTE, 2))
        self.assertFails(OWL_PH)

    def test_texture_found_by_embedded_md5(self):
        other = "Content/UmbrellaElla/Art/Ella/T_Ella_Copy_PH.uasset"
        self.write(other, uasset(APPROVED, 1))
        self.base = self.commit("another slot ships the approved bytes")
        self.write(other, uasset(SILHOUETTE, 2))
        self.assertFails(other)

    def test_changing_approved_file_fails(self):
        self.write(COPY, SILHOUETTE)
        self.assertFails(COPY)

    def test_standins_row_to_other_bytes_fails(self):
        self.write(guard.STANDINS, json.dumps({"slots": {"ella-state:Idle": {"piece": "ella-up-open", "copy": "x.png", "sha256": sha(SILHOUETTE)}}}))
        self.assertFails("ella-state:Idle")

    def test_tint_code_fails(self):
        self.write(PRESENTER, "void Draw()\n{\n\tApplyArt(TEXT(\"T_Ella_Idle\"));\n"
                   "\tMesh->SetVectorParameterValueOnMaterials(TEXT(\"Tint\"), DarkSilhouette);\n}\n")
        self.assertFails("tint, hide or swap")

    def test_hide_by_visual_id_fails(self):
        self.write("Source/UmbrellaElla/Private/Feedback/Art/Other.cpp",
                   "if (Row.Visual == TEXT(\"ella-state:Idle\"))\n{\n\tMesh->SetHiddenInGame(true);\n}\n")
        self.assertFails("ella-up-open")

    def test_unrelated_code_and_art_pass(self):
        self.write("Source/UmbrellaElla/Private/Motor/Motor.cpp", "void Step() { Color = FLinearColor::Red; }\n")
        self.write("Content/UmbrellaElla/Art/Scene/T_BgBase_PH.uasset", uasset(SILHOUETTE, 5))
        self.assertEqual(self.run_check(), [])

    def test_cli_exit_codes(self):
        self.write(IDLE_PH, uasset(SILHOUETTE, 2))
        head = self.commit("bad")
        self.assertEqual(guard.main(["check", "--root", self.root, "--base", self.base, "--head", head]), 1)
        self.assertEqual(guard.main(["check", "--root", self.root, "--base", head, "--head", head]), 0)


if __name__ == "__main__":
    unittest.main()
