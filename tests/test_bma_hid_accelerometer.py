"""Checks for Mira's vendor-HID BMA422 accelerometer decoder."""

import os
import runpy
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HidBmaAccelerometer = runpy.run_path(str(ROOT / "scripts" / "yoga-tablet"))[
    "HidBmaAccelerometer"
]
Daemon = runpy.run_path(str(ROOT / "scripts" / "yoga-tablet"))["Daemon"]


class BmaHidAccelerometerTests(unittest.TestCase):
    def test_face_up_base_means_normal_in_laptop_mode(self):
        daemon = type("Stub", (), {})()
        daemon.cfg = {"threshold_g": 0.55, "flat_threshold_g": 0.8}
        daemon.tablet_mode = False
        daemon.orientation = "left-up"
        daemon.orientation_from = lambda _g: daemon.orientation

        self.assertEqual(Daemon.orientation_from_bma(daemon, (0.01, -0.02, 0.99)), "normal")

        daemon.tablet_mode = True
        self.assertEqual(Daemon.orientation_from_bma(daemon, (0.01, -0.02, 0.99)), "left-up")

    def test_decodes_signed_custom_axes_from_report_two(self):
        reader, writer = os.pipe2(os.O_NONBLOCK)
        self.addCleanup(os.close, writer)

        sensor = HidBmaAccelerometer.__new__(HidBmaAccelerometer)
        sensor.path = Path("/dev/hidraw-test")
        sensor.fd = reader
        sensor.sample = None
        sensor.sample_time = 0.0
        sensor.last_discovery = time.monotonic()

        report = bytearray(41)
        report[0] = 2
        for start, value in zip((27, 31, 35), (-980665, 490332, 0)):
            report[start:start + 4] = value.to_bytes(4, "little", signed=True)
        os.write(writer, report)

        self.assertEqual(sensor.read_g(), (-1.0, 490332 / 980665.0, 0.0))
        sensor.close()

    def test_ignores_other_report_ids(self):
        reader, writer = os.pipe2(os.O_NONBLOCK)
        self.addCleanup(os.close, writer)

        sensor = HidBmaAccelerometer.__new__(HidBmaAccelerometer)
        sensor.path = Path("/dev/hidraw-test")
        sensor.fd = reader
        sensor.sample = None
        sensor.sample_time = 0.0
        sensor.last_discovery = time.monotonic()

        report = bytearray(41)
        report[0] = 6
        os.write(writer, report)

        self.assertIsNone(sensor.read_g())
        sensor.close()


if __name__ == "__main__":
    unittest.main()
