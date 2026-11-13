"""Tests for the shared UI style's procedural art sources (Art/Source/UI): the display font the game embeds.
The font is built from code, so the committed TTF and the C++ byte array must be exactly what the script writes."""
import importlib.util
import os
import struct
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "Art", "Source", "UI", "Font", "build_font.py")


def load():
    spec = importlib.util.spec_from_file_location("build_font", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class DisplayFont(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bf = load()
        cls.data = cls.bf.build_ttf()

    def tables(self):
        n = struct.unpack(">H", self.data[4:6])[0]
        out = {}
        for i in range(n):
            tag, cs, off, ln = struct.unpack(">4sIII", self.data[12 + 16 * i:28 + 16 * i])
            out[tag.decode()] = (cs, off, ln)
        return out

    def test_committed_outputs_are_fresh(self):
        self.assertEqual(self.bf.main(["--check"]), 0, "run Art/Source/UI/Font/build_font.py and commit its outputs")

    def test_build_is_deterministic(self):
        self.assertEqual(self.data, self.bf.build_ttf())

    def test_table_checksums_and_required_tables(self):
        t = self.tables()
        for tag in ("cmap", "glyf", "head", "hhea", "hmtx", "loca", "maxp", "name", "post", "OS/2"):
            self.assertIn(tag, t)
        for tag, (cs, off, ln) in t.items():
            if tag == "head":
                continue   # holds the whole-file adjustment
            self.assertEqual(self.bf._checksum(self.data[off:off + ln]), cs, tag)
        self.assertEqual(self.bf._checksum(self.data), 0xB1B0AFBA, "whole-file checksum")

    def test_every_menu_character_has_a_glyph(self):
        have = set()
        for cps, _, _ in self.bf.all_glyphs():
            have.update(cps)
        text = ("Umbrella Ella The Stolen Hour Start Game Director's Cut Settings Quit Paused Continue Defeated Retry "
                "Quit to Title Level 12 Points left 3 Confirm (2 points) Cancel Done Back Save Journey Complete "
                "Try Again Main Menu Sound Controller Credits + - 0123456789 .,:;!?%/&")
        missing = sorted({c for c in text if ord(c) not in have})
        self.assertEqual(missing, [])

    def test_small_capitals_are_smaller_and_contours_wind_one_way(self):
        g = {cps[0]: (contours, adv) for cps, contours, adv in self.bf.all_glyphs() if cps}
        top = lambda ch: max(y for c in g[ord(ch)][0] for _, y in c)
        self.assertLess(top("h"), top("H"))
        self.assertGreater(top("h"), 0.6 * top("H"))
        for cp, (contours, _) in g.items():
            for c in contours:
                self.assertLess(self.bf.area(c), 0, f"U+{cp:04X}: a contour winds the other way (it would cut a hole)")

    def test_inl_holds_the_same_bytes(self):
        text = self.bf.inl_text(self.data)
        self.assertIn(f"GUmbrellaStorybookFontSize = {len(self.data)};", text)
        body = text[text.index("{") + 1:text.rindex("}")]
        self.assertEqual(bytes(int(x) for x in body.replace("\n", "").replace("\t", "").split(",") if x), self.data)


if __name__ == "__main__":
    unittest.main()
