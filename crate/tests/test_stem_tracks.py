import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.families import family_key, strip_role_markup
from ix_crate.stems_playlists import (
    TRACK_ROLES,
    all_sync_files,
    track_component_role,
)


class StemTrackComponentTests(unittest.TestCase):
    def test_dot_role_detection(self) -> None:
        p = Path("/x/What's up with That.drums.m4a")
        self.assertEqual(track_component_role(p), "drums")
        self.assertEqual(track_component_role(Path("/x/mix.m4a")), "")
        self.assertEqual(track_component_role(Path("/x/What's up with That.stem.m4a")), "")

    def test_family_key_strips_dot_roles(self) -> None:
        key = family_key(Path("/x/What's up with That.vocals.m4a"))
        self.assertEqual(strip_role_markup("What's up with That.vocals"), "What's up with That")
        self.assertEqual(key, "What's up with That")

    def test_walk_includes_components(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            album = root / "ZZ Top" / "Goin' 50"
            album.mkdir(parents=True)
            (album / "What's up with That.stem.m4a").write_bytes(b"x")
            (album / "What's up with That.drums.m4a").write_bytes(b"x")
            (album / "What's up with That.m4a").write_bytes(b"x")
            files = all_sync_files(root)
            roles = {f.track_role for f in files if f.track_role}
            crates = {f.crate for f in files if f.crate}
        self.assertIn("drums", roles)
        self.assertEqual(roles.issubset(set(TRACK_ROLES)), True)
        self.assertIn("Stems", crates)
        self.assertIn("Mixes", crates)


if __name__ == "__main__":
    unittest.main()