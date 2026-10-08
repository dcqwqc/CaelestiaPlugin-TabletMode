"""Regression tests for Mirai boot orientation and compositor resync."""
import importlib.machinery
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "yoga-tablet"
loader = importlib.machinery.SourceFileLoader("yoga_tablet_orientation", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
mod = importlib.util.module_from_spec(spec)
loader.exec_module(mod)


class OrientationTests(unittest.TestCase):
    def daemon(self, *, orientation="left-up", transform=1, locked=False, invert=False):
        daemon = mod.Daemon.__new__(mod.Daemon)
        daemon.cfg = {"auto_rotate": "always", "invert_sides": invert}
        daemon.tablet_mode = False
        daemon.rotation_locked = locked
        daemon.orientation = orientation
        daemon.transform = transform
        return daemon

    def test_proxy_normal_overrides_stale_portrait_baseline(self):
        daemon = self.daemon()
        self.assertEqual(daemon.orientation_from_proxy("normal"), "normal")

    def test_proxy_side_orientations_and_invert_setting(self):
        daemon = self.daemon(orientation="normal")
        self.assertEqual(daemon.orientation_from_proxy("left-up"), "left-up")
        self.assertEqual(daemon.orientation_from_proxy("right-up"), "right-up")
        daemon.cfg["invert_sides"] = True
        self.assertEqual(daemon.orientation_from_proxy("left-up"), "right-up")
        self.assertEqual(daemon.orientation_from_proxy("right-up"), "left-up")

    def test_mirai_landscape_raw_gravity_maps_to_normal(self):
        daemon = self.daemon()
        with patch.object(mod, "sensor_mount_quarters", return_value=0):
            self.assertEqual(daemon.orientation_from((-0.27, -9.56, -2.46)), "normal")
            self.assertEqual(daemon.orientation_from((9.4, 0, 0)), "right-up")
        self.assertEqual(mod.SENSOR_MOUNT_QUIRKS[("LENOVO", "83DJ")], 0)

    def test_reconcile_repairs_stale_daemon_or_compositor_state(self):
        daemon = self.daemon(orientation="normal", transform=1)
        applied = []
        daemon._current_transform = lambda: 0
        daemon.apply_transform = lambda target, reason="": applied.append((target, reason))
        daemon.reconcile_transform("startup sensor")
        self.assertEqual(applied, [(0, "startup sensor")])

        daemon.transform = 0
        daemon._current_transform = lambda: 1
        applied.clear()
        daemon.reconcile_transform("compositor sync")
        self.assertEqual(applied, [(0, "compositor sync")])

    def test_manual_rotation_lock_is_respected(self):
        daemon = self.daemon(orientation="normal", transform=1, locked=True)
        daemon._current_transform = lambda: 1
        applied = []
        daemon.apply_transform = lambda target, reason="": applied.append(target)
        daemon.reconcile_transform()
        self.assertEqual(applied, [])


if __name__ == "__main__":
    unittest.main()
