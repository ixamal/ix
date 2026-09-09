from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.stemit_dupes import apply_disk_dupes, plan_disk_dupes, plan_finder_copies, prune_empty_dirs


class PlanDiskDupesTests(unittest.TestCase):
    def test_drops_mashups_copy_of_same_name(self) -> None:
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
            keep.write_bytes(b"stem-bytes")
            dump.write_bytes(b"stem-bytes")
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 1)
            self.assertEqual(Path(plan.twins[0].keep), keep.resolve())
            self.assertEqual(Path(plan.twins[0].drop), dump.resolve())

    def test_keeps_unique_mashup(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            mash = (
                root
                / "Compilations"
                / "Mashups"
                / "PSY vs Ghostbusters"
                / "Ghostbusters Gangnam Style.stem.m4a"
            )
            mash.parent.mkdir(parents=True)
            mash.write_bytes(b"unique")
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 0)

    def test_does_not_collapse_industry_stem_parts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = root / "IndustryStems" / "03_God_is_God"
            pack.mkdir(parents=True)
            for name in ("drums.wav", "bass.wav", "other.wav", "vocals.wav"):
                (pack / name).write_bytes(name.encode())
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 0)

    def test_does_not_drop_industry_pack(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            factory = root / "Juno Reactor" / "Singles" / "God is God - vocals.m4a"
            pack = root / "IndustryStems" / "03_God_is_God" / "vocals.wav"
            factory.parent.mkdir(parents=True)
            pack.parent.mkdir(parents=True)
            factory.write_bytes(b"mel")
            pack.write_bytes(b"official")
            plan = plan_disk_dupes(stems_root=root)
            dropped = [item.drop for item in plan.twins]
            self.assertNotIn(str(pack.resolve()), dropped)

    def test_drops_unknown_album_copy(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / "Queen" / "Flash Gordon" / "Flash.stem.m4a"
            dump = root / "Queen" / "Unknown Album" / "Flash.stem.m4a"
            keep.parent.mkdir(parents=True)
            dump.parent.mkdir(parents=True)
            keep.write_bytes(b"xxxx")
            dump.write_bytes(b"xxxx")
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 1)
            self.assertEqual(Path(plan.twins[0].drop), dump.resolve())

    def test_prefers_artist_stems_over_mashups(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / "Blaze" / "Stems" / "Lovelee Dae.stem.m4a"
            dump = (
                root
                / "Compilations"
                / "Mashups"
                / "Blaze"
                / "Lovelee Dae.stem.m4a"
            )
            keep.parent.mkdir(parents=True)
            dump.parent.mkdir(parents=True)
            keep.write_bytes(b"artist")
            dump.write_bytes(b"mash")
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 1)
            self.assertEqual(Path(plan.twins[0].keep), keep.resolve())
            self.assertEqual(Path(plan.twins[0].drop), dump.resolve())

    def test_drops_dump_vs_dump_same_name(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = (
                root
                / "Planet Funk"
                / "Stems Spring Blossoms"
                / "PlanetFunk_Static.stem.m4a"
            )
            dump = (
                root
                / "Compilations"
                / "Mashups"
                / "Planet Funk"
                / "PlanetFunk_Static.stem.m4a"
            )
            keep.parent.mkdir(parents=True)
            dump.parent.mkdir(parents=True)
            keep.write_bytes(b"stem-a")
            dump.write_bytes(b"stem-b")
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 1)
            self.assertEqual(Path(plan.twins[0].drop), dump.resolve())

    def test_keeps_mashup_stem_parts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Compilations" / "Mashups" / "Miscellaneous"
            folder.mkdir(parents=True)
            for name in (
                "kpop-piano-music_drums.wav",
                "kpop-piano-music_bass.wav",
                "kpop-piano-music_other.wav",
            ):
                (folder / name).write_bytes(name.encode())
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 0)

    def test_drops_stem_remux_in_second_album(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / "Queen" / "Flash Gordon" / "Queen - The Ring.stem.m4a"
            extra = root / "Queen" / "Stems Flash Gordon" / "Queen - The Ring.stem.mp3"
            keep.parent.mkdir(parents=True)
            extra.parent.mkdir(parents=True)
            keep.write_bytes(b"m4a-bytes")
            extra.write_bytes(b"mp3-bytes")
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 1)
            self.assertIn(plan.twins[0].reason, {"stem-family-remux", "dump-same-stem-family"})
            self.assertEqual(Path(plan.twins[0].drop), extra.resolve())

    def test_keeps_live_vs_studio(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            studio = root / "Front Line Assembly" / "Tactical Neural Implant" / "07 Gun.stem.m4a"
            live = root / "Front Line Assembly" / "Live Wired Disc 2" / "2-01 Gun.stem.m4a"
            studio.parent.mkdir(parents=True)
            live.parent.mkdir(parents=True)
            studio.write_bytes(b"studio-stem")
            live.write_bytes(b"live-stem")
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 0)

    def test_drops_same_folder_stem_mp4(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / "Andy Caldwell" / "Genesis" / "Scream.stem.m4a"
            extra = root / "Andy Caldwell" / "Genesis" / "Scream.stem.mp4"
            keep.parent.mkdir(parents=True)
            keep.write_bytes(b"m4a")
            extra.write_bytes(b"mp4")
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 1)
            self.assertEqual(plan.twins[0].reason, "stem-family-remux")
            self.assertEqual(Path(plan.twins[0].drop), extra.resolve())

    def test_drops_album_title_variant(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = (
                root
                / "Nine Inch Nails"
                / "TRON_ Ares - Original Motion Picture Soundtrack"
                / "01 Init.stem.m4a"
            )
            extra = (
                root
                / "Nine Inch Nails"
                / "TRON Ares (Original Motion Picture Soundtrack)"
                / "01 Init.stem.m4a"
            )
            keep.parent.mkdir(parents=True)
            extra.parent.mkdir(parents=True)
            keep.write_bytes(b"a")
            extra.write_bytes(b"b")
            plan = plan_disk_dupes(stems_root=root)
            self.assertEqual(plan.extras, 1)
            self.assertEqual(plan.twins[0].reason, "album-variant")

    def test_execute_unlinks_and_prunes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / "Kettama" / "Singles" / "Fly Away.stem.m4a"
            dump = root / "Compilations" / "Mashups" / "Kettama" / "Fly Away.stem.m4a"
            keep.parent.mkdir(parents=True)
            dump.parent.mkdir(parents=True)
            keep.write_bytes(b"stem")
            dump.write_bytes(b"stem")
            plan = plan_disk_dupes(stems_root=root)
            apply_disk_dupes(plan, stems_root=root)
            self.assertTrue(keep.is_file())
            self.assertFalse(dump.is_file())
            self.assertFalse(dump.parent.is_dir())


class FinderCopyTests(unittest.TestCase):
    def test_drops_stem_paren_copy(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            album = root / "Lords of Acid" / "Lust"
            album.mkdir(parents=True)
            keep = album / "03 Lets Get High.stem.m4a"
            extra = album / "03 Lets Get High.stem (2).m4a"
            keep.write_bytes(b"keep")
            extra.write_bytes(b"copy")
            plan = plan_finder_copies(stems_root=root)
            self.assertEqual(plan.extras, 1)
            self.assertEqual(Path(plan.twins[0].drop), extra.resolve())
            apply_disk_dupes(plan, stems_root=root)
            self.assertTrue(keep.is_file())
            self.assertFalse(extra.is_file())

    def test_keeps_live_and_studio(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            studio = root / "Front Line Assembly" / "Tactical Neural Implant" / "07 Gun.stem.m4a"
            live = root / "Front Line Assembly" / "Live Wired Disc 2" / "2-01 Gun.stem.m4a"
            studio.parent.mkdir(parents=True)
            live.parent.mkdir(parents=True)
            studio.write_bytes(b"studio")
            live.write_bytes(b"live")
            plan = plan_finder_copies(stems_root=root)
            self.assertEqual(plan.extras, 0)


class PruneTests(unittest.TestCase):
    def test_leaves_root(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "stems_audio"
            empty = root / "Gone" / "Album"
            empty.mkdir(parents=True)
            self.assertEqual(prune_empty_dirs(root), 2)
            self.assertTrue(root.is_dir())


if __name__ == "__main__":
    unittest.main()
