from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.identify import is_placeholder_artist
from ix_crate.industry_stems import (
    crate_title_index,
    fold_title,
    industry_folder_title,
    is_industry_name,
    match_crate_artist,
    patch_nml_industry,
    patch_xml_industry,
    plan_crate_keepers,
    plan_industry_artists,
)
from ix_crate.stems_playlists import (
    DiskFile,
    _traktor_dir_file,
    filing_from_path,
    prefer_crate_files,
)


class IndustryNameTests(unittest.TestCase):
    def test_folder_spellings(self) -> None:
        self.assertTrue(is_industry_name("IndustryStems"))
        self.assertTrue(is_industry_name("Industry Stems"))
        self.assertTrue(is_industry_name("industry-stems"))
        self.assertFalse(is_industry_name("Style Industry"))
        self.assertTrue(is_placeholder_artist("IndustryStems"))

    def test_pack_prefix(self) -> None:
        self.assertEqual(industry_folder_title("01_Bohemian_Rhapsody_OG_Mix"), "Bohemian Rhapsody OG Mix")
        self.assertEqual(industry_folder_title("102_Wish"), "Wish")
        self.assertEqual(industry_folder_title("03_God_is_God"), "God is God")

    def test_fold_naive_im_and_censored_fuck(self) -> None:
        self.assertEqual(fold_title("Naïve"), fold_title("Naive"))
        self.assertEqual(fold_title("Control I'm Here"), fold_title("Control Im Here"))
        self.assertEqual(fold_title("What the F k Is Wrong With You"), "what the fuck is wrong with you")


class CrateMatchTests(unittest.TestCase):
    def test_matches_artist_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Nine Inch Nails" / "The Fragile").mkdir(parents=True)
            (root / "Nine Inch Nails" / "The Fragile" / "Wish.stem.m4a").write_bytes(b"stem")
            ind = root / "IndustryStems" / "102_Wish"
            ind.mkdir(parents=True)
            (ind / "vocals.wav").write_bytes(b"RIFF")
            artist, source = match_crate_artist("Wish", crate_title_index(root))
            self.assertEqual(artist, "Nine Inch Nails")
            self.assertEqual(source, "crate-exact")

    def test_remix_title_uses_crate_prefix(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Nitzer Ebb" / "Singles"
            dest.mkdir(parents=True)
            (dest / "Join In The Chant.stem.m4a").write_bytes(b"stem")
            artist, source = match_crate_artist(
                "Join In The Chant XPress 2 Remix 1", crate_title_index(root)
            )
            self.assertEqual(artist, "Nitzer Ebb")
            self.assertEqual(source, "crate-prefix")

    def test_remix_keeps_stem_when_prefix_pool_is_busy(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Nitzer Ebb" / "Singles"
            dest.mkdir(parents=True)
            (dest / "Control Im Here.stem.m4a").write_bytes(b"stem")
            artist, source = match_crate_artist(
                "Control Im Here The Hacker Remix 2006", crate_title_index(root)
            )
            self.assertEqual(artist, "Nitzer Ebb")
            self.assertEqual(source, "crate-prefix")

    def test_plan_resolves_without_catalog(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Juno Reactor" / "God Is God"
            dest.mkdir(parents=True)
            (dest / "God is God.stem.m4a").write_bytes(b"stem")
            pack = root / "IndustryStems" / "03_God_is_God"
            pack.mkdir(parents=True)
            (pack / "vocals.wav").write_bytes(b"RIFF")
            (pack / "drums.wav").write_bytes(b"RIFF")
            fixes = plan_industry_artists(stems_root=root, lookup=False)
            self.assertEqual(len(fixes), 1)
            self.assertEqual(fixes[0].artist, "Juno Reactor")
            self.assertEqual(fixes[0].title, "God is God")
            self.assertEqual(len(fixes[0].files), 2)


class FilingTests(unittest.TestCase):
    def test_industry_folder_is_not_the_artist(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "IndustryStems" / "03_God_is_God"
            dest.mkdir(parents=True)
            path = dest / "vocals.wav"
            path.write_bytes(b"RIFF")
            artist, _album, title = filing_from_path(path, root)
            self.assertEqual(title, "God is God")
            self.assertEqual(artist, "")


class PreferCrateTests(unittest.TestCase):
    def test_keeps_artist_folder_over_mashups(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / "Buddy Holly" / "Singles" / "Buddy Holly - Everyday.stem.m4a"
            dump = (
                root
                / "Compilations"
                / "Mashups"
                / "Buddy Holly"
                / "Buddy Holly - Everyday.stem.m4a"
            )
            keep.parent.mkdir(parents=True)
            dump.parent.mkdir(parents=True)
            keep.write_bytes(b"a")
            dump.write_bytes(b"b")
            files = [
                DiskFile(path=keep.resolve(), crate="Stems"),
                DiskFile(path=dump.resolve(), crate="Stems"),
            ]
            kept = prefer_crate_files(files, root)
            self.assertEqual([item.path for item in kept], [keep.resolve()])

    def test_does_not_collapse_two_untitled_mixes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "Pivots" / "Gave You My Love" / "mix.m4a"
            b = root / "Other Act" / "Gave You My Love" / "mix.m4a"
            a.parent.mkdir(parents=True)
            b.parent.mkdir(parents=True)
            a.write_bytes(b"a")
            b.write_bytes(b"b")
            files = [
                DiskFile(path=a.resolve(), crate="Mixes"),
                DiskFile(path=b.resolve(), crate="Mixes"),
            ]
            kept = prefer_crate_files(files, root)
            self.assertEqual(len(kept), 2)

    def test_keepers_report_drops_mashups_copy(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / "Queen" / "Flash Gordon" / "Flash.stem.m4a"
            dump = root / "Compilations" / "Mashups" / "Queen" / "Flash.stem.m4a"
            keep.parent.mkdir(parents=True)
            dump.parent.mkdir(parents=True)
            keep.write_bytes(b"a")
            dump.write_bytes(b"b")
            report = plan_crate_keepers(stems_root=root)
            self.assertEqual(len(report), 1)
            self.assertEqual(report[0].crate, "Stems")
            self.assertEqual(Path(report[0].keep), keep.resolve())
            self.assertEqual(report[0].dropped, [str(dump.resolve())])


class NmlPatchTests(unittest.TestCase):
    def test_sets_artist_on_wav_rows(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Juno Reactor" / "Singles"
            dest.mkdir(parents=True)
            (dest / "God is God.stem.m4a").write_bytes(b"stem")
            pack = root / "IndustryStems" / "03_God_is_God"
            pack.mkdir(parents=True)
            vocals = pack / "vocals.wav"
            vocals.write_bytes(b"RIFF")
            directory, file_attr = _traktor_dir_file(vocals.resolve())
            nml = Path(tmp) / "collection.nml"
            nml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<NML VERSION=\"20\">"
                "<COLLECTION ENTRIES=\"1\">"
                f'<ENTRY TITLE="vocals" ARTIST="IndustryStems">'
                f'<LOCATION DIR="{directory}" FILE="{file_attr}" VOLUME="Macintosh HD"/>'
                '<ALBUM TITLE="IndustryStems"/>'
                "</ENTRY></COLLECTION></NML>",
                encoding="utf-8",
            )
            fixes = plan_industry_artists(stems_root=root, lookup=False)
            patched = patch_nml_industry(fixes, nml=nml, execute=True)
            self.assertEqual(patched, 1)
            entry = ET.parse(nml).find("COLLECTION/ENTRY")
            self.assertEqual(entry.get("ARTIST"), "Juno Reactor")
            self.assertEqual(entry.get("TITLE"), "God is God")

    def test_xml_patch_sets_artist(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Juno Reactor" / "Singles"
            dest.mkdir(parents=True)
            (dest / "God is God.stem.m4a").write_bytes(b"stem")
            pack = root / "IndustryStems" / "03_God_is_God"
            pack.mkdir(parents=True)
            vocals = pack / "vocals.wav"
            vocals.write_bytes(b"RIFF")
            xml = Path(tmp) / "rekordbox.xml"
            from ix_crate.stems_playlists import _rb_location

            xml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<DJ_PLAYLISTS Version="1.0.0"><COLLECTION Entries="1">'
                f'<TRACK TrackID="3" Name="vocals" Artist="IndustryStems" '
                f'Location="{_rb_location(vocals.resolve())}"/>'
                "</COLLECTION></DJ_PLAYLISTS>",
                encoding="utf-8",
            )
            fixes = plan_industry_artists(stems_root=root, lookup=False)
            patched = patch_xml_industry(fixes, xml=xml, execute=True)
            self.assertEqual(patched, 1)
            track = ET.parse(xml).find("COLLECTION/TRACK")
            self.assertEqual(track.get("Artist"), "Juno Reactor")
            self.assertEqual(track.get("Name"), "God is God")

    def test_listen_fills_unresolved_remix(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = root / "IndustryStems" / "Murderous_Phil_Kieran_Remix"
            pack.mkdir(parents=True)
            (pack / "vocals.wav").write_bytes(b"RIFF")
            from unittest.mock import patch

            with (
                patch(
                    "ix_crate.industry_stems._catalog_artist",
                    return_value=("", "", ""),
                ),
                patch(
                    "ix_crate.industry_stems._listen_artist",
                    return_value=("Nitzer Ebb", "That Total Age", "shazam"),
                ),
            ):
                fixes = plan_industry_artists(stems_root=root, lookup=True)
            self.assertEqual(fixes[0].artist, "Nitzer Ebb")
            self.assertEqual(fixes[0].source, "shazam")


if __name__ == "__main__":
    unittest.main()
