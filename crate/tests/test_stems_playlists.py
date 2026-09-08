from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.stems_playlists import (
    classify,
    sync_playlists,
    walk_stems,
)


class ClassifyTests(unittest.TestCase):
    def test_stem_container(self) -> None:
        self.assertEqual(classify(Path("Honey.stem.m4a")), "Stems")
        self.assertEqual(classify(Path("Honey.stem (2).m4a")), "Stems")

    def test_vocals_pair(self) -> None:
        self.assertEqual(classify(Path("Honey - vocals.m4a")), "Acapellas")

    def test_acapella_paren(self) -> None:
        self.assertEqual(classify(Path("Let It Go (acapella).mp3")), "Acapellas")

    def test_instrumental_pair(self) -> None:
        self.assertEqual(classify(Path("Honey - instrumental.m4a")), "Instrumentals")

    def test_mix_is_mixes_crate(self) -> None:
        self.assertEqual(classify(Path("Honey (Original Mix).m4a")), "Mixes")

    def test_vocal_club_mix_is_mix_not_acapella(self) -> None:
        self.assertEqual(
            classify(Path("What Planet You On (Bodyrox Vocal Club Mix).mp3")),
            "Mixes",
        )


class WalkTests(unittest.TestCase):
    def test_walks_mix_and_role_and_stem(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            album = root / "Moby" / "Play"
            album.mkdir(parents=True)
            (album / "Honey.m4a").write_bytes(b"mix")
            (album / "Honey.stem.m4a").write_bytes(b"stem")
            (album / "Honey - vocals.m4a").write_bytes(b"vox")
            (album / "Honey - instrumental.m4a").write_bytes(b"inst")
            (album / "Honey.stem (2).m4a").write_bytes(b"dup")
            files = walk_stems(root)
            crates = {item.path.name: item.crate for item in files}
            self.assertEqual(
                crates,
                {
                    "Honey.m4a": "Mixes",
                    "Honey.stem.m4a": "Stems",
                    "Honey - vocals.m4a": "Acapellas",
                    "Honey - instrumental.m4a": "Instrumentals",
                },
            )


class SyncExecuteTests(unittest.TestCase):
    def test_execute_adds_collection_rows_and_playlists(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            album = root / "Moby" / "Play"
            album.mkdir(parents=True)
            mix = album / "Honey.m4a"
            stem = album / "Honey.stem.m4a"
            mix.write_bytes(b"mix")
            stem.write_bytes(b"stem")
            nml = Path(tmp) / "collection.nml"
            nml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<NML VERSION=\"20\">"
                '<COLLECTION ENTRIES="0"/>'
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
            plan = sync_playlists(
                execute=True, stems_root=root, nml=nml, xml=xml
            )
            self.assertEqual(plan.added_traktor, 2)
            self.assertEqual(plan.added_rekordbox, 2)
            ntree = ET.parse(nml)
            names = [
                node.get("NAME")
                for node in ntree.getroot().iter("NODE")
                if node.get("TYPE") == "PLAYLIST"
            ]
            self.assertIn("Mixes", names)
            self.assertIn("Stems", names)
            mixes = [
                node.find("PLAYLIST")
                for node in ntree.getroot().iter("NODE")
                if node.get("TYPE") == "PLAYLIST" and node.get("NAME") == "Mixes"
            ][0]
            self.assertEqual(mixes.get("TYPE"), "LIST")
            self.assertTrue(mixes.get("UUID"))
            again = sync_playlists(
                execute=True, stems_root=root, nml=nml, xml=xml
            )
            self.assertEqual(again.added_traktor, 0)
            mixes2 = [
                node.find("PLAYLIST")
                for node in ET.parse(nml).getroot().iter("NODE")
                if node.get("TYPE") == "PLAYLIST" and node.get("NAME") == "Mixes"
            ][0]
            self.assertEqual(mixes2.get("TYPE"), "LIST")
            self.assertEqual(mixes2.get("UUID"), mixes.get("UUID"))
            stemit = [
                node
                for node in ET.parse(nml).getroot().iter("NODE")
                if node.get("TYPE") == "FOLDER" and node.get("NAME") == "STEMIT"
            ][0]
            mix_nodes = [
                node
                for node in stemit.find("SUBNODES").findall("NODE")
                if node.get("NAME") == "Mixes"
            ]
            self.assertEqual(len(mix_nodes), 1)
            rtree = ET.parse(xml)
            rb_names = [node.get("Name") for node in rtree.getroot().iter("NODE")]
            self.assertIn("STEMIT", rb_names)
            self.assertIn("Mixes", rb_names)
            self.assertEqual(rtree.find("COLLECTION").get("Entries"), "2")

    def test_prunes_empty_stemit_shells(self) -> None:
        from ix_crate.stems_playlists import rebuild_stemit_nml

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            album = root / "Moby" / "Play"
            album.mkdir(parents=True)
            (album / "Honey.m4a").write_bytes(b"mix")
            nml = Path(tmp) / "collection.nml"
            nml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<NML VERSION=\"20\">"
                '<COLLECTION ENTRIES="0"/>'
                "<PLAYLISTS><NODE TYPE=\"FOLDER\" NAME=\"$ROOT\">"
                "<SUBNODES COUNT=\"1\">"
                '<NODE TYPE="FOLDER" NAME="STEMIT"><SUBNODES COUNT="4">'
                '<NODE TYPE="PLAYLIST" NAME="Acapellas"/>'
                '<NODE TYPE="PLAYLIST" NAME="Instrumentals"/>'
                '<NODE TYPE="PLAYLIST" NAME="Mixes"/>'
                '<NODE TYPE="PLAYLIST" NAME="Stems"/>'
                "</SUBNODES></NODE></SUBNODES></NODE></PLAYLISTS></NML>",
                encoding="utf-8",
            )
            rebuild_stemit_nml(nml, stems_root=root)
            tree = ET.parse(nml)
            stemit = [
                node
                for node in tree.getroot().iter("NODE")
                if node.get("TYPE") == "FOLDER" and node.get("NAME") == "STEMIT"
            ][0]
            kids = list(stemit.find("SUBNODES").findall("NODE"))
            names = [n.get("NAME") for n in kids]
            self.assertEqual(names.count("Mixes"), 1)
            mixes = next(n for n in kids if n.get("NAME") == "Mixes")
            playlist = mixes.find("PLAYLIST")
            self.assertEqual(playlist.get("TYPE"), "LIST")
            self.assertEqual(playlist.get("ENTRIES"), "1")


if __name__ == "__main__":
    unittest.main()
