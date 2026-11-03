import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from ix_crate.phone_status import STATUS_NAME, PhoneStatus

LOG = """
=== phase 5/8: stemit-chain-1 ===
2026-11-03T21:30:32Z Electronic: 3 tracks  3 to stem  queued 3
queued 100 across 30 genres (African → Electronica)
2026-11-03 13:00:00.042 - INFO - separator - Processing file: /Users/someone/Music/stems_audio/Colette/Feelin Hypnotized/Feelin Hypnotized (Electro Mix).m4a
Processing audio chunks:  10%|█         | 1/10 [00:01<00:09]\rProcessing audio chunks:  43%|████      | 4/10 [00:04<00:06]
ok 1/194 Feelin Hypnotized (Electro Mix).m4a
ok 2/194 Feelin Hypnotized (Electro Mix).m4a
fail 3/194 37 State Fair Suite_ Junk Food Blues - Narration.m4a: audio-separator failed (-6) for x
"""


class PhoneStatusTests(unittest.TestCase):
    def test_parses_babylon_log(self) -> None:
        with TemporaryDirectory() as tmp:
            status = PhoneStatus("BABYLON", Path(tmp) / STATUS_NAME, started=0)
            status.feed(LOG, now=600)
            data = status.payload(now=600)
        self.assertEqual(data["phase"], {"index": 5, "total": 8, "name": "stemit-chain-1"})
        self.assertEqual(data["passes"]["done"], 3)
        self.assertEqual(data["passes"]["total"], 194)
        self.assertEqual(data["passes"]["failed"], 1)
        self.assertEqual(data["passes"]["queued_tracks"], 100)
        self.assertEqual(data["track"], "Feelin Hypnotized (Electro Mix)")
        self.assertEqual(data["last_fail"], "37 State Fair Suite_ Junk Food Blues - Narration.m4a")

    def test_never_writes_paths(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / STATUS_NAME
            status = PhoneStatus("BABYLON", out, started=0)
            status.feed(LOG, now=600)
            status.flush(force=True, now=600)
            raw = out.read_text(encoding="utf-8")
        self.assertNotIn("/Users/", raw)
        self.assertNotIn("stems_audio", raw)
        json.loads(raw)

    def test_track_percent_follows_carriage_returns(self) -> None:
        with TemporaryDirectory() as tmp:
            status = PhoneStatus("BABYLON", Path(tmp) / STATUS_NAME, started=0)
            status.feed("Processing file: /x/a.mp3\nProcessing audio chunks:  10%|\rProcessing audio chunks:  43%|", now=5)
        self.assertEqual(status.track_pct, 43)

    def test_queue_planning_step(self) -> None:
        with TemporaryDirectory() as tmp:
            status = PhoneStatus("BABYLON", Path(tmp) / STATUS_NAME, started=0)
            status.feed("2026-11-03T21:17:15Z Alternative: 194 tracks  0 to stem  queued 0", now=5)
        self.assertEqual(status.step, "planning Alternative")

    def test_eta_from_pass_rate(self) -> None:
        with TemporaryDirectory() as tmp:
            status = PhoneStatus("BABYLON", Path(tmp) / STATUS_NAME, started=0)
            status.feed("ok 10/20 a.mp3", now=600)
            status.stem_started = 0
        self.assertEqual(status.eta_min(600), 10.0)

    def test_open_respects_off_switch_and_dir(self) -> None:
        with TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"IX_PHONE_STATUS": "0", "IX_STATUS_DIR": tmp}):
                self.assertIsNone(PhoneStatus.open("BABYLON"))
            with mock.patch.dict(os.environ, {"IX_PHONE_STATUS": "1", "IX_STATUS_DIR": tmp}):
                status = PhoneStatus.open("BABYLON")
                self.assertIsNotNone(status)
                self.assertTrue((Path(tmp) / STATUS_NAME).is_file())
                status.finish("done", "CRATER done")
                data = json.loads((Path(tmp) / STATUS_NAME).read_text(encoding="utf-8"))
        self.assertEqual(data["state"], "done")


if __name__ == "__main__":
    unittest.main()
