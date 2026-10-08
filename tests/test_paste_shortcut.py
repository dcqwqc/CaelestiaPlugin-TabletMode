"""Focused paste shortcut selection for the touch keyboard panes."""
import importlib.machinery
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HELPER = Path(__file__).resolve().parents[1] / "scripts" / "osk-action"
loader = importlib.machinery.SourceFileLoader("osk_action", str(HELPER))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)


class PasteShortcutTests(unittest.TestCase):
    def check_shortcut(self, window_class, expected):
        calls = []

        def execute(command, **kwargs):
            calls.append(command)
            if command[0] == "hyprctl":
                return SimpleNamespace(stdout='{"class": "' + window_class + '"}', returncode=0)
            return SimpleNamespace(stdout="", returncode=0)

        with patch.object(module.subprocess, "run", side_effect=execute), \
             patch.object(module.shutil, "which", return_value="/usr/bin/ydotool"), \
             patch.object(module.Path, "is_socket", return_value=True):
            self.assertTrue(module.paste_shortcut())

        self.assertEqual(calls[-1][0], expected)

    def test_sumi_uses_uinput(self):
        self.check_shortcut("sumi", "ydotool")

    def test_other_apps_use_existing_wtype(self):
        self.check_shortcut("app.zen_browser.zen", "wtype")


if __name__ == "__main__":
    unittest.main()
