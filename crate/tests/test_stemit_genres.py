from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.stemit_genres import GENRES_FOLDER, UNTAGGED, apply_genre_crates
from ix_crate.music_genre import clean_genre
from ix_crate.stems_playlists import DiskFile, _traktor_dir_file, _traktor_key, write_rekordbox, write_traktor


class CleanGenreAliasTests(unittest.TestCase):
    def test_import_clean(self) -> None:
        self.assertEqual(clean_genre("EDM, House, Deep"), "Deep House")


class GenreCrateTests(unittest.TestCase):
    def test_builds_genre_role_playlists(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            house = root / "Kettama" / "Singles"
            house.mkdir(parents=True)
            mix = house / "Fly Away.m4a"
            stem = house / "Fly Away.stem.m4a"
            mix.write_bytes(b"mix")
            stem.write_bytes(b"stem")
            nml = Path(tmp) / "collection.nml"
            loc_m, file_m = _traktor_dir_file(mix.resolve())
            loc_s, file_s = _traktor_dir_file(stem.resolve())
            nml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<NML VERSION=\"20\">"
                '<COLLECTION ENTRIES="2">'
                f'<ENTRY TITLE="Fly Away" ARTIST="Kettama">'
                f'<LOCATION DIR="{loc_m}" FILE="{file_m}" VOLUME="Macintosh HD"/>'
                '<INFO GENRE="EDM, House, Deep"/>'
                "</ENTRY>"
                f'<ENTRY TITLE="Fly Away" ARTIST="Kettama">'
                f'<LOCATION DIR="{loc_s}" FILE="{file_s}" VOLUME="Macintosh HD"/>'
                '<INFO GENRE="EDM, House, Deep"/>'
                "</ENTRY></COLLECTION>"
                "<PLAYLISTS><NODE TYPE=\"FOLDER\" NAME=\"$ROOT\">"
                '<SUBNODES COUNT="0"/></NODE></PLAYLISTS></NML>',
                encoding="utf-8",
            )
            files = [
                DiskFile(path=mix.resolve(), crate="Mixes"),
                DiskFile(path=stem.resolve(), crate="Stems"),
            ]
            index = {
                mix.resolve(): _traktor_key(mix.resolve()),
                stem.resolve(): _traktor_key(stem.resolve()),
            }
            tree = ET.parse(nml)
            apply_genre_crates(tree.getroot(), files, index, root)
            tree.write(nml, encoding="UTF-8", xml_declaration=True)
            tree = ET.parse(nml)
            genre_el = tree.find("COLLECTION/ENTRY/INFO")
            self.assertEqual(genre_el.get("GENRE"), "Deep House")
            genres = [
                node
                for node in tree.getroot().iter("NODE")
                if node.get("TYPE") == "FOLDER" and node.get("NAME") == GENRES_FOLDER
            ][0]
            names = [n.get("NAME") for n in genres.find("SUBNODES").findall("NODE")]
            self.assertEqual(names, ["Deep House"])
            deep = genres.find("SUBNODES").find("NODE")
            roles = [n.get("NAME") for n in deep.find("SUBNODES").findall("NODE")]
            self.assertEqual(list(roles), ["Mixes", "Stems", "Acapellas", "Instrumentals"])
            mixes = next(
                n.find("PLAYLIST")
                for n in deep.find("SUBNODES").findall("NODE")
                if n.get("NAME") == "Mixes"
            )
            self.assertEqual(mixes.get("ENTRIES"), "1")
            stems = next(
                n.find("PLAYLIST")
                for n in deep.find("SUBNODES").findall("NODE")
                if n.get("NAME") == "Stems"
            )
            self.assertEqual(stems.get("ENTRIES"), "1")

    def test_patches_extra_collection_rows(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            album = root / "Chic" / "Best"
            album.mkdir(parents=True)
            mix = album / "Le Freak.m4a"
            extra = album / "Le Freak_vocals.m4a"
            mix.write_bytes(b"mix")
            extra.write_bytes(b"voc")
            loc_m, file_m = _traktor_dir_file(mix.resolve())
            loc_e, file_e = _traktor_dir_file(extra.resolve())
            nml = Path(tmp) / "collection.nml"
            nml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<NML VERSION=\"20\">"
                '<COLLECTION ENTRIES="2">'
                f'<ENTRY TITLE="Le Freak" ARTIST="Chic">'
                f'<LOCATION DIR="{loc_m}" FILE="{file_m}" VOLUME="Macintosh HD"/>'
                '<INFO GENRE="House"/>'
                "</ENTRY>"
                f'<ENTRY TITLE="Le Freak" ARTIST="Chic">'
                f'<LOCATION DIR="{loc_e}" FILE="{file_e}" VOLUME="Macintosh HD"/>'
                '<INFO GENRE="EDM, House, Funk / Soul / Disco"/>'
                "</ENTRY></COLLECTION>"
                "<PLAYLISTS><NODE TYPE=\"FOLDER\" NAME=\"$ROOT\">"
                '<SUBNODES COUNT="0"/></NODE></PLAYLISTS></NML>',
                encoding="utf-8",
            )
            files = [DiskFile(path=mix.resolve(), crate="Mixes")]
            index = {mix.resolve(): _traktor_key(mix.resolve())}
            tree = ET.parse(nml)
            apply_genre_crates(tree.getroot(), files, index, root)
            genres = [
                e.find("INFO").get("GENRE")
                for e in tree.getroot().find("COLLECTION").findall("ENTRY")
            ]
            self.assertEqual(genres, ["House", "Funk / Soul / Disco"])

    def test_write_traktor_appends_genres_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            album = root / "Moby" / "Play"
            album.mkdir(parents=True)
            mix = album / "Honey.m4a"
            mix.write_bytes(b"mix")
            nml = Path(tmp) / "collection.nml"
            nml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<NML VERSION=\"20\">"
                '<COLLECTION ENTRIES="0"/>'
                "<PLAYLISTS><NODE TYPE=\"FOLDER\" NAME=\"$ROOT\">"
                '<SUBNODES COUNT="0"/></NODE></PLAYLISTS></NML>',
                encoding="utf-8",
            )
            write_traktor(
                [DiskFile(path=mix.resolve(), crate="Mixes")],
                {},
                nml,
                stems_root=root,
            )
            stemit = [
                node
                for node in ET.parse(nml).getroot().iter("NODE")
                if node.get("TYPE") == "FOLDER" and node.get("NAME") == "STEMIT"
            ][0]
            kids = [n.get("NAME") for n in stemit.find("SUBNODES").findall("NODE")]
            self.assertIn(GENRES_FOLDER, kids)
            self.assertEqual(kids[-1], GENRES_FOLDER)
            self.assertIn(UNTAGGED, ET.tostring(stemit, encoding="unicode"))

    def test_write_rekordbox_nested_genre_crates(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            album = root / "Kettama" / "Singles"
            album.mkdir(parents=True)
            mix = album / "Fly Away.m4a"
            stem = album / "Fly Away.stem.m4a"
            mix.write_bytes(b"mix")
            stem.write_bytes(b"stem")
            loc_m, file_m = _traktor_dir_file(mix.resolve())
            loc_s, file_s = _traktor_dir_file(stem.resolve())
            nml = Path(tmp) / "collection.nml"
            nml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<NML VERSION=\"20\">"
                '<COLLECTION ENTRIES="2">'
                f'<ENTRY TITLE="Fly Away" ARTIST="Kettama">'
                f'<LOCATION DIR="{loc_m}" FILE="{file_m}" VOLUME="Macintosh HD"/>'
                '<INFO GENRE="Deep House"/>'
                "</ENTRY>"
                f'<ENTRY TITLE="Fly Away" ARTIST="Kettama">'
                f'<LOCATION DIR="{loc_s}" FILE="{file_s}" VOLUME="Macintosh HD"/>'
                '<INFO GENRE="Deep House"/>'
                "</ENTRY></COLLECTION>"
                "<PLAYLISTS><NODE TYPE=\"FOLDER\" NAME=\"$ROOT\">"
                '<SUBNODES COUNT="0"/></NODE></PLAYLISTS></NML>',
                encoding="utf-8",
            )
            xml = Path(tmp) / "rekordbox.xml"
            xml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<DJ_PLAYLISTS Version="1.0.0">'
                '<COLLECTION Entries="0"/>'
                "<PLAYLISTS/>"
                "</DJ_PLAYLISTS>",
                encoding="utf-8",
            )
            files = [
                DiskFile(path=mix.resolve(), crate="Mixes"),
                DiskFile(path=stem.resolve(), crate="Stems"),
            ]
            write_rekordbox(files, {}, xml, stems_root=root, nml=nml)
            tree = ET.parse(xml)
            stemit = [
                node
                for node in tree.getroot().iter("NODE")
                if node.get("Type") == "0" and node.get("Name") == "STEMIT"
            ][0]
            kids = [n.get("Name") for n in stemit.findall("NODE")]
            self.assertEqual(kids[:4], ["Mixes", "Stems", "Acapellas", "Instrumentals"])
            self.assertEqual(kids[-1], GENRES_FOLDER)
            genres = next(n for n in stemit.findall("NODE") if n.get("Name") == GENRES_FOLDER)
            deep = next(n for n in genres.findall("NODE") if n.get("Name") == "Deep House")
            roles = [n.get("Name") for n in deep.findall("NODE")]
            self.assertEqual(roles, ["Mixes", "Stems", "Acapellas", "Instrumentals"])
            mixes = next(n for n in deep.findall("NODE") if n.get("Name") == "Mixes")
            self.assertEqual(mixes.get("Entries"), "1")
            self.assertEqual(mixes.get("Type"), "1")


if __name__ == "__main__":
    unittest.main()
