import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ix_crate.music_dupes import (
    TrackRow,
    canon_path,
    group_file_rows,
    keep_key,
    pick_keeper,
)


def _row(
    pid: str,
    location: str,
    *,
    database_id: int = 1,
    played_count: int = 0,
    rating: int = 0,
    playlist_hits: int = 0,
    name: str = "Track",
) -> TrackRow:
    return TrackRow(
        persistent_id=pid,
        database_id=database_id,
        artist="Artist",
        album="Album",
        name=name,
        location=location,
        played_count=played_count,
        rating=rating,
        playlist_hits=playlist_hits,
    )


class CanonPathTests(unittest.TestCase):
    def test_empty_is_empty(self) -> None:
        self.assertEqual(canon_path(""), "")
        self.assertEqual(canon_path("   "), "")

    def test_resolves_existing_file(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.mp3"
            path.write_bytes(b"x")
            alias = Path(tmp) / "sub"
            alias.mkdir()
            linked = alias / ".." / "a.mp3"
            self.assertEqual(canon_path(str(linked)), str(path.resolve()))


class KeeperTests(unittest.TestCase):
    def test_playlist_hits_win(self) -> None:
        a = _row("A", "/x", database_id=1, playlist_hits=0, played_count=99)
        b = _row("B", "/x", database_id=2, playlist_hits=3, played_count=0)
        self.assertEqual(pick_keeper([a, b]).persistent_id, "B")

    def test_plays_then_rating_then_oldest(self) -> None:
        a = _row("A", "/x", database_id=10, played_count=1, rating=80)
        b = _row("B", "/x", database_id=2, played_count=1, rating=80)
        self.assertEqual(pick_keeper([a, b]).persistent_id, "B")
        self.assertGreater(keep_key(a), keep_key(_row("C", "/x", database_id=10)))


class GroupTests(unittest.TestCase):
    def test_same_file_two_rows(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "cut.mp3"
            path.write_bytes(b"x")
            loc = str(path)
            groups = group_file_rows(
                [
                    _row("KEEP", loc, database_id=1, playlist_hits=2),
                    _row("DROP", loc, database_id=9, playlist_hits=0),
                    _row("CLOUD", ""),
                ]
            )
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0].keep.persistent_id, "KEEP")
            self.assertEqual([row.persistent_id for row in groups[0].extras], ["DROP"])

    def test_missing_file_is_ignored(self) -> None:
        groups = group_file_rows(
            [
                _row("A", "/no/such/file.mp3", database_id=1),
                _row("B", "/no/such/file.mp3", database_id=2),
            ]
        )
        self.assertEqual(groups, [])

    def test_singletons_are_not_dupes(self) -> None:
        with TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.mp3"
            b = Path(tmp) / "b.mp3"
            a.write_bytes(b"a")
            b.write_bytes(b"b")
            groups = group_file_rows([_row("A", str(a)), _row("B", str(b))])
            self.assertEqual(groups, [])


class ScanGuardTests(unittest.TestCase):
    def test_scan_requires_music(self) -> None:
        from ix_crate.music_dupes import MusicDupesError, scan_library

        with patch("ix_crate.music_dupes.music_running", return_value=False):
            with self.assertRaises(MusicDupesError):
                scan_library()


if __name__ == "__main__":
    unittest.main()
