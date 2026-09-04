from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.music_genre import GenreRow, promote, write_file_genre


class PromoteTest(unittest.TestCase):
    def test_strips_the_edm_prefix(self) -> None:
        self.assertEqual(promote("EDM, House"), "House")
        self.assertEqual(promote("EDM, Ambient"), "Ambient")
        self.assertEqual(promote("EDM, Electronica"), "Electronica")

    def test_keeps_the_store_subgenre_tail(self) -> None:
        self.assertEqual(promote("EDM, House, Deep"), "House, Deep")

    def test_leaves_other_genres_alone(self) -> None:
        for genre in ("House", "Electronica / Downtempo", "Pop / Rock", "Acapella"):
            self.assertEqual(promote(genre), genre)

    def test_does_not_strip_a_genre_that_merely_contains_edm(self) -> None:
        self.assertEqual(promote("Progressive EDM, House"), "Progressive EDM, House")

    def test_handles_empty(self) -> None:
        self.assertEqual(promote(""), "")
        self.assertEqual(promote("   "), "")


class RowTest(unittest.TestCase):
    def test_row_exposes_its_promoted_genre(self) -> None:
        row = GenreRow(index=1, persistent_id="A1", name="x", genre="EDM, House", path="")
        self.assertEqual(row.promoted, "House")


class WriteFileGenreTest(unittest.TestCase):
    def test_refuses_drm_purchases(self) -> None:
        with TemporaryDirectory() as tmp:
            drm = Path(tmp) / "a.m4p"
            drm.write_bytes(b"x")
            self.assertFalse(write_file_genre(drm, "House"))

    def test_missing_file_is_not_an_error(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertFalse(write_file_genre(Path(tmp) / "gone.mp3", "House"))

    def test_refuses_wav_so_id3_is_not_prepended(self) -> None:
        with TemporaryDirectory() as tmp:
            wav = Path(tmp) / "a.wav"
            wav.write_bytes(b"RIFF" + b"\x00" * 80)
            self.assertFalse(write_file_genre(wav, "House"))
            self.assertTrue(wav.read_bytes().startswith(b"RIFF"))


if __name__ == "__main__":
    unittest.main()
