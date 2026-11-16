import unittest

from ix_crate.batch_progress import build_crater_phases


class CraterPhaseTests(unittest.TestCase):
    def test_default_steps(self) -> None:
        phases = build_crater_phases(
            skip_follow=True,
            skip_stemit=False,
            skip_music=False,
            plain=False,
        )
        names = [p.name for p in phases]
        self.assertEqual(
            names,
            [
                "favorites",
                "stemit-sync",
                "stemit-genres",
                "music-crates",
                "xml-prune",
                "rekordbox-samplers",
                "traktor-remix",
                "mixed-in",
            ],
        )
        self.assertIn("--step", phases[0].argv)
        self.assertIn("stemit-sync", phases[1].argv)

    def test_skip_stemit(self) -> None:
        phases = build_crater_phases(
            skip_follow=True,
            skip_stemit=True,
            skip_music=True,
            plain=True,
        )
        names = [p.name for p in phases]
        self.assertNotIn("stemit-sync", names)
        self.assertIn("--plain", phases[0].argv)