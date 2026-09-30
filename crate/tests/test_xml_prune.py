from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.stems_playlists import _rb_location
from ix_crate.xml_prune import prune_xml


class XmlPruneTest(unittest.TestCase):
    def test_drops_missing_and_m4p_keeps_live_and_volumes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            live = root / "Live.m4a"
            live.write_bytes(b"x")
            drm = root / "Drm.m4p"
            drm.write_bytes(b"x")
            gone = root / "Gone.stem.m4a"
            xml = root / "rekordbox.xml"
            xml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n<DJ_PLAYLISTS Version="1.0.0">'
                '<COLLECTION Entries="4">'
                f'<TRACK TrackID="1" Location="{_rb_location(live)}"/>'
                f'<TRACK TrackID="2" Location="{_rb_location(drm)}"/>'
                f'<TRACK TrackID="3" Location="{_rb_location(gone)}"/>'
                '<TRACK TrackID="4" Location="file://localhost/Volumes/USB/Off.mp3"/>'
                "</COLLECTION><PLAYLISTS>"
                '<NODE Type="0" Name="ROOT" Count="1">'
                '<NODE Name="P" Type="1" KeyType="0" Entries="4">'
                '<TRACK Key="1"/><TRACK Key="2"/><TRACK Key="3"/><TRACK Key="4"/>'
                "</NODE></NODE></PLAYLISTS></DJ_PLAYLISTS>",
                encoding="utf-8",
            )

            dry = prune_xml(xml)
            self.assertEqual(dry.reasons(), {"m4p": 1, "missing": 1})
            self.assertIn('TrackID="3"', xml.read_text(encoding="utf-8"))

            prune_xml(xml, execute=True)
            tree = ET.parse(xml).getroot()
            ids = [t.get("TrackID") for t in tree.find("COLLECTION").findall("TRACK")]
            self.assertEqual(ids, ["1", "4"])
            self.assertEqual(tree.find("COLLECTION").get("Entries"), "2")
            node = next(n for n in tree.iter("NODE") if n.get("Name") == "P")
            self.assertEqual([t.get("Key") for t in node.findall("TRACK")], ["1", "4"])
            self.assertEqual(node.get("Entries"), "2")
            self.assertTrue(xml.with_suffix(".xml.prune.bak").exists())


if __name__ == "__main__":
    unittest.main()
