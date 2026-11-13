"""CORE-06: package.sh appends asset_manifest=<id> to BUILD_INFO.txt (levelchunks lane)."""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, HERE)
import test_ue_scripts as tus  # noqa: E402

UAT = ('for a in "$@"; do case "$a" in -archivedirectory=*) d="${a#-archivedirectory=}";; esac; done\n'
       'mkdir -p "$d/Mac" "$d/../Saved/StagedBuilds/Mac/UmbrellaElla.app/Contents/UE"; echo game > "$d/Mac/UmbrellaElla"\n'
       'echo "BUILD SUCCESSFUL"; exit 0')


def asset_line(path):
    with open(path, encoding="utf-8") as fh:
        return [ln for ln in fh.read().splitlines() if ln.startswith("asset_manifest=")]


@unittest.skipIf(os.name == "nt", "runs the Mac tools/ue/package.sh on a bash RunUAT.sh stub")
class PackageWritesAssetManifest(unittest.TestCase):
    def setUp(self):
        self.r = tus.FakeRepo()
        self.addCleanup(self.r.close)
        self.r.stub("Engine/Build/BatchFiles/RunUAT.sh", UAT)

    def package(self):
        rc, out = self.r.sh("package.sh")
        self.assertEqual(rc, 0, out)
        return asset_line(os.path.join(self.r.dir, "Packaged", "BUILD_INFO.txt"))

    def test_build_info_gets_one_asset_manifest_line_per_folder(self):
        top = self.package()
        self.assertEqual(len(top), 1, top)
        self.assertRegex(top[0], r"^asset_manifest=[0-9a-f]{16}$")
        self.assertEqual(asset_line(os.path.join(self.r.dir, "Packaged", "Mac", "BUILD_INFO.txt")), top)

    def test_same_commit_same_id_and_a_new_asset_changes_it(self):
        first = self.package()
        self.assertEqual(self.package(), first)
        tus.write(os.path.join(self.r.dir, "Content", "Art", "T_New.txt"), "x\n")
        for args in (["add", "-A"], ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "asset"]):
            subprocess.run(["git", *args], cwd=self.r.dir, check=True)
        self.assertNotEqual(self.package(), first)


if __name__ == "__main__":
    unittest.main()
