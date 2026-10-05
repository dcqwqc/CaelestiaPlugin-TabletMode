import runpy
import unittest
from pathlib import Path

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "yoga-tablet"))
Daemon = MODULE["Daemon"]


class DummyDaemon:
    cfg = {
        "threshold_g": 0.55,
        "flat_threshold_g": 0.80,
        "invert_sides": False,
    }
    orientation = "normal"


class RotationMappingTests(unittest.TestCase):
    def test_iio_axis_signs(self):
        dummy = DummyDaemon()
        orientation_from = Daemon.orientation_from
        self.assertEqual(orientation_from(dummy, (0.0, -1.0, 0.0)), "normal")
        self.assertEqual(orientation_from(dummy, (0.0, 1.0, 0.0)), "bottom-up")
        self.assertEqual(orientation_from(dummy, (1.0, 0.0, 0.0)), "right-up")
        self.assertEqual(orientation_from(dummy, (-1.0, 0.0, 0.0)), "left-up")

    def test_invert_sides_is_explicit_override(self):
        dummy = DummyDaemon()
        dummy.cfg = dict(dummy.cfg, invert_sides=True)
        orientation_from = Daemon.orientation_from
        self.assertEqual(orientation_from(dummy, (1.0, 0.0, 0.0)), "left-up")
        self.assertEqual(orientation_from(dummy, (-1.0, 0.0, 0.0)), "right-up")


if __name__ == "__main__":
    unittest.main()
