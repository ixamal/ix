import unittest

from pathlib import Path

from ix_crate.acoustid import parse_acoustid
from ix_crate.identify import Identity, filename_hints_artist, parse_filename
from ix_crate.music_fix import choose_album, is_junk_album, plan_fix_row, salvage_title, title_is_junk
from ix_crate.music_repair import RepairRow
from ix_crate.shazam import parse_shazam


class JunkAlbumTests(unittest.TestCase):
    def test_dump_folder_is_junk(self) -> None:
        self.assertTrue(is_junk_album("Rain or Shine Summer"))
        self.assertTrue(is_junk_album("Unknown Album"))
        self.assertFalse(is_junk_album("Cream Live [Disc 1]"))
        self.assertFalse(is_junk_album("The Darkness Forever"))


class NumberedParseTests(unittest.TestCase):
    def test_collide_album_in_name(self) -> None:
        artist, album, title = parse_filename(
            "Collide - The Darkness Forever - 01 Wandering Star"
        )
        self.assertEqual(artist, "Collide")
        self.assertEqual(album, "The Darkness Forever")
        self.assertIn("Wandering Star", title)


class FilenameHintTests(unittest.TestCase):
    def test_dash_name_hints_artist(self) -> None:
        self.assertTrue(filename_hints_artist("Bonobo - Kong"))
        self.assertFalse(filename_hints_artist("04 Girl without a Planet (Slut of Saturn Mix)"))
        self.assertFalse(filename_hints_artist("Track 01"))


class ChooseAlbumTests(unittest.TestCase):
    def test_keep_cream_live(self) -> None:
        self.assertEqual(choose_album("Cream Live [Disc 1]", "Singles", "Someone"), "")

    def test_dump_becomes_singles(self) -> None:
        self.assertEqual(choose_album("Rain or Shine Summer", "", "Bonobo"), "Singles")

    def test_catalog_album_replaces_unknown(self) -> None:
        self.assertEqual(
            choose_album("Unknown Album", "The Darkness Forever", "Collide"),
            "The Darkness Forever",
        )


class SalvageTitleTests(unittest.TestCase):
    def test_named_dump_keeps_words(self) -> None:
        row = RepairRow(
            persistent_id="X",
            database_id=1,
            artist="",
            album="Rain or Shine Summer",
            name="03-killer queen",
            genre="",
            duration=180,
            location="/tmp/03-killer queen.m4a",
        )
        self.assertEqual(
            salvage_title(row, Path("/tmp/03-killer queen.m4a")),
            "03-killer queen",
        )

    def test_track_nn_uses_album_and_number(self) -> None:
        row = RepairRow(
            persistent_id="X",
            database_id=1,
            artist="",
            album="Cream Live [Disc 1]",
            name="Track 01",
            genre="",
            duration=180,
            location="/tmp/01 Track 01.m4a",
        )
        self.assertEqual(
            salvage_title(row, Path("/tmp/01 Track 01.m4a")),
            "Cream Live [Disc 1] 01",
        )


class AcoustidParseTests(unittest.TestCase):
    def test_picks_duration_matched_recording(self) -> None:
        payload = {
            "status": "ok",
            "results": [
                {
                    "score": 0.96,
                    "recordings": [
                        {
                            "title": "Folsom Prison Blues",
                            "duration": 162,
                            "artists": [{"name": "Johnny Cash"}],
                            "releasegroups": [{"title": "At Folsom Prison"}],
                        }
                    ],
                }
            ],
        }
        hit = parse_acoustid(payload, 161.5)
        self.assertIsNotNone(hit)
        self.assertEqual(hit["artist"], "Johnny Cash")
        self.assertEqual(hit["title"], "Folsom Prison Blues")
        self.assertTrue(hit.get("duration_match"))


class TitleJunkTests(unittest.TestCase):
    def test_dump_album_prefixed_title(self) -> None:
        row = RepairRow(
            persistent_id="X",
            database_id=1,
            artist="Various Artists",
            album="Rain or Shine Summer",
            name="Rain or Shine Summer 01",
            genre="",
            duration=296,
            location="/tmp/01 Track 01.m4a",
        )
        self.assertTrue(title_is_junk(row))


class ShazamParseTests(unittest.TestCase):
    def test_artist_title_album_genre(self) -> None:
        payload = {
            "track": {
                "title": "Driftin'",
                "subtitle": "Sun Orchestra",
                "genres": {"primary": "Dance"},
                "sections": [
                    {"metadata": [{"title": "Album", "text": "Deep And Sexy"}]}
                ],
            }
        }
        hit = parse_shazam(payload)
        self.assertIsNotNone(hit)
        self.assertEqual(hit["artist"], "Sun Orchestra")
        self.assertEqual(hit["title"], "Driftin'")
        self.assertEqual(hit["album"], "Deep And Sexy")
        self.assertEqual(hit["genre"], "Dance")
        self.assertEqual(hit["source"], "shazam")

    def test_empty_track_is_none(self) -> None:
        self.assertIsNone(parse_shazam({"track": {}}))


class NoSalvageTests(unittest.TestCase):
    def test_unidentified_is_not_various_artists(self) -> None:
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "01 Track 01.m4a"
            path.write_bytes(b"x")
            row = RepairRow(
                persistent_id="ABC123",
                database_id=1,
                artist="Various Artists",
                album="Rain or Shine Summer",
                name="Rain or Shine Summer 01",
                genre="",
                duration=296,
                location=str(path),
            )
            with patch(
                "ix_crate.music_fix.resolve",
                return_value=Identity(artist="", album="", title="", source="acoustid"),
            ):
                self.assertIsNone(plan_fix_row(row, aggressive=True))
