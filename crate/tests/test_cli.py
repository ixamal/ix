from __future__ import annotations

import io
import unittest
from unittest.mock import patch


class DispatchTest(unittest.TestCase):
    def test_top_help_lists_genre_replicants_and_consolidate(self) -> None:
        from ix_crate.__main__ import main

        buf = io.StringIO()
        with patch("sys.stdout", buf), self.assertRaises(SystemExit) as ctx:
            main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        text = buf.getvalue()
        self.assertIn("music-genre", text)
        self.assertIn("music-replicants", text)
        self.assertIn("consolidate", text)
        self.assertIn("music-cull", text)
        self.assertIn("music-organize", text)

    def test_music_genre_help(self) -> None:
        from ix_crate.__main__ import main

        buf = io.StringIO()
        with patch("sys.stdout", buf), self.assertRaises(SystemExit) as ctx:
            main(["music-genre", "--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("--execute", buf.getvalue())

    def test_music_replicants_help(self) -> None:
        from ix_crate.__main__ import main

        buf = io.StringIO()
        with patch("sys.stdout", buf), self.assertRaises(SystemExit) as ctx:
            main(["music-replicants", "--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("--execute", buf.getvalue())

    def test_music_organize_help(self) -> None:
        from ix_crate.__main__ import main

        buf = io.StringIO()
        with patch("sys.stdout", buf), self.assertRaises(SystemExit) as ctx:
            main(["music-organize", "--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("--execute", buf.getvalue())

    def test_music_cull_help(self) -> None:
        from ix_crate.__main__ import main

        buf = io.StringIO()
        with patch("sys.stdout", buf), self.assertRaises(SystemExit) as ctx:
            main(["music-cull", "--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("--execute", buf.getvalue())


class ParserTest(unittest.TestCase):
    def test_genre_defaults_to_dry_run(self) -> None:
        from ix_crate.music_genre import build_parser

        args = build_parser().parse_args([])
        self.assertFalse(args.execute)
        self.assertEqual(args.passes, 3)

    def test_replicants_defaults_to_dry_run(self) -> None:
        from ix_crate.music_replicants import build_parser

        args = build_parser().parse_args([])
        self.assertFalse(args.execute)

    def test_cull_defaults_to_dry_run(self) -> None:
        from ix_crate.music_cull import build_parser

        args = build_parser().parse_args([])
        self.assertFalse(args.execute)

    def test_organize_defaults_to_dry_run(self) -> None:
        from ix_crate.music_organize import build_parser

        args = build_parser().parse_args([])
        self.assertFalse(args.execute)


if __name__ == "__main__":
    unittest.main()
