import runpy
import unittest
from pathlib import Path

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "yoga-tablet"))
Daemon = MODULE["Daemon"]
ORIGINAL_SENSOR_MOUNT = Daemon.orientation_from.__globals__["sensor_mount_quarters"]


class DummyDaemon:
    cfg = {
        "threshold_g": 0.55,
        "flat_threshold_g": 0.80,
        "invert_sides": False,
    }
    orientation = "normal"


class RotationMappingTests(unittest.TestCase):
    def setUp(self):
        Daemon.orientation_from.__globals__["sensor_mount_quarters"] = lambda: 0

    def tearDown(self):
        Daemon.orientation_from.__globals__["sensor_mount_quarters"] = ORIGINAL_SENSOR_MOUNT

    def test_iio_axis_signs(self):
        dummy = DummyDaemon()
        orientation_from = Daemon.orientation_from
        self.assertEqual(orientation_from(dummy, (0.0, -1.0, 0.0)), "normal")
        self.assertEqual(orientation_from(dummy, (0.0, 1.0, 0.0)), "bottom-up")
        self.assertEqual(orientation_from(dummy, (1.0, 0.0, 0.0)), "right-up")
        self.assertEqual(orientation_from(dummy, (-1.0, 0.0, 0.0)), "left-up")


    def test_mirai_mount_offset(self):
        Daemon.orientation_from.__globals__["sensor_mount_quarters"] = lambda: 1
        dummy = DummyDaemon()
        orientation_from = Daemon.orientation_from
        self.assertEqual(orientation_from(dummy, (1.0, 0.0, 0.0)), "normal")
        self.assertEqual(orientation_from(dummy, (-1.0, 0.0, 0.0)), "bottom-up")
        self.assertEqual(orientation_from(dummy, (0.0, -1.0, 0.0)), "left-up")
        self.assertEqual(orientation_from(dummy, (0.0, 1.0, 0.0)), "right-up")


    def test_live_proxy_relative_mapping_ignores_mount_offset(self):
        dummy = DummyDaemon()
        dummy.transform = 0
        dummy.orientation = "normal"
        dummy._proxy_baseline_orientation = None
        dummy._proxy_baseline_transform = 0

        orientation_from_proxy = Daemon.orientation_from_proxy
        self.assertEqual(orientation_from_proxy(dummy, "left-up"), "normal")
        self.assertEqual(orientation_from_proxy(dummy, "bottom-up"), "left-up")
        self.assertEqual(orientation_from_proxy(dummy, "right-up"), "bottom-up")
        self.assertEqual(orientation_from_proxy(dummy, "normal"), "right-up")

    def test_auto_rotation_scope(self):
        dummy = DummyDaemon()
        rotation_active = Daemon.rotation_active
        dummy.rotation_locked = False

        dummy.cfg = dict(dummy.cfg, auto_rotate="always")
        dummy.tablet_mode = False
        self.assertTrue(rotation_active(dummy))
        dummy.tablet_mode = True
        self.assertTrue(rotation_active(dummy))

        dummy.cfg = dict(dummy.cfg, auto_rotate="tablet")
        dummy.tablet_mode = False
        self.assertFalse(rotation_active(dummy))
        dummy.tablet_mode = True
        self.assertTrue(rotation_active(dummy))

        dummy.cfg = dict(dummy.cfg, auto_rotate="never")
        self.assertFalse(rotation_active(dummy))

        dummy.cfg = dict(dummy.cfg, auto_rotate="always")
        dummy.rotation_locked = True
        self.assertFalse(rotation_active(dummy))

    def test_invert_sides_is_explicit_override(self):
        dummy = DummyDaemon()
        dummy.cfg = dict(dummy.cfg, invert_sides=True)
        orientation_from = Daemon.orientation_from
        self.assertEqual(orientation_from(dummy, (1.0, 0.0, 0.0)), "left-up")
        self.assertEqual(orientation_from(dummy, (-1.0, 0.0, 0.0)), "right-up")


if __name__ == "__main__":
    unittest.main()
