from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ix_crate.music_dupes import TrackRow
from ix_crate.music_replicants import (
    build_plan,
    choose_keeper,
    identity,
    same_audio,
)


def _row(pid: str, path: Path, *, name="Alone", artist="Abfart", album="Choice",
         plays=0, rating=0, hits=0, dbid=1) -> TrackRow:
    return TrackRow(
        persistent_id=pid,
        database_id=dbid,
        artist=artist,
        album=album,
        name=name,
        location=str(path),
        played_count=plays,
        rating=rating,
        playlist_hits=hits,
    )


def _file(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


class IdentityTest(unittest.TestCase):
    def test_copy_suffix_does_not_split_a_pair(self) -> None:
        a = _row("A", Path("/x/a.m4a"), name="Alone (2)")
        b = _row("B", Path("/x/b.m4a"), name="Alone")
        self.assertEqual(identity(a), identity(b))


class SameAudioTest(unittest.TestCase):
    def test_identical_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "a.m4a", b"same")
            b = _file(root / "b.m4a", b"same")
            self.assertTrue(same_audio([a, b]))

    def test_same_size_different_bytes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "a.m4a", b"aaaa")
            b = _file(root / "b.m4a", b"bbbb")
            self.assertFalse(same_audio([a, b]))

    def test_different_size(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "a.m4a", b"aa")
            b = _file(root / "b.m4a", b"aaaa")
            self.assertFalse(same_audio([a, b]))


class KeeperTest(unittest.TestCase):
    def test_playlist_membership_wins(self) -> None:
        a = _row("A", Path("/x/a 1.m4a"), hits=3, dbid=9)
        b = _row("B", Path("/x/a.m4a"), hits=0, dbid=1)
        self.assertEqual(choose_keeper([a, b]).persistent_id, "A")

    def test_otherwise_the_unmarked_filename_wins(self) -> None:
        a = _row("A", Path("/x/Alone 1.m4a"), dbid=1)
        b = _row("B", Path("/x/Alone.m4a"), dbid=9)
        self.assertEqual(choose_keeper([a, b]).persistent_id, "B")

    def test_plays_beat_filename(self) -> None:
        a = _row("A", Path("/x/Alone 1.m4a"), plays=5)
        b = _row("B", Path("/x/Alone.m4a"), plays=0)
        self.assertEqual(choose_keeper([a, b]).persistent_id, "A")


class BuildPlanTest(unittest.TestCase):
    def test_pairs_identical_audio_under_two_filenames(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "Alone 1.m4a", b"same-bytes")
            b = _file(root / "Alone.m4a", b"same-bytes")
            plan = build_plan([_row("A", a, dbid=1), _row("B", b, dbid=2)])
            self.assertEqual(len(plan.twins), 1)
            self.assertEqual(plan.extra_rows, 1)
            self.assertEqual(Path(plan.twins[0].keep.location).name, "Alone.m4a")

    def test_same_title_different_audio_is_left_alone(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "Alone 1.m4a", b"aaaa")
            b = _file(root / "Alone.m4a", b"bbbb")
            plan = build_plan([_row("A", a), _row("B", b)])
            self.assertEqual(plan.twins, [])
            self.assertEqual(plan.mismatched, 1)

    def test_several_rows_on_one_file_is_not_our_job(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "Alone.m4a", b"same")
            plan = build_plan([_row("A", a, dbid=1), _row("B", a, dbid=2)])
            self.assertEqual(plan.twins, [])

    def test_reclaim_counts_only_dropped_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = b"x" * 4096
            a = _file(root / "Alone 1.m4a", payload)
            b = _file(root / "Alone.m4a", payload)
            plan = build_plan([_row("A", a, dbid=1), _row("B", b, dbid=2)])
            self.assertEqual(plan.reclaim, 4096)

    def test_missing_file_is_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "Alone.m4a", b"same")
            plan = build_plan([_row("A", a), _row("B", root / "gone.m4a")])
            self.assertEqual(plan.twins, [])


if __name__ == "__main__":
    unittest.main()


class FingerprintTest(unittest.TestCase):
    def test_retagged_copies_compare_equal(self) -> None:
        """Same audio, different tag bytes, different total size."""
        from ix_crate import music_replicants as mr

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "a.m4a", b"TAGV1" + b"audio")
            b = _file(root / "b.m4a", b"TAGVERSION2" + b"audio")
            fake = {str(a): "audio:MD5=same", str(b): "audio:MD5=same"}
            self.assertTrue(mr.same_audio([a, b], dict(fake)))

    def test_different_encodes_do_not_compare_equal(self) -> None:
        from ix_crate import music_replicants as mr

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "a.m4a", b"x")
            b = _file(root / "b.m4a", b"y")
            cache = {str(a): "audio:MD5=one", str(b): "audio:MD5=two"}
            self.assertFalse(mr.same_audio([a, b], cache))

    def test_undecodable_pair_falls_back_to_bytes(self) -> None:
        from ix_crate import music_replicants as mr

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "a.m4p", b"drm-bytes")
            b = _file(root / "b.m4p", b"drm-bytes")
            self.assertTrue(mr.same_audio([a, b], {}))

    def test_a_file_that_cannot_be_read_blocks_the_match(self) -> None:
        from ix_crate import music_replicants as mr

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _file(root / "a.m4a", b"x")
            cache = {str(a): "audio:MD5=one", str(root / "gone.m4a"): ""}
            self.assertFalse(mr.same_audio([a, root / "gone.m4a"], cache))


class DecodedDigestTest(unittest.TestCase):
    def _wav(self, path: Path, seconds: float, tone: int) -> Path:
        import math, struct, wave

        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(22050)
            n = int(22050 * seconds)
            w.writeframes(b"".join(
                struct.pack("<h", int(16000 * math.sin(2 * math.pi * tone * i / 22050)))
                for i in range(n)
            ))
        return path

    def test_same_audio_hashes_equal_across_copies(self) -> None:
        from ix_crate.music_replicants import decoded_digest

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = self._wav(root / "a.wav", 0.4, 440)
            b = root / "b.wav"
            b.write_bytes(a.read_bytes())
            first = decoded_digest(a)
            if not first:
                self.skipTest("ffmpeg not available")
            self.assertEqual(first, decoded_digest(b))

    def test_different_audio_hashes_differ(self) -> None:
        from ix_crate.music_replicants import decoded_digest

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = self._wav(root / "a.wav", 0.4, 440)
            b = self._wav(root / "b.wav", 0.4, 880)
            first = decoded_digest(a)
            if not first:
                self.skipTest("ffmpeg not available")
            self.assertNotEqual(first, decoded_digest(b))

    def test_digest_carries_duration(self) -> None:
        from ix_crate.music_replicants import decoded_digest

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = self._wav(root / "a.wav", 1.0, 440)
            digest = decoded_digest(a)
            if not digest:
                self.skipTest("ffmpeg not available")
            self.assertTrue(digest.startswith("audio:1.0:MD5="), digest)

    def test_non_audio_yields_nothing(self) -> None:
        from ix_crate.music_replicants import decoded_digest

        with TemporaryDirectory() as tmp:
            junk = Path(tmp) / "x.m4a"
            junk.write_bytes(b"not audio at all")
            self.assertEqual(decoded_digest(junk), "")
