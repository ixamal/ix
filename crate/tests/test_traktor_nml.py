from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.traktor_nml import cache_ok, plan_repair


def _nml(collection: str, playlists: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<NML VERSION="20">'
        f"<COLLECTION ENTRIES=\"2\">{collection}</COLLECTION>"
        f"<PLAYLISTS><NODE TYPE=\"FOLDER\" NAME=\"$ROOT\">"
        f"<SUBNODES COUNT=\"1\">{playlists}</SUBNODES></NODE></PLAYLISTS>"
        "</NML>"
    )


class CacheOkTests(unittest.TestCase):
    def test_requires_000_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "040").mkdir()
            self.assertFalse(cache_ok("040/ABCDEF", root))
            (root / "040" / "ABCDEF000").write_bytes(b"x")
            self.assertTrue(cache_ok("040/ABCDEF", root))


class PlaylistDedupeTests(unittest.TestCase):
    def test_drops_second_primarykey(self) -> None:
        with TemporaryDirectory() as tmp:
            nml = Path(tmp) / "collection.nml"
            playlists = (
                '<NODE TYPE="PLAYLIST" NAME="Humid chills">'
                '<PLAYLIST ENTRIES="3" TYPE="LIST">'
                '<ENTRY><PRIMARYKEY TYPE="TRACK" KEY="a"/></ENTRY>'
                '<ENTRY><PRIMARYKEY TYPE="TRACK" KEY="a"/></ENTRY>'
                '<ENTRY><PRIMARYKEY TYPE="TRACK" KEY="b"/></ENTRY>'
                "</PLAYLIST></NODE>"
            )
            nml.write_text(_nml("", playlists), encoding="utf-8")
            plan, tree = plan_repair(nml=nml, cover_root=Path(tmp) / "Coverart", execute=True)
            self.assertEqual(plan.playlist_extras, 1)
            self.assertEqual(plan.playlists[0].kept, 2)
            keys = [
                ent.find("PRIMARYKEY").get("KEY")
                for ent in tree.find("PLAYLISTS").iter("ENTRY")
                if ent.find("PRIMARYKEY") is not None
            ]
            self.assertEqual(keys, ["a", "b"])
            playlist = tree.find("PLAYLISTS").find(".//PLAYLIST")
            self.assertEqual(playlist.get("ENTRIES"), "2")


class ArtworkShareTests(unittest.TestCase):
    def test_copies_folder_sibling_cover(self) -> None:
        with TemporaryDirectory() as tmp:
            cover = Path(tmp) / "Coverart"
            (cover / "040").mkdir(parents=True)
            (cover / "040" / "ABCDEF000").write_bytes(b"art")
            nml = Path(tmp) / "collection.nml"
            collection = (
                '<ENTRY TITLE="Mix" ARTIST="Buku">'
                '<LOCATION DIR="/:Music/:Buku/:Singles/:" FILE="mix.m4a"/>'
                '<ALBUM TITLE="Singles"/>'
                '<INFO COVERARTID="040/ABCDEF"/>'
                "</ENTRY>"
                '<ENTRY TITLE="Mix" ARTIST="Buku">'
                '<LOCATION DIR="/:Music/:Buku/:Singles/:" FILE="mix - vocals.m4a"/>'
                '<ALBUM TITLE="Singles"/>'
                "<INFO FILESIZE=\"1\"/>"
                "</ENTRY>"
            )
            nml.write_text(_nml(collection, ""), encoding="utf-8")
            plan, tree = plan_repair(nml=nml, cover_root=cover, execute=True)
            self.assertEqual(plan.artwork, 1)
            vocals = [
                e
                for e in tree.find("COLLECTION").findall("ENTRY")
                if (e.find("LOCATION").get("FILE") or "").endswith("vocals.m4a")
            ][0]
            self.assertEqual(vocals.find("INFO").get("COVERARTID"), "040/ABCDEF")

    def test_does_not_share_singles_across_folders(self) -> None:
        with TemporaryDirectory() as tmp:
            cover = Path(tmp) / "Coverart"
            (cover / "040").mkdir(parents=True)
            (cover / "040" / "ABCDEF000").write_bytes(b"art")
            nml = Path(tmp) / "collection.nml"
            collection = (
                '<ENTRY TITLE="A" ARTIST="One">'
                '<LOCATION DIR="/:Music/:One/:Singles/:" FILE="a.m4a"/>'
                '<ALBUM TITLE="Singles"/>'
                '<INFO COVERARTID="040/ABCDEF"/>'
                "</ENTRY>"
                '<ENTRY TITLE="B" ARTIST="Two">'
                '<LOCATION DIR="/:Music/:Two/:Singles/:" FILE="b.m4a"/>'
                '<ALBUM TITLE="Singles"/>'
                "<INFO FILESIZE=\"1\"/>"
                "</ENTRY>"
            )
            nml.write_text(_nml(collection, ""), encoding="utf-8")
            plan, _tree = plan_repair(nml=nml, cover_root=cover, execute=True)
            self.assertEqual(plan.artwork, 0)


class CopyTwinTests(unittest.TestCase):
    def _wav(self, path: Path, seconds: float, tone: int) -> Path:
        import math
        import struct
        import wave

        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(22050)
            count = int(22050 * seconds)
            handle.writeframes(
                b"".join(
                    struct.pack(
                        "<h",
                        int(16000 * math.sin(2 * math.pi * tone * i / 22050)),
                    )
                    for i in range(count)
                )
            )
        return path

    def test_drops_numbered_wav_when_length_and_audio_match(self) -> None:
        from ix_crate.traktor_nml import apply_copy_twins, plan_copy_twins

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            album = root / "IndustryStems" / "03_God_is_God"
            keep = self._wav(album / "vocals.wav", 0.4, 440)
            extra = album / "vocals (2).wav"
            extra.write_bytes(keep.read_bytes())
            from ix_crate.music_replicants import decoded_digest

            if not decoded_digest(keep):
                self.skipTest("ffmpeg not available")
            twins, skipped = plan_copy_twins(stems_root=root)
            self.assertEqual(skipped, 0)
            self.assertEqual(len(twins), 1)
            self.assertEqual(Path(twins[0].drop).name, "vocals (2).wav")
            apply_copy_twins(twins, stems_root=root)
            self.assertTrue(keep.is_file())
            self.assertFalse(extra.exists())

    def test_keeps_same_length_different_audio(self) -> None:
        from ix_crate.traktor_nml import plan_copy_twins

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            album = root / "IndustryStems" / "Song"
            self._wav(album / "vocals.wav", 0.4, 440)
            self._wav(album / "vocals (2).wav", 0.4, 880)
            twins, skipped = plan_copy_twins(stems_root=root)
            from ix_crate.music_replicants import decoded_digest

            if not decoded_digest(album / "vocals.wav"):
                self.skipTest("ffmpeg not available")
            self.assertEqual(twins, [])
            self.assertGreaterEqual(skipped, 1)

    def test_stem_finder_copy_matches_on_size_and_head(self) -> None:
        from ix_crate.traktor_nml import apply_copy_twins, plan_copy_twins

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            album = root / "Buku" / "Singles"
            album.mkdir(parents=True)
            keep = album / "Honey.stem.m4a"
            extra = album / "Honey.stem (2).m4a"
            keep.write_bytes(b"STEM" + b"\x00" * 2000)
            extra.write_bytes(keep.read_bytes())
            twins, skipped = plan_copy_twins(stems_root=root)
            self.assertEqual(skipped, 0)
            self.assertEqual(len(twins), 1)
            self.assertEqual(Path(twins[0].drop).name, "Honey.stem (2).m4a")
            apply_copy_twins(twins, stems_root=root)
            self.assertTrue(keep.is_file())
            self.assertFalse(extra.exists())
        from ix_crate.traktor_nml import plan_copy_twins

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            album = root / "IndustryStems" / "Song"
            payload = self._wav(album / "vocals.wav", 0.4, 440).read_bytes()
            (album / "drums.wav").write_bytes(payload)
            twins, _skipped = plan_copy_twins(stems_root=root)
            self.assertEqual(twins, [])


if __name__ == "__main__":
    unittest.main()
