from __future__ import annotations

import plistlib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.music_reconcile import (
    DeadRow,
    ReconcileError,
    build_plan,
    hoist,
    rebase,
    xml_locations,
)
from ix_crate.music_repair import index_tree


def _row(pid: str, **kw) -> DeadRow:
    return DeadRow(index=kw.pop("index", 1), persistent_id=pid, **kw)


class HoistTest(unittest.TestCase):
    def test_drops_music_container(self) -> None:
        got = hoist("/u/Music/Music/Media.localized/Music/Moby/Play/01 Honey.m4a")
        self.assertEqual(got, "/u/Music/Music/Media.localized/Moby/Play/01 Honey.m4a")

    def test_only_first_occurrence(self) -> None:
        got = hoist("/x/Media.localized/Music/Music/Album/01 a.m4a")
        self.assertEqual(got, "/x/Media.localized/Music/Album/01 a.m4a")

    def test_none_when_not_nested(self) -> None:
        self.assertIsNone(hoist("/x/Media.localized/Moby/Play/01 Honey.m4a"))


class RebaseTest(unittest.TestCase):
    def test_maps_tail_onto_new_root(self) -> None:
        got = rebase("/u/Media.localized/Moby/Play/01 a.m4a", Path("/V/Media.localized"))
        self.assertEqual(got, ["/V/Media.localized/Moby/Play/01 a.m4a"])

    def test_offers_hoisted_variant(self) -> None:
        got = rebase(
            "/u/Media.localized/Music/Moby/Play/01 a.m4a", Path("/V/Media.localized")
        )
        self.assertEqual(
            got,
            [
                "/V/Media.localized/Music/Moby/Play/01 a.m4a",
                "/V/Media.localized/Moby/Play/01 a.m4a",
            ],
        )

    def test_empty_when_no_media_segment(self) -> None:
        self.assertEqual(rebase("/some/other/file.m4a", Path("/V")), [])


class XmlLocationsTest(unittest.TestCase):
    def test_reads_persistent_id_map(self) -> None:
        with TemporaryDirectory() as tmp:
            xml = Path(tmp) / "iTunes Music Library.xml"
            payload = {
                "Tracks": {
                    "1": {"Persistent ID": "AA11", "Location": "file:///x/a%20b.m4a"},
                    "2": {"Persistent ID": "BB22"},
                }
            }
            with xml.open("wb") as fh:
                plistlib.dump(payload, fh)
            got = xml_locations(xml)
            self.assertEqual(got, {"AA11": "/x/a b.m4a"})

    def test_missing_xml_explains_the_setting(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ReconcileError) as ctx:
                xml_locations(Path(tmp) / "nope.xml")
            self.assertIn("Share Library XML", str(ctx.exception))


class BuildPlanTest(unittest.TestCase):
    def test_relinks_recorded_path(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "Media.localized" / "Moby" / "Play" / "01 a.m4a"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            plan = build_plan([_row("AA11")], set(), {"AA11": str(target)})
            self.assertEqual(len(plan.relink), 1)
            self.assertEqual(plan.relink[0].path, target)
            self.assertEqual(plan.relink[0].reason, "xml:recorded")

    def test_hoisted_path_when_music_container_is_gone(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            target = media / "Moby" / "Play" / "01 a.m4a"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            recorded = str(media / "Music" / "Moby" / "Play" / "01 a.m4a")
            plan = build_plan([_row("AA11")], set(), {"AA11": recorded})
            self.assertEqual(len(plan.relink), 1)
            self.assertEqual(plan.relink[0].path, target)
            self.assertEqual(plan.relink[0].reason, "xml:hoisted")

    def test_claimed_file_is_a_duplicate_row_not_a_relink(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "Media.localized" / "Moby" / "Play" / "01 a.m4a"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            plan = build_plan([_row("AA11")], {str(target)}, {"AA11": str(target)})
            self.assertEqual(plan.relink, [])
            self.assertEqual(len(plan.duplicate), 1)

    def test_two_dead_rows_never_share_one_file(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "Media.localized" / "Moby" / "Play" / "01 a.m4a"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            locations = {"AA11": str(target), "BB22": str(target)}
            plan = build_plan([_row("AA11"), _row("BB22", index=2)], set(), locations)
            self.assertEqual(len(plan.relink), 1)
            self.assertEqual(len(plan.duplicate), 1)

    def test_external_rebase_when_local_file_is_gone(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            backup = root / "backup" / "Media.localized"
            target = backup / "Moby" / "Play" / "01 a.m4a"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            recorded = str(root / "live" / "Media.localized" / "Moby/Play/01 a.m4a")
            plan = build_plan(
                [_row("AA11")], set(), {"AA11": recorded}, external=backup
            )
            self.assertEqual(len(plan.relink), 1)
            self.assertEqual(plan.relink[0].path, target)
            self.assertEqual(plan.relink[0].reason, "external:rebase")

    def test_external_index_match_when_rebase_misses(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "drive"
            album = root / "Moby" / "Play"
            album.mkdir(parents=True)
            target = album / "01 Honey.mp3"
            target.write_bytes(b"x")
            plan = build_plan(
                [_row("AA11", artist="Moby", album="Play", name="Honey")],
                set(),
                {"AA11": "/gone/Media.localized/Moby/Play/01 Honey.mp3"},
                external_index=index_tree(root),
            )
            self.assertEqual(len(plan.relink), 1)
            self.assertEqual(plan.relink[0].path, target)
            self.assertTrue(plan.relink[0].reason.startswith("external:"))

    def test_unresolved_when_nothing_matches(self) -> None:
        plan = build_plan([_row("AA11")], set(), {"AA11": "/nope/gone.m4a"})
        self.assertEqual(plan.relink, [])
        self.assertEqual(len(plan.unresolved), 1)

    def test_row_absent_from_xml_is_unresolved(self) -> None:
        plan = build_plan([_row("ZZ99")], set(), {})
        self.assertEqual(len(plan.unresolved), 1)


class LocalOnlyTest(unittest.TestCase):
    def test_home_music_is_allowed(self) -> None:
        from ix_crate.music_reconcile import MUSIC_HOME, is_under_music

        self.assertTrue(is_under_music(MUSIC_HOME / "a.m4a"))

    def test_volumes_are_refused(self) -> None:
        from ix_crate.music_reconcile import is_under_music

        self.assertFalse(is_under_music(Path("/Volumes/Terrarum/a.m4a")))


if __name__ == "__main__":
    unittest.main()
