from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.families import family_key, is_role_file, strip_role_markup
from ix_crate.role_titles import (
    apply_nml_store_titles,
    identity_for_role,
    patch_nml_titles,
    plan_nml_store_titles,
    plan_role_titles,
)
from ix_crate.stems_playlists import _traktor_dir_file, classify, filing_from_path, is_cloud_path, walk_stems


class StripRoleMarkupTests(unittest.TestCase):
    def test_bare_vocals_is_empty(self) -> None:
        self.assertEqual(strip_role_markup("vocals"), "")
        self.assertEqual(strip_role_markup("vocals (2)"), "")
        self.assertEqual(strip_role_markup("drums"), "")

    def test_space_vocals(self) -> None:
        self.assertEqual(strip_role_markup("Everyday vocals"), "Everyday")
        self.assertEqual(
            strip_role_markup("Buddy Holly - Everyday vocals"),
            "Buddy Holly - Everyday",
        )

    def test_vocal_club_mix_stays(self) -> None:
        self.assertEqual(
            strip_role_markup("What Planet You On (Bodyrox Vocal Club Mix)"),
            "What Planet You On (Bodyrox Vocal Club Mix)",
        )
        self.assertFalse(is_role_file(Path("What Planet You On (Bodyrox Vocal Club Mix).mp3")))

    def test_war_drums_is_not_a_role(self) -> None:
        self.assertEqual(strip_role_markup("War drums"), "War drums")
        self.assertFalse(is_role_file(Path("War drums.mp3")))
        self.assertEqual(classify(Path("War drums.mp3")), "Mixes")

    def test_family_key_space_vocals(self) -> None:
        self.assertEqual(family_key(Path("Everyday vocals.m4a")), "Everyday")


class IdentityForRoleTests(unittest.TestCase):
    def test_filename_artist_title(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Buku" / "Singles"
            dest.mkdir(parents=True)
            path = dest / "Buku - What You See - vocals.m4a"
            path.write_bytes(b"vox")
            item = identity_for_role(path, root=root)
            self.assertEqual(item.artist, "Buku")
            self.assertEqual(item.title, "What You See")
            self.assertTrue(item.write_tags)

    def test_rewrites_role_markup_in_existing_tags(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Buddy Holly" / "Singles"
            dest.mkdir(parents=True)
            path = dest / "Buddy Holly - Everyday_vocals.m4a"
            path.write_bytes(b"vox")
            from unittest.mock import patch

            with patch(
                "ix_crate.role_titles._tag_fields",
                return_value=("Unknown Artist", "Buddy Holly - Everyday vocals"),
            ):
                item = identity_for_role(path, root=root)
            self.assertEqual(item.title, "Everyday")
            self.assertEqual(item.artist, "Buddy Holly")
            self.assertTrue(item.write_tags)
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Buddy Holly" / "Singles"
            dest.mkdir(parents=True)
            path = dest / "Buddy Holly - Everyday_vocals.m4a"
            path.write_bytes(b"vox")
            item = identity_for_role(path, root=root)
            self.assertEqual(item.artist, "Buddy Holly")
            self.assertEqual(item.title, "Everyday")

    def test_industry_stems_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "IndustryStems" / "03_God_is_God"
            dest.mkdir(parents=True)
            path = dest / "vocals.wav"
            path.write_bytes(b"RIFF")
            item = identity_for_role(path, root=root)
            self.assertEqual(item.title, "God is God")
            self.assertEqual(item.source, "album-folder")
            self.assertFalse(item.write_tags)

    def test_mix_sibling_when_bare_vocals(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Moby" / "Play"
            dest.mkdir(parents=True)
            (dest / "Honey.m4a").write_bytes(b"mix")
            path = dest / "vocals.m4a"
            path.write_bytes(b"vox")
            item = identity_for_role(path, root=root)
            self.assertEqual(item.title, "Honey")
            self.assertEqual(item.source, "mix-sibling")

    def test_filing_from_path_does_not_keep_vocals(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "IndustryStems" / "03_God_is_God"
            dest.mkdir(parents=True)
            path = dest / "vocals.wav"
            path.write_bytes(b"RIFF")
            artist, album, title = filing_from_path(path, root)
            self.assertEqual(title, "God is God")
            self.assertNotEqual(title, "vocals")
            self.assertEqual(artist, "")

    def test_plan_includes_wav_and_taggable(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            album = root / "Buku" / "Singles"
            album.mkdir(parents=True)
            (album / "Buku - What You See - vocals.m4a").write_bytes(b"vox")
            ind = root / "IndustryStems" / "03_God_is_God"
            ind.mkdir(parents=True)
            (ind / "vocals.wav").write_bytes(b"RIFF")
            (ind / "vocals (2).wav").write_bytes(b"RIFF")
            fixes = plan_role_titles(stems_root=root)
            titles = {Path(item.path).name: item.title for item in fixes}
            self.assertEqual(titles["Buku - What You See - vocals.m4a"], "What You See")
            self.assertEqual(titles["vocals.wav"], "God is God")
            self.assertEqual(titles["vocals (2).wav"], "God is God")

    def test_nml_patch_sets_title(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Buku" / "Singles"
            dest.mkdir(parents=True)
            path = dest / "Buku - What You See - vocals.m4a"
            path.write_bytes(b"vox")
            directory, file_attr = _traktor_dir_file(path.resolve())
            nml = Path(tmp) / "collection.nml"
            nml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<NML VERSION=\"20\">"
                "<COLLECTION ENTRIES=\"1\">"
                f'<ENTRY TITLE="vocals" ARTIST="Unknown Artist">'
                f'<LOCATION DIR="{directory}" FILE="{file_attr}" VOLUME="Macintosh HD"/>'
                '<ALBUM TITLE="Singles"/>'
                "</ENTRY></COLLECTION></NML>",
                encoding="utf-8",
            )
            fixes = plan_role_titles(stems_root=root)
            patched = patch_nml_titles(fixes, nml=nml, execute=True)
            self.assertEqual(patched, 1)
            entry = ET.parse(nml).find("COLLECTION/ENTRY")
            self.assertEqual(entry.get("TITLE"), "What You See")
            self.assertEqual(entry.get("ARTIST"), "Buku")

    def test_classify_bare_vocals(self) -> None:
        self.assertEqual(classify(Path("vocals.wav")), "Acapellas")
        self.assertEqual(classify(Path("vocals (2).wav")), "Acapellas")

    def test_beatport_role_title_is_pretty(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "Venture" / "Lost & Found"
            dest.mkdir(parents=True)
            path = dest / "12432715_Together_We_Fall_(Alexvnder_Remix)_vocals.mp3"
            path.write_bytes(b"vox")
            item = identity_for_role(path, root=root)
            self.assertEqual(item.title, "Together We Fall (Alexvnder Remix)")

    def test_nml_store_titles_and_cloud_drop(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "stems_audio" / "Venture" / "Lost and Found"
            dest.mkdir(parents=True)
            local = dest / "12432715_Together_We_Fall_(Alexvnder_Remix)_vocals.mp3"
            local.write_bytes(b"vox")
            cloud = (
                root
                / "Library"
                / "CloudStorage"
                / "GoogleDrive-x"
                / ".shortcut-targets-by-id"
                / "abc"
                / "Trotter Dubplate Mix.m4a"
            )
            cloud.parent.mkdir(parents=True)
            cloud.write_bytes(b"cloud")
            nml = Path(tmp) / "collection.nml"
            loc_a, file_a = _traktor_dir_file(local.resolve())
            loc_b, file_b = _traktor_dir_file(cloud.resolve())
            nml.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<NML VERSION=\"20\">"
                "<COLLECTION ENTRIES=\"2\">"
                f'<ENTRY TITLE="12432715_Together_We_Fall_(Alexvnder_Remix)" ARTIST="Venture">'
                f'<LOCATION DIR="{loc_a}" FILE="{file_a}" VOLUME="Macintosh HD"/>'
                "</ENTRY>"
                f'<ENTRY TITLE="Dubplate Mix" ARTIST="Trotter">'
                f'<LOCATION DIR="{loc_b}" FILE="{file_b}" VOLUME="Macintosh HD"/>'
                "</ENTRY></COLLECTION>"
                "<PLAYLISTS><NODE TYPE=\"FOLDER\" NAME=\"$ROOT\"><SUBNODES COUNT=\"1\">"
                '<NODE TYPE="PLAYLIST" NAME="STEMIT">'
                '<PLAYLIST ENTRIES="1" TYPE="LIST" UUID="x">'
                f'<ENTRY><PRIMARYKEY TYPE="TRACK" KEY="Macintosh HD{loc_b}{file_b}"/></ENTRY>'
                "</PLAYLIST></NODE></SUBNODES></NODE></PLAYLISTS>"
                "</NML>",
                encoding="utf-8",
            )
            self.assertTrue(is_cloud_path(cloud, root))
            self.assertEqual(len(walk_stems(root)), 1)
            fixes = plan_nml_store_titles(nml)
            titled, dropped = apply_nml_store_titles(fixes, nml=nml, execute=True)
            self.assertEqual(titled, 1)
            self.assertEqual(dropped, 1)
            tree = ET.parse(nml)
            entries = tree.findall("COLLECTION/ENTRY")
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].get("TITLE"), "Together We Fall (Alexvnder Remix)")
            playlist = tree.find(".//PLAYLIST")
            self.assertEqual(playlist.get("ENTRIES"), "0")

    def test_walk_skips_library_cloud(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / "Trotter" / "Burning Man 2014 Mix"
            keep.mkdir(parents=True)
            (keep / "Trotter Dubplate Mix.m4a").write_bytes(b"local")
            cloud = root / "Library" / "CloudStorage" / "GoogleDrive-x" / "mix.m4a"
            cloud.parent.mkdir(parents=True)
            cloud.write_bytes(b"cloud")
            files = walk_stems(root)
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].path.name, "Trotter Dubplate Mix.m4a")


if __name__ == "__main__":
    unittest.main()
