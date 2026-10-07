import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch
from talkenglish.clipboard import copy_to_system_clipboard

class TestClipboard(unittest.TestCase):
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_wayland_wl_copy(self, mock_run, mock_which):
        mock_which.side_effect = lambda cmd: "/usr/bin/wl-copy" if cmd == "wl-copy" else None
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}, clear=False):
            result = copy_to_system_clipboard("test text")
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["wl-copy"],
            input="test text".encode("utf-8"),
            check=True,
            timeout=2
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_x11_xclip(self, mock_run, mock_which):
        def fake_which(cmd):
            return "/usr/bin/xclip" if cmd == "xclip" else None
        mock_which.side_effect = fake_which
        env = {"DISPLAY": ":0"}
        with patch.dict(os.environ, env, clear=True):
            result = copy_to_system_clipboard("x11 text")
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["xclip", "-selection", "clipboard"],
            input="x11 text".encode("utf-8"),
            check=True,
            timeout=2
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_x11_xsel_fallback_when_xclip_missing(self, mock_run, mock_which):
        mock_which.side_effect = lambda cmd: "/usr/bin/xsel" if cmd == "xsel" else None
        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
            result = copy_to_system_clipboard("xsel text")
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["xsel", "--clipboard", "--input"],
            input="xsel text".encode("utf-8"),
            check=True,
            timeout=2
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_macos_pbcopy(self, mock_run, mock_which):
        mock_which.side_effect = lambda cmd: "/usr/bin/pbcopy" if cmd == "pbcopy" else None
        with patch("sys.platform", "darwin"):
            result = copy_to_system_clipboard("mac text")
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["pbcopy"],
            input="mac text".encode("utf-8"),
            check=True,
            timeout=2
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_windows_clip(self, mock_run, mock_which):
        mock_which.side_effect = lambda cmd: "clip.exe" if cmd == "clip" else None
        with patch("sys.platform", "win32"):
            result = copy_to_system_clipboard("win text")
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["clip"],
            input="win text".encode("utf-8"),
            check=True,
            timeout=2
        )

    @patch("shutil.which", return_value=None)
    @patch("sys.stdout.write")
    @patch("sys.stdout.flush")
    def test_osc52_fallback_when_no_tools(self, mock_flush, mock_write, mock_which):
        with patch.dict(os.environ, {}, clear=True):
            result = copy_to_system_clipboard("osc text")
        self.assertTrue(result)
        self.assertTrue(mock_write.called)
        written_arg = mock_write.call_args[0][0]
        self.assertIn("\033]52;c;", written_arg)

    def test_empty_text_returns_false(self):
        self.assertFalse(copy_to_system_clipboard(""))

if __name__ == "__main__":
    unittest.main()
