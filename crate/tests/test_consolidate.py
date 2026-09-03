from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.consolidate import (
    ConsolidateError,
    assert_under_music,
    assert_within,
    build_plan,
    execute,
    index_local,
    is_stem,
    unique_dest,
    walk_audio,
)


def _mp3(path: Path, payload: bytes = b"audio-payload") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


class WalkTest(unittest.TestCase):
    def test_skips_app_state_and_appledouble(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = _mp3(root / "Moby" / "Play" / "01 Honey.mp3")
            _mp3(root / "_Serato_" / "sample.mp3")
            _mp3(root / "Ableton" / "loop.mp3")
            _mp3(root / "Moby" / "Play" / "._01 Honey.mp3")
            got = sorted(walk_audio(root))
            self.assertEqual(got, [keep])

    def test_ignores_non_audio(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = _mp3(root / "a.mp3")
            (root / "notes.txt").write_text("x")
            self.assertEqual(sorted(walk_audio(root)), [keep])


class IsStemTest(unittest.TestCase):
    def test_role_suffix_is_a_stem(self) -> None:
        self.assertTrue(is_stem(Path("/x/Track (vocals).mp3".replace(" (", "_").replace(")", ""))))
        self.assertTrue(is_stem(Path("/x/Track_drums.mp3")))

    def test_plain_mix_is_not_a_stem(self) -> None:
        self.assertFalse(is_stem(Path("/x/01 Honey.mp3")))


class SafetyTest(unittest.TestCase):
    def test_refuses_root_outside_music(self) -> None:
        with self.assertRaises(ConsolidateError):
            assert_under_music(Path("/tmp/elsewhere"))

    def test_allows_root_under_music(self) -> None:
        target = Path.home() / "Music" / "Music" / "Media.localized"
        self.assertEqual(assert_under_music(target).name, "Media.localized")

    def test_refuses_escape_from_planned_root(self) -> None:
        with self.assertRaises(ConsolidateError):
            assert_within(Path("/a/b/../../etc/passwd"), Path("/a/b"))

    def test_traversal_in_a_tag_cannot_escape(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dest, stems = root / "src", root / "dest", root / "stems"
            _mp3(src / "x.mp3")
            plan = build_plan([src], {}, dest_root=dest, stems_root=stems)
            self.assertTrue(str(plan.copy[0].dest).startswith(str(dest)))


class UniqueDestTest(unittest.TestCase):
    def test_suffixes_when_name_is_taken_on_disk(self) -> None:
        with TemporaryDirectory() as tmp:
            dest = _mp3(Path(tmp) / "a.mp3")
            self.assertEqual(unique_dest(dest, set()).name, "a (2).mp3")

    def test_suffixes_when_name_is_claimed_in_this_run(self) -> None:
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "a.mp3"
            self.assertEqual(unique_dest(dest, {dest}).name, "a (2).mp3")


class BuildPlanTest(unittest.TestCase):
    def _dirs(self, tmp: str) -> tuple[Path, Path, Path]:
        root = Path(tmp)
        return root / "src", root / "dest", root / "stems"

    def test_copies_unseen_audio_named_by_folder_fallback(self) -> None:
        with TemporaryDirectory() as tmp:
            src, dest, stems = self._dirs(tmp)
            _mp3(src / "Moby" / "Play" / "01 Honey.mp3")
            plan = build_plan([src], {}, dest_root=dest, stems_root=stems)
            self.assertEqual(len(plan.copy), 1)
            self.assertEqual(plan.duplicate, 0)
            # no tags in a stub file, so it lands in the unknown bucket
            self.assertEqual(plan.copy[0].dest.name, "01 Honey.mp3")

    def test_drops_audio_already_held_locally(self) -> None:
        with TemporaryDirectory() as tmp:
            src, dest, stems = self._dirs(tmp)
            payload = b"the-same-bytes"
            source = _mp3(src / "Moby" / "Play" / "01 Honey.mp3", payload)
            local = _mp3(dest / "Moby" / "Play" / "01 Honey.mp3", payload)
            index = index_local([dest])
            plan = build_plan([src], index, dest_root=dest, stems_root=stems)
            self.assertEqual(plan.copy, [])
            self.assertEqual(plan.duplicate, 1)
            self.assertTrue(local.exists() and source.exists())

    def test_same_size_different_audio_is_not_a_duplicate(self) -> None:
        with TemporaryDirectory() as tmp:
            src, dest, stems = self._dirs(tmp)
            _mp3(src / "Moby" / "Play" / "01 Honey.mp3", b"aaaaaaaaaaaa")
            _mp3(dest / "Moby" / "Play" / "01 Honey.mp3", b"bbbbbbbbbbbb")
            index = index_local([dest])
            plan = build_plan([src], index, dest_root=dest, stems_root=stems)
            self.assertEqual(len(plan.copy), 1)
            self.assertEqual(plan.duplicate, 0)

    def test_stems_are_routed_to_the_stems_root(self) -> None:
        with TemporaryDirectory() as tmp:
            src, dest, stems = self._dirs(tmp)
            _mp3(src / "Stems" / "Track_vocals.mp3")
            plan = build_plan([src], {}, dest_root=dest, stems_root=stems)
            self.assertEqual(len(plan.copy), 1)
            self.assertTrue(str(plan.copy[0].dest).startswith(str(stems)))

    def test_missing_source_is_an_error(self) -> None:
        with TemporaryDirectory() as tmp:
            _, dest, stems = self._dirs(tmp)
            with self.assertRaises(ConsolidateError):
                build_plan([Path(tmp) / "nope"], {}, dest_root=dest, stems_root=stems)


class ExecuteTest(unittest.TestCase):
    def test_copy_preserves_bytes_and_leaves_source(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dest = root / "src", root / "dest"
            payload = b"copy-me-please"
            source = _mp3(src / "Moby" / "Play" / "01 Honey.mp3", payload)
            plan = build_plan([src], {}, dest_root=dest, stems_root=root / "stems")
            target = plan.copy[0].dest

            copied, failed, moved = execute(plan)

            self.assertEqual((copied, failed), (1, 0))
            self.assertEqual(moved, len(payload))
            self.assertEqual(target.read_bytes(), payload)
            self.assertTrue(source.exists(), "source must never be moved")
            self.assertFalse(target.with_name(target.name + ".partial").exists())

    def test_second_run_copies_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dest, stems = root / "src", root / "dest", root / "stems"
            _mp3(src / "Moby" / "Play" / "01 Honey.mp3", b"copy-me-please")
            execute(build_plan([src], {}, dest_root=dest, stems_root=stems))
            again = build_plan(
                [src], index_local([dest]), dest_root=dest, stems_root=stems
            )
            self.assertEqual(again.copy, [])
            self.assertEqual(again.duplicate, 1)


if __name__ == "__main__":
    unittest.main()


class TitleKeyTest(unittest.TestCase):
    def test_truncated_filename_still_matches_via_tag(self) -> None:
        from ix_crate.consolidate import title_keys

        keys = title_keys(Path("/x/08 Head Affect _ Afrochrome [Gent.mp3"), "Afrochrome")
        self.assertIn("afrochrome", keys)

    def test_untagged_file_falls_back_to_filename(self) -> None:
        from ix_crate.consolidate import title_keys

        self.assertEqual(title_keys(Path("/x/01 Honey.mp3"), ""), {"honey"})


class DestinationTest(unittest.TestCase):
    def test_bare_role_filename_is_a_stem(self) -> None:
        self.assertTrue(is_stem(Path("/x/vocals.wav")))
        self.assertTrue(is_stem(Path("/x/drums.wav")))

    def test_untagged_stem_is_grouped_by_its_project_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dest, stems = root / "src", root / "dest", root / "stems"
            _mp3(src / "Documents" / "Stems Flash Gordon" / "vocals.wav")
            _mp3(src / "Documents" / "Stems April Fools" / "vocals.wav")
            plan = build_plan([src], {}, dest_root=dest, stems_root=stems)
            albums = sorted(item.dest.parent.name for item in plan.copy)
            self.assertEqual(albums, ["Stems April Fools", "Stems Flash Gordon"])
            # generic container must not become the artist
            self.assertNotIn("Documents", {i.dest.parent.parent.name for i in plan.copy})

    def test_untagged_track_uses_artist_and_album_folders(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dest, stems = root / "src", root / "dest", root / "stems"
            _mp3(src / "Moby" / "Play" / "01 Honey.mp3")
            plan = build_plan([src], {}, dest_root=dest, stems_root=stems)
            got = plan.copy[0].dest
            self.assertEqual(got.parent.name, "Play")
            self.assertEqual(got.parent.parent.name, "Moby")


class IndexCacheTest(unittest.TestCase):
    def test_round_trips(self) -> None:
        from ix_crate.consolidate import load_index, save_index

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mp3(root / "dest" / "Moby" / "Play" / "01 Honey.mp3", b"abc")
            index = index_local([root / "dest"])
            cache = save_index(index, root / "cache.json")
            self.assertEqual(load_index(cache), index)
