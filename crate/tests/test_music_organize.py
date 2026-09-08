from __future__ import annotations

import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ix_crate.music_organize import (
    OrganizeRow,
    apply_move,
    build_parser,
    filename_is_junk,
    filing_album,
    filing_artist,
    organized_filename,
    plan_rows,
    run,
    tree_root,
)


def _row(
    location: str,
    *,
    pid: str = "AA11BB22",
    artist: str = "Moby",
    album_artist: str = "",
    album: str = "Play",
    name: str = "Honey",
    track_number: int = 1,
    disc_number: int = 1,
) -> OrganizeRow:
    return OrganizeRow(
        persistent_id=pid,
        artist=artist,
        album_artist=album_artist,
        album=album,
        name=name,
        track_number=track_number,
        disc_number=disc_number,
        location=location,
    )


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"audio")
    return path


class FilenameJunkTests(unittest.TestCase):
    def test_track_nn_is_junk(self) -> None:
        self.assertTrue(filename_is_junk("Track 01"))
        self.assertTrue(filename_is_junk("01 Track 01"))
        self.assertTrue(filename_is_junk("Track 1"))
        self.assertTrue(filename_is_junk("Track 1 (2)"))
        self.assertTrue(filename_is_junk("05-Track-05"))

    def test_real_titles_are_kept(self) -> None:
        self.assertFalse(filename_is_junk("01 Honey"))
        self.assertFalse(filename_is_junk("Moby - Honey"))
        self.assertFalse(filename_is_junk("Honey (Original Mix)"))
        self.assertFalse(filename_is_junk("Soundtrack"))


class NamingTests(unittest.TestCase):
    def test_track_number_prefixes_title(self) -> None:
        self.assertEqual(organized_filename("Honey", ".m4a", track_number=1), "01 Honey.m4a")

    def test_multi_disc_uses_disc_track(self) -> None:
        self.assertEqual(
            organized_filename("Honey", ".m4a", track_number=7, disc_number=2),
            "2-07 Honey.m4a",
        )

    def test_no_track_number_is_bare_title(self) -> None:
        self.assertEqual(organized_filename("Honey", ".m4a"), "Honey.m4a")

    def test_album_artist_wins_folder(self) -> None:
        row = _row(
            "/tmp/x.m4a",
            artist="16 Bit Lolitas",
            album_artist="Danny Tenaglia",
            album="Global Underground 010 Athens",
        )
        self.assertEqual(filing_artist(row), "Danny Tenaglia")

    def test_various_artists_is_not_a_home(self) -> None:
        row = _row("/tmp/x.m4a", artist="Bonobo", album_artist="Various Artists")
        self.assertEqual(filing_artist(row), "Bonobo")

    def test_compilation_track_artist_does_not_explode_the_mix_cd(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(
                media / "Music" / "Compilations" / "Global Underground 014" / "01 Cut.m4a"
            )
            row = _row(
                str(src),
                artist="A:Xus",
                album_artist="",
                album="Global Underground 014",
                name="Cut",
            )
            self.assertEqual(
                filing_artist(row, path=src, root=media / "Music"),
                "Compilations",
            )
            plan = plan_rows([row], media_root=media)
            self.assertEqual(plan.moves, [])
            self.assertEqual(plan.skipped.get("already_organized"), 1)

    def test_various_artists_folder_does_not_explode(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Various Artists" / "Midnight Express" / "01 Cut.m4a")
            row = _row(
                str(src),
                artist="A:Xus",
                album_artist="Various Artists",
                album="Midnight Express",
                name="Cut",
            )
            plan = plan_rows([row], media_root=media)
            self.assertEqual(plan.moves, [])
            self.assertEqual(plan.skipped.get("already_organized"), 1)

    def test_unicode_folder_is_already_organized(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            nfd = "Bjo\u0308rk"
            src = _touch(media / nfd / "Homogenic" / "01 Hunter.m4a")
            row = _row(
                str(src),
                artist="Björk",
                album="Homogenic",
                name="Hunter",
            )
            plan = plan_rows([row], media_root=media)
            self.assertEqual(plan.moves, [])
            self.assertEqual(plan.skipped.get("already_organized"), 1)

    def test_split_compilation_stays_together(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            one = _touch(media / "Compilations" / "Barbie Dance" / "01 Cut.m4a")
            two = _touch(media / "Compilations" / "Barbie Dance" / "02 Other.m4a")
            plan = plan_rows(
                [
                    _row(
                        str(one),
                        pid="A",
                        artist="Le Juice",
                        album_artist="Le Juice",
                        album="Barbie Dance",
                        name="Cut",
                    ),
                    _row(
                        str(two),
                        pid="B",
                        artist="95 North",
                        album_artist="95 North",
                        album="Barbie Dance",
                        name="Other",
                    ),
                ],
                media_root=media,
            )
            self.assertEqual(plan.moves, [])
            self.assertGreaterEqual(plan.skipped.get("split_compilation", 0), 1)

    def test_compilation_with_dj_album_artist_may_leave_artist_root(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(
                media / "Compilations" / "Global Underground 010 Athens" / "01 Cut.m4a"
            )
            row = _row(
                str(src),
                artist="16 Bit Lolitas",
                album_artist="Danny Tenaglia",
                album="Global Underground 010 Athens",
                name="Cut",
            )
            plan = plan_rows([row], media_root=media)
            self.assertEqual(len(plan.moves), 1)
            self.assertEqual(
                Path(plan.moves[0].dest).parent,
                media / "Danny Tenaglia" / "Global Underground 010 Athens",
            )

    def test_music_tree_folder_move_is_locked(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(
                media / "Music" / "Compilations" / "Global Underground 010 Athens" / "01 Cut.m4a"
            )
            row = _row(
                str(src),
                artist="16 Bit Lolitas",
                album_artist="Danny Tenaglia",
                album="Global Underground 010 Athens",
                name="Cut",
            )
            plan = plan_rows([row], media_root=media)
            self.assertEqual(plan.moves, [])
            self.assertEqual(plan.skipped.get("music_tree_locked"), 1)

    def test_empty_album_becomes_singles(self) -> None:
        self.assertEqual(filing_album(_row("/tmp/x.m4a", album="")), "Singles")
        self.assertEqual(filing_album(_row("/tmp/x.m4a", album="Unknown Album")), "Singles")

    def test_cream_live_stays(self) -> None:
        self.assertEqual(
            filing_album(_row("/tmp/x.m4a", album="Cream Live [Disc 1]")),
            "Cream Live [Disc 1]",
        )


class PlanTests(unittest.TestCase):
    def test_track_01_renames_from_library_title(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Unknown Album" / "Track 01.m4a")
            plan = plan_rows([_row(str(src))], media_root=media)
            self.assertEqual(len(plan.moves), 1)
            move = plan.moves[0]
            self.assertEqual(Path(move.dest), media / "Moby" / "Play" / "01 Honey.m4a")
            self.assertEqual(move.reason, "placeholder_and_folder")

    def test_already_named_in_place_is_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Moby" / "Play" / "01 Honey.m4a")
            plan = plan_rows([_row(str(src))], media_root=media)
            self.assertEqual(plan.moves, [])
            self.assertEqual(plan.skipped.get("already_organized"), 1)

    def test_beatport_name_is_kept_when_refiling(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Downloads" / "Moby - Honey (Original Mix).mp3")
            plan = plan_rows(
                [_row(str(src), name="Honey (Original Mix)", track_number=0)],
                media_root=media,
            )
            self.assertEqual(len(plan.moves), 1)
            self.assertEqual(
                Path(plan.moves[0].dest).name, "Moby - Honey (Original Mix).mp3"
            )
            self.assertEqual(plan.moves[0].reason, "wrong_folder")

    def test_stays_in_music_copy_on_add_tree(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Music" / "Moby" / "Play" / "01 Honey.m4a")
            plan = plan_rows([_row(str(src))], media_root=media)
            self.assertEqual(plan.moves, [])
            self.assertEqual(plan.skipped.get("already_organized"), 1)
            self.assertEqual(tree_root(src, media), media / "Music")

    def test_music_tree_unknown_album_is_locked(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Music" / "Unknown Album" / "Track 01.m4a")
            plan = plan_rows([_row(str(src))], media_root=media)
            self.assertEqual(plan.moves, [])
            self.assertEqual(plan.skipped.get("music_tree_locked"), 1)

    def test_does_not_hoist_music_tree_onto_artist_root(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Music" / "Moby" / "Play" / "Track 01.m4a")
            plan = plan_rows([_row(str(src))], media_root=media)
            dest = Path(plan.moves[0].dest)
            self.assertTrue(str(dest).startswith(str(media / "Music")))
            self.assertEqual(dest, media / "Music" / "Moby" / "Play" / "01 Honey.m4a")

    def test_placeholder_library_title_is_left_alone(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Cream Live [Disc 1]" / "01 Track 01.m4a")
            plan = plan_rows(
                [_row(str(src), artist="", album="Cream Live [Disc 1]", name="Track 01")],
                media_root=media,
            )
            self.assertEqual(plan.moves, [])
            self.assertEqual(plan.skipped.get("placeholder_identity"), 1)

    def test_skips_stems_and_drm(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            stem = _touch(media / "Moby" / "Play" / "Honey.stem.m4a")
            drm = _touch(media / "Moby" / "Play" / "Honey.m4p")
            plan = plan_rows(
                [_row(str(stem), pid="A"), _row(str(drm), pid="B")],
                media_root=media,
            )
            self.assertEqual(plan.skipped.get("skip_stem_or_drm"), 2)

    def test_skips_files_outside_media(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            media.mkdir()
            other = _touch(Path(tmp) / "elsewhere" / "Track 01.m4a")
            plan = plan_rows([_row(str(other))], media_root=media)
            self.assertEqual(plan.skipped.get("outside_media"), 1)

    def test_collision_gets_a_suffix(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            one = _touch(media / "Unknown Album" / "Track 01.m4a")
            two = _touch(media / "Unknown Album" / "Track 02.m4a")
            existing = _touch(media / "Moby" / "Play" / "01 Honey.m4a")
            plan = plan_rows(
                [
                    _row(str(one), pid="A", name="Honey", track_number=1),
                    _row(str(two), pid="B", name="Honey", track_number=1),
                ],
                media_root=media,
            )
            dests = {Path(item.dest).name for item in plan.moves}
            self.assertIn("01 Honey (2).m4a", dests)
            self.assertTrue(existing.is_file())

    def test_shared_file_is_planned_once(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Unknown Album" / "Track 01.m4a")
            plan = plan_rows(
                [_row(str(src), pid="A"), _row(str(src), pid="B")],
                media_root=media,
            )
            self.assertEqual(len(plan.moves), 1)
            self.assertEqual(plan.skipped.get("shared_file"), 1)


class ApplyTests(unittest.TestCase):
    def test_rename_relink_and_prune(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Unknown Album" / "Track 01.m4a")
            seen: list[tuple[str, Path]] = []
            plan = plan_rows([_row(str(src))], media_root=media)
            result = apply_move(
                plan.moves[0],
                media_root=media,
                set_location=lambda pid, path: seen.append((pid, path)),
            )
            dest = media / "Moby" / "Play" / "01 Honey.m4a"
            self.assertTrue(result["ok"])
            self.assertTrue(dest.is_file())
            self.assertFalse(src.exists())
            self.assertFalse((media / "Unknown Album").exists())
            self.assertEqual(seen, [("AA11BB22", dest)])

    def test_refuses_overwrite(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Unknown Album" / "Track 01.m4a")
            dest = _touch(media / "Moby" / "Play" / "01 Honey.m4a")
            from ix_crate.music_organize import OrganizeMove, OrganizeError

            with self.assertRaises(OrganizeError):
                apply_move(
                    OrganizeMove(
                        persistent_id="AA11BB22",
                        source=str(src),
                        dest=str(dest),
                        artist="Moby",
                        album="Play",
                        title="Honey",
                        reason="placeholder_name",
                    ),
                    media_root=media,
                    set_location=lambda pid, path: None,
                )
            self.assertTrue(src.is_file())


class RunTests(unittest.TestCase):
    def test_placeholders_only_skips_folder_moves(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            named = _touch(media / "Downloads" / "Moby - Honey (Original Mix).mp3")
            junk = _touch(media / "Unknown Album" / "Track 01.m4a")
            with TemporaryDirectory() as reports:
                with patch("ix_crate.music_organize.REPORTS", Path(reports)):
                    payload = run(
                        execute=False,
                        placeholders_only=True,
                        media_root=media,
                        rows=[
                            _row(
                                str(named),
                                name="Honey (Original Mix)",
                                track_number=0,
                            ),
                            _row(str(junk)),
                        ],
                    )
            self.assertEqual(len(payload["moves"]), 1)
            self.assertIn("placeholder", payload["moves"][0]["reason"])

    def test_dry_run_does_not_move(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Unknown Album" / "Track 01.m4a")
            with TemporaryDirectory() as reports:
                with patch("ix_crate.music_organize.REPORTS", Path(reports)):
                    payload = run(
                        execute=False,
                        media_root=media,
                        rows=[_row(str(src))],
                    )
            self.assertFalse(payload["executed"])
            self.assertEqual(payload["applied"], 0)
            self.assertTrue(src.is_file())
            self.assertEqual(len(payload["remaps"]), 1)

    def test_execute_renames(self) -> None:
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "Media.localized"
            src = _touch(media / "Unknown Album" / "Track 01.m4a")
            with TemporaryDirectory() as reports:
                with patch("ix_crate.music_organize.REPORTS", Path(reports)):
                    payload = run(
                        execute=True,
                        media_root=media,
                        rows=[_row(str(src))],
                        set_location=lambda pid, path: None,
                    )
            dest = media / "Moby" / "Play" / "01 Honey.m4a"
            self.assertTrue(payload["executed"])
            self.assertEqual(payload["applied"], 1)
            self.assertTrue(dest.is_file())
            self.assertFalse(src.exists())


class ParserTests(unittest.TestCase):
    def test_defaults_to_dry_run(self) -> None:
        args = build_parser().parse_args([])
        self.assertFalse(args.execute)
        self.assertEqual(args.playlist, "")
        self.assertEqual(args.limit, 0)


class DispatchTests(unittest.TestCase):
    def test_top_help_lists_organize(self) -> None:
        from ix_crate.__main__ import main

        buf = io.StringIO()
        with patch("sys.stdout", buf), self.assertRaises(SystemExit) as ctx:
            main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("music-organize", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
