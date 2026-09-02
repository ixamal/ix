import unittest
from pathlib import Path

from ix_crate.families import family_key
from ix_crate.identify import (
    duration_close,
    is_clip_name,
    is_mashup_name,
    is_placeholder_album_folder,
    is_placeholder_title,
    parse_filename,
    strip_track_number,
    titles_match,
)
from ix_crate.lookup import artist_named_in_text, catalog_worth_query, pick_catalog_hit
from ix_crate.mashup import dest_mashup_artist, parse_mashup_artist


class FamilyKeyTests(unittest.TestCase):
    def test_strips_stem_and_role(self) -> None:
        self.assertEqual(
            family_key(Path("Freqax - Tear You Apart.stem.m4a")),
            "Freqax - Tear You Apart",
        )
        self.assertEqual(
            family_key(Path("Freqax - Tear You Apart - vocals.m4a")),
            "Freqax - Tear You Apart",
        )
        self.assertEqual(
            family_key(Path("Freqax - Tear You Apart - instrumental.m4a")),
            "Freqax - Tear You Apart",
        )
        self.assertEqual(
            family_key(Path("Freqax - Tear You Apart.mp3")),
            "Freqax - Tear You Apart",
        )

    def test_strips_underscore_vocals(self) -> None:
        self.assertEqual(
            family_key(Path("Queen - Flash (Official Video)_vocals.m4a")),
            "Queen - Flash (Official Video)",
        )

    def test_strips_paren_acapella(self) -> None:
        self.assertEqual(
            family_key(Path("The Orb - Buddhist Hipsters - 01 Spontaneously Combust (acapella).mp3")),
            "The Orb - Buddhist Hipsters - 01 Spontaneously Combust",
        )
        self.assertEqual(
            family_key(Path("The Orb - Buddhist Hipsters - 01 Spontaneously Combust (instrumental).mp3")),
            "The Orb - Buddhist Hipsters - 01 Spontaneously Combust",
        )


class ParseFilenameTests(unittest.TestCase):
    def test_artist_title(self) -> None:
        artist, album, title = parse_filename("Don Diablo & CID - Fever")
        self.assertEqual(artist, "Don Diablo & CID")
        self.assertEqual(album, "")
        self.assertEqual(title, "Fever")

    def test_underscore_and_pipe(self) -> None:
        artist, album, title = parse_filename("Gorgon City _ 5AM At Bagleys")
        self.assertEqual(artist, "Gorgon City")
        self.assertEqual(title, "5AM At Bagleys")
        artist, album, title = parse_filename("Wiley | And Again [CLB Edit]")
        self.assertEqual(artist, "Wiley")
        self.assertIn("And Again", title)

    def test_long_underscore_stays_unparsed(self) -> None:
        artist, album, title = parse_filename(
            "You reposted in the wrong neighborhood _ Short Lyrics"
        )
        self.assertEqual(artist, "")
        self.assertIn("You reposted", title)

    def test_mix_title_is_not_an_artist(self) -> None:
        artist, album, title = parse_filename(
            "Dark 80_s Synthwave Mix _ Vol.4 _ Stranger Synths"
        )
        self.assertEqual(artist, "")
        self.assertIn("Synthwave Mix", title)

    def test_artist_album_title(self) -> None:
        artist, album, title = parse_filename(
            "Front Line Assembly - Mechviruses - 08 Heatmap feat. Cardinal Noire"
        )
        self.assertEqual(artist, "Front Line Assembly")
        self.assertEqual(album, "Mechviruses")
        self.assertEqual(title, "08 Heatmap feat. Cardinal Noire")

    def test_strips_tuberipper(self) -> None:
        artist, album, title = parse_filename(
            "Right Said Fred - Im Too Sexy (Original Mix - 2006 Version) [TubeRipper.cc]"
        )
        self.assertEqual(artist, "Right Said Fred")
        self.assertNotIn("TubeRipper", title)
        self.assertIn("Original Mix", title)

    def test_clean_official_video(self) -> None:
        from ix_crate.identify import clean_text

        self.assertEqual(clean_text("Flash (Official Video)"), "Flash")

    def test_outliers_go_to_miscellaneous(self) -> None:
        from ix_crate.identify import Identity
        from ix_crate.paths import MISC_ALBUM, MISC_ARTIST

        ident = Identity(artist="", album="", title="clip", source="outlier")
        self.assertEqual(ident.dest_artist, MISC_ARTIST)
        self.assertEqual(ident.dest_album, MISC_ALBUM)
        self.assertNotIn("unknown", ident.dest_artist.lower())
        self.assertNotIn("unknown", ident.dest_album.lower())

    def test_orb_album_title(self) -> None:
        artist, album, title = parse_filename(
            "The Orb - Buddhist Hipsters - 01 Spontaneously Combust"
        )
        self.assertEqual(artist, "The Orb")
        self.assertEqual(album, "Buddhist Hipsters")
        self.assertEqual(title, "01 Spontaneously Combust")

    def test_undefined_tag_is_placeholder(self) -> None:
        self.assertTrue(is_placeholder_title("undefined (instrumental)"))
        self.assertTrue(is_placeholder_title("instrumental"))
        self.assertTrue(is_placeholder_title("Track 01"))
        self.assertTrue(is_placeholder_title("track 9"))
        self.assertFalse(is_placeholder_title("01 Spontaneously Combust"))


class CatalogMatchTests(unittest.TestCase):
    def test_strips_track_number(self) -> None:
        self.assertEqual(strip_track_number("03 As Alive As You Need Me To Be"), "As Alive As You Need Me To Be")
        self.assertEqual(strip_track_number("12 Who Wants To Live Forever_"), "Who Wants To Live Forever")

    def test_titles_match_ignores_number(self) -> None:
        self.assertTrue(titles_match("03 As Alive As You Need Me To Be", "As Alive As You Need Me To Be"))

    def test_mashup_and_clip(self) -> None:
        self.assertTrue(is_mashup_name("Stayin' in Black (Bee Gees + AC/DC Mashup) by Wax Audio"))
        self.assertTrue(is_mashup_name("Gorillaz vs. The Killers- Somebody Told Me to Feel Good"))
        self.assertTrue(is_clip_name("ScreenRecording_08-09-2025 16-30-33_1"))
        self.assertFalse(is_mashup_name("03 As Alive As You Need Me To Be"))

    def test_duration_close(self) -> None:
        self.assertTrue(duration_close(237.0, 236.2))
        self.assertFalse(duration_close(237.0, 297.0))

    def test_pick_requires_duration(self) -> None:
        hits = [
            {
                "artist": "Queen",
                "album": "A Kind of Magic",
                "title": "Who Wants to Live Forever",
                "duration": 297.0,
            },
            {
                "artist": "Nine Inch Nails",
                "album": "TRON: Ares",
                "title": "Who Wants to Live Forever",
                "duration": 350.0,
            },
        ]
        picked = pick_catalog_hit(hits, "12 Who Wants To Live Forever_", 350.0)
        self.assertIsNotNone(picked)
        self.assertEqual(picked["artist"], "Nine Inch Nails")
        self.assertIsNone(pick_catalog_hit(hits, "12 Who Wants To Live Forever_", None))

    def test_ollama_artist_must_be_named(self) -> None:
        self.assertTrue(artist_named_in_text("Gorgon City", "Gorgon City _ 5AM At Bagleys"))
        self.assertFalse(artist_named_in_text("Michael Jackson", "Aftershock"))

    def test_short_untitled_skips_catalog(self) -> None:
        self.assertFalse(catalog_worth_query("FLO", ""))
        self.assertTrue(catalog_worth_query("Midnight City", ""))


class MashupParseTests(unittest.TestCase):
    def test_known_mashers(self) -> None:
        self.assertEqual(
            parse_mashup_artist("Stayin' in Black (Bee Gees + AC/DC Mashup) by Wax Audio"),
            "Wax Audio",
        )
        self.assertEqual(
            parse_mashup_artist("Chili Peppers All Star Mashup _ Pomplamoose"),
            "Pomplamoose",
        )
        self.assertEqual(
            parse_mashup_artist("Al Corley Vs Ace of Base Paolo Monti megamashup 2013"),
            "Paolo Monti",
        )

    def test_vs_and_credits(self) -> None:
        self.assertEqual(
            parse_mashup_artist("Gorillaz vs. The Killers- Somebody Told Me to Feel Good"),
            "Gorillaz vs. The Killers",
        )
        self.assertEqual(
            parse_mashup_artist("Korn vs. Britney Spears - Toxic Transistor"),
            "Korn vs. Britney Spears",
        )
        self.assertEqual(
            parse_mashup_artist("Levitating x Baby One More Time _ Mashup of Dua Lipa_Britney Spears"),
            "Dua Lipa x Britney Spears",
        )
        self.assertEqual(
            parse_mashup_artist("Midnight Sky x In Your Eyes (MASHUP) – Miley Cyrus x The Weeknd"),
            "Miley Cyrus x The Weeknd",
        )
        self.assertEqual(
            parse_mashup_artist("Crazy Little Thing Called Rehab (Amy Winehouse vs. Queen)"),
            "Amy Winehouse vs. Queen",
        )

    def test_fallback_various(self) -> None:
        self.assertEqual(
            parse_mashup_artist("Best Rock EDM Mashup Remix ... Summer 2019 Reboot"),
            "Various Artists",
        )

    def test_dest_path(self) -> None:
        from ix_crate.identify import Identity

        ident = Identity(artist="Pomplamoose", album="Mashups", title="x", source="mashup")
        self.assertEqual(ident.dest_artist, "Compilations")
        self.assertEqual(ident.dest_album, "Mashups/Pomplamoose")
        self.assertNotIn("unknown", ident.dest_album.lower())

    def test_parent_folder_wins_when_mashup_named(self) -> None:
        self.assertEqual(
            dest_mashup_artist(
                "Coldplay vs Imagine Dragons vs Sia - Viva La Vida Titanium Radioactive",
                "Coldplay vs Imagine Dragons vs Sia",
            ),
            "Coldplay vs Imagine Dragons vs Sia",
        )
        self.assertEqual(
            dest_mashup_artist("DJ Cummerbund - WarMCA", "DJ Cummerbund"),
            "DJ Cummerbund",
        )
        self.assertEqual(
            dest_mashup_artist(
                "Coldplay feat. Alan Walker - The Faded Scientist",
                "Coldplay feat. Alan Walker",
            ),
            "Coldplay feat. Alan Walker",
        )
        self.assertEqual(
            dest_mashup_artist(
                "Deadmau5, Cypress Hill - Failbait (First Mix)",
                "deadmau5",
            ),
            "deadmau5",
        )
        self.assertEqual(
            dest_mashup_artist("Play That Funky Music Rammstein", "DJ Cummerbund"),
            "DJ Cummerbund",
        )

    def test_placeholder_album_folder(self) -> None:
        self.assertTrue(is_placeholder_album_folder("Unknown Album"))
        self.assertTrue(is_placeholder_album_folder("_ album title goes here _"))
        self.assertTrue(is_placeholder_album_folder("__ album title goes here __"))
        self.assertFalse(is_placeholder_album_folder("What the F__k Is Wrong With You People_"))


if __name__ == "__main__":
    unittest.main()
