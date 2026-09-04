from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.music_cull import verdict


class VerdictTest(unittest.TestCase):
    def test_empty_path_is_missing(self) -> None:
        self.assertEqual(verdict(""), "missing")
        self.assertEqual(verdict("   "), "missing")

    def test_absent_file_is_missing(self) -> None:
        self.assertEqual(verdict("/no/such/track.m4a"), "missing")

    def test_id3_wav_is_corrupt(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.wav"
            path.write_bytes(b"ID3\x03\x00\x00" + b"x" * 80)
            self.assertEqual(verdict(str(path)), "corrupt")

    def test_riff_wav_is_kept(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.wav"
            path.write_bytes(b"RIFF" + b"\x00" * 80)
            self.assertEqual(verdict(str(path)), "keep")

    def test_tiny_file_is_corrupt(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.mp3"
            path.write_bytes(b"ID3")
            self.assertEqual(verdict(str(path)), "corrupt")

    def test_drm_purchase_is_kept(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.m4p"
            path.write_bytes(b"xxxx")
            self.assertEqual(verdict(str(path)), "keep")


if __name__ == "__main__":
    unittest.main()
