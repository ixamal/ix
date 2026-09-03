import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.music_repair import RepairRow, index_tree, pick_match, title_keys_for


def _row(
    name: str,
    *,
    artist: str = "Artist",
    album: str = "Album",
    genre: str = "House",
    duration: float = 180,
) -> RepairRow:
    return RepairRow(
        persistent_id="ABC123",
        database_id=1,
        artist=artist,
        album=album,
        name=name,
        genre=genre,
        duration=duration,
        location="",
    )


class TitleKeysTests(unittest.TestCase):
    def test_slash_compilation_name(self) -> None:
        keys = title_keys_for(_row("Revolt / Relax [Lemon 8 Remix]"))
        self.assertIn("relax lemon 8 remix", keys)


class PickMatchTests(unittest.TestCase):
    def test_unique_artist_title(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "A1 Bassline" / "Pets" / "14 Breakaway (Original Mix).mp3"
            dest.parent.mkdir(parents=True)
            dest.write_bytes(b"x")
            index = index_tree(root)
            path, reason = pick_match(
                _row("Breakaway (Original Mix)", artist="A1 Bassline", album="Pets"),
                index,
            )
            self.assertEqual(path, dest)
            self.assertEqual(reason, "artist+title")

    def test_music_copy_subdir_is_not_artist(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = (
                root
                / "Music"
                / "CHANEY (UK)"
                / "Holding Onto You"
                / "Holding Onto You (Extended Mix).mp3"
            )
            dest.parent.mkdir(parents=True)
            dest.write_bytes(b"x")
            index = index_tree(root)
            path, reason = pick_match(
                _row(
                    "Holding Onto You (Extended Mix)",
                    artist="CHANEY (UK)",
                    album="Holding Onto You",
                ),
                index,
            )
            self.assertEqual(path, dest)
            self.assertEqual(reason, "artist+title")

    def test_album_breaks_tie(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "Aphex Twin" / "Ventolin" / "01 Ventolin (Salbutamol Mix).m4a"
            b = root / "Aphex Twin" / "Ventolin [EP]" / "01 Ventolin (Salbutamol Mix).m4a"
            for path in (a, b):
                path.parent.mkdir(parents=True)
                path.write_bytes(b"x")
            index = index_tree(root)
            path, reason = pick_match(
                _row(
                    "Ventolin (Salbutamol Mix)",
                    artist="Aphex Twin",
                    album="Ventolin [EP]",
                ),
                index,
            )
            self.assertEqual(path, b)
            self.assertIn("album", reason)

    def test_apostrophe_artist(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = (
                root
                / "16 Bit Lolita's"
                / "Passing Lights"
                / "01 Passing Lights.m4a"
            )
            dest.parent.mkdir(parents=True)
            dest.write_bytes(b"x")
            index = index_tree(root)
            path, reason = pick_match(
                _row("Passing Lights", artist="16 Bit Lolitas", album="Passing Lights"),
                index,
            )
            self.assertEqual(path, dest)
            self.assertEqual(reason, "artist+title")

    def test_generic_title_uses_album(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Compilations" / "Cream Live [Disc 1]" / "01 Track 01.m4a"
            dest.parent.mkdir(parents=True)
            dest.write_bytes(b"x")
            index = index_tree(root)
            path, reason = pick_match(
                _row("Track 01", artist="", album="Cream Live [Disc 1]"),
                index,
            )
            self.assertEqual(path, dest)
            self.assertEqual(reason, "album+title")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Other" / "Singles" / "Unrelated.mp3"
            dest.parent.mkdir(parents=True)
            dest.write_bytes(b"x")
            index = index_tree(root)
            path, reason = pick_match(_row("Missing Song", artist="Ghost"), index)
            self.assertIsNone(path)
            self.assertEqual(reason, "")


class AppleDoubleTest(unittest.TestCase):
    def test_appledouble_stub_is_not_indexed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            album = root / "Moby" / "Play"
            album.mkdir(parents=True)
            real = album / "01 Honey.mp3"
            real.write_bytes(b"x")
            (album / "._01 Honey.mp3").write_bytes(b"x")
            index = index_tree(root)
            hits = [h.path for hits in index["by_title"].values() for h in hits]
            self.assertEqual(hits, [real])
