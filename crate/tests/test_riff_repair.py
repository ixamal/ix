from __future__ import annotations

import math
import struct
import unittest
import wave
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.music_repair import write_file_tags
from ix_crate.riff_repair import (
    copy_number,
    finder_copy_number,
    group_key,
    is_id3_headed,
    is_riff,
    plan_group,
    apply_group,
)


def _wav(path: Path, seconds: float = 0.2, tone: int = 440) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(22050)
        n = int(22050 * seconds)
        handle.writeframes(
            b"".join(
                struct.pack("<h", int(12000 * math.sin(2 * math.pi * tone * i / 22050)))
                for i in range(n)
            )
        )
    return path


def _id3_prefix(path: Path) -> Path:
    body = path.read_bytes()
    path.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x20" + b"x" * 32 + body)
    return path


class HeaderTest(unittest.TestCase):
    def test_riff_and_id3(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = _wav(root / "a.wav")
            bad = _id3_prefix(_wav(root / "b.wav"))
            self.assertTrue(is_riff(good))
            self.assertFalse(is_riff(bad))
            self.assertTrue(is_id3_headed(bad))


class GroupKeyTest(unittest.TestCase):
    def test_numbered_copies_share_a_key(self) -> None:
        self.assertEqual(
            group_key(Path("/x/Kwai (Roland Appel Remix).wav")),
            group_key(Path("/x/Kwai (Roland Appel Remix) (2).wav")),
        )
        self.assertEqual(copy_number("Kwai (2)"), 2)
        self.assertEqual(copy_number("Kwai"), 0)
        self.assertEqual(finder_copy_number(Path("Title.stem (2).m4a")), 2)
        self.assertEqual(finder_copy_number(Path("Title (2).stem.m4a")), 2)
        self.assertEqual(finder_copy_number(Path("Let's Get High (1999).mp3")), 0)

    def test_same_title_in_two_albums_stays_distinct(self) -> None:
        self.assertNotEqual(
            group_key(Path("/a/Album 1/Track.wav")),
            group_key(Path("/a/Album 2/Track.wav")),
        )


class PlanGroupTest(unittest.TestCase):
    def test_corrupt_unnumbered_is_restored_from_sibling(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            good_bytes = _wav(root / "Track (2).wav").read_bytes()
            _wav(root / "Track (3).wav").write_bytes(good_bytes)
            bad = _id3_prefix(_wav(root / "Track.wav"))
            plan = plan_group([bad, root / "Track (2).wav", root / "Track (3).wav"])
            self.assertEqual(plan.keeper, bad)
            self.assertEqual(plan.restore_from, root / "Track (2).wav")
            self.assertEqual(set(plan.delete), {root / "Track (2).wav", root / "Track (3).wav"})

    def test_valid_unnumbered_just_drops_identical_copies(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = _wav(root / "Track.wav")
            extra = root / "Track (2).wav"
            extra.write_bytes(keep.read_bytes())
            plan = plan_group([keep, extra])
            self.assertIsNone(plan.restore_from)
            self.assertEqual(plan.delete, [extra])

    def test_nested_folder_is_scanned(self) -> None:
        from ix_crate.riff_repair import build_plan

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = _wav(root / "Artist" / "Album" / "Track.wav")
            extra = root / "Artist" / "Album" / "Track (2).wav"
            extra.write_bytes(keep.read_bytes())
            _wav(root / "Artist" / "Album" / "Other.wav")
            items, _ = build_plan(root)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].delete, [extra])

    def test_execute_leaves_one_riff_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            donor = _wav(root / "Track (2).wav")
            payload = donor.read_bytes()
            (root / "Track (3).wav").write_bytes(payload)
            keeper = _id3_prefix(_wav(root / "Track.wav"))
            plan = plan_group([keeper, donor, root / "Track (3).wav"])
            apply_group(plan)
            self.assertTrue(is_riff(keeper))
            self.assertFalse(donor.exists())
            self.assertFalse((root / "Track (3).wav").exists())


class WriteFileTagsWavTest(unittest.TestCase):
    def test_does_not_prepend_id3_on_wav(self) -> None:
        with TemporaryDirectory() as tmp:
            path = _wav(Path(tmp) / "a.wav")
            before = path.read_bytes()[:4]
            write_file_tags(
                path, artist="A", album="B", title="C", genre="Electronic"
            )
            self.assertEqual(path.read_bytes()[:4], before)
            self.assertEqual(before, b"RIFF")


if __name__ == "__main__":
    unittest.main()
