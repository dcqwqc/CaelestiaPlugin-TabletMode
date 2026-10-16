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
        "sensor_offset_degrees": 0,
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


    def test_proxy_is_absolute_and_not_relative_to_old_display_state(self):
        dummy = DummyDaemon()
        dummy.transform = 3  # compositor was left in portrait
        orientation_from_proxy = Daemon.orientation_from_proxy
        for orientation in ("normal", "left-up", "bottom-up", "right-up"):
            self.assertEqual(orientation_from_proxy(dummy, orientation), orientation)

    def test_180_degree_user_calibration_applies_to_both_sensor_backends(self):
        dummy = DummyDaemon()
        dummy.cfg = dict(dummy.cfg, sensor_offset_degrees=180)
        raw = Daemon.orientation_from
        proxy = Daemon.orientation_from_proxy
        self.assertEqual(raw(dummy, (0.0, -1.0, 0.0)), "bottom-up")
        self.assertEqual(proxy(dummy, "normal"), "bottom-up")
        self.assertEqual(raw(dummy, (0.0, 1.0, 0.0)), "normal")
        self.assertEqual(proxy(dummy, "bottom-up"), "normal")
        self.assertEqual(raw(dummy, (-1.0, 0.0, 0.0)), "right-up")
        self.assertEqual(proxy(dummy, "left-up"), "right-up")

    def test_invalid_calibration_is_rejected_without_rotation(self):
        dummy = DummyDaemon()
        for bad in (45, 360, "xyz", None):
            dummy.cfg = dict(dummy.cfg, sensor_offset_degrees=bad)
            self.assertEqual(Daemon.orientation_from_proxy(dummy, "normal"), "normal")

    def test_sensor_calibration_and_portrait_side_swap(self):
        dummy = DummyDaemon()
        dummy.cfg = dict(dummy.cfg, sensor_offset_degrees=90, invert_sides=True)
        self.assertEqual(Daemon.orientation_from_proxy(dummy, "normal"), "right-up")

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
