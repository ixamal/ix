from __future__ import annotations

import unittest
from pathlib import Path

from ix_crate.music_playlist import collect_sources, want_from_filename


class WantFromFilenameTests(unittest.TestCase):
    def test_beatport_id(self) -> None:
        want = want_from_filename(Path("9671006_Acid_Queen_(Original_Mix).mp3"))
        self.assertEqual(want.title, "Acid Queen (Original Mix)")
        self.assertEqual(want.artist, "")

    def test_youre_so_just_just(self) -> None:
        want = want_from_filename(
            Path("18638646_You_re_So_Just_Just_(Seth_Troxler_x_Ryan_Crosson_Remix).mp3")
        )
        self.assertEqual(
            want.title, "You're So Just Just (Seth Troxler x Ryan Crosson Remix)"
        )

    def test_artist_dash_missing_space(self) -> None:
        want = want_from_filename(
            Path("Bodyrox, Luciana -What Planet You On (Bodyrox Vocal Club Mix).mp3")
        )
        self.assertEqual(want.artist, "Bodyrox, Luciana")
        self.assertEqual(want.title, "What Planet You On (Bodyrox Vocal Club Mix)")

    def test_whats_up_hyphen_s(self) -> None:
        want = want_from_filename(
            Path("DJ Jazzy Jeff, Terry Hunter, Uhmeer, Christian Crosby -What-s Up (Terry Hunter Remix).mp3")
        )
        self.assertEqual(want.title, "What's Up (Terry Hunter Remix)")
        from ix_crate.music_playlist import _titles_ok

        self.assertTrue(_titles_ok(want.title, "What_s Up (Terry Hunter Remix)"))


class CollectSourcesTests(unittest.TestCase):
    def test_root_and_beatport_folder(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Chemars -Jazz In The Park (Extended Club Mix).mp3").write_bytes(b"a")
            folder = root / "beatport_tracks_2026-09"
            folder.mkdir()
            (folder / "9671006_Acid_Queen_(Original_Mix).mp3").write_bytes(b"b")
            (root / "ignore.txt").write_text("x")
            names = [p.name for p in collect_sources(root)]
            self.assertEqual(len(names), 2)
            self.assertIn("Chemars -Jazz In The Park (Extended Club Mix).mp3", names)
            self.assertIn("9671006_Acid_Queen_(Original_Mix).mp3", names)


if __name__ == "__main__":
    unittest.main()
