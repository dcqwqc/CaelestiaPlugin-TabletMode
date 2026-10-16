"""The OSK may show its utility toolbar, but never a draggable keyboard handle."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class NoKeyboardHandleTest(unittest.TestCase):
    def test_no_handle_layer_or_hitbox(self):
        source = (ROOT / "osk/shell.qml").read_text()
        for fragment in ("yoga-osk-handle", "closeGrabberHitbox", "closeGrabberArea", "id: win", "onReleased: win.trigger"):
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)
        self.assertIn("yoga-osk-toolbar", source)
        self.assertIn("yoga-osk-pager", source)
        self.assertIn("function animateState", source)

    def test_no_setting_can_restore_handle(self):
        self.assertNotIn("oskHandle", (ROOT / "Settings.qml").read_text())
        daemon = (ROOT / "scripts/yoga-tablet").read_text()
        self.assertNotIn('if not self.cfg.get("osk_handle"', daemon)
        self.assertIn('self.grab.start(name, mode="open", bottom=0)', daemon)

if __name__ == "__main__":
    unittest.main()
