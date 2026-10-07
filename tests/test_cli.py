import io
import sys
import unittest
from unittest.mock import MagicMock, patch
from talkenglish.main import main, parse_args, run_cli

class TestCLI(unittest.TestCase):
    def test_parse_args_headless_with_prompt(self):
        args = parse_args(["--headless", "تست"])
        self.assertTrue(args.headless)
        self.assertEqual(args.prompt, "تست")

    def test_parse_args_default_tui(self):
        args = parse_args([])
        self.assertFalse(args.headless)
        self.assertIsNone(args.prompt)

    def test_parse_args_positional_only(self):
        args = parse_args(["test prompt"])
        self.assertFalse(args.headless)
        self.assertEqual(args.prompt, "test prompt")

    @patch("talkenglish.middleware.PromptMiddleware.process")
    def test_run_cli_headless_output(self, mock_process):
        mock_process.return_value = "Test output"
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            run_cli("تست")
        self.assertEqual(captured.getvalue().strip(), "Test output")

    @patch("talkenglish.tui.run_tui")
    @patch("sys.stdin.isatty", return_value=True)
    def test_main_launches_tui_by_default(self, mock_isatty, mock_run_tui):
        with patch("sys.argv", ["talkenglish"]):
            main()
        mock_run_tui.assert_called_once()

    @patch("talkenglish.main.run_cli")
    def test_main_runs_headless_flag(self, mock_run_cli):
        with patch("sys.argv", ["talkenglish", "--headless", "hello world"]):
            main()
        mock_run_cli.assert_called_once_with("hello world")

    @patch("talkenglish.main.run_cli")
    def test_main_runs_positional_argument(self, mock_run_cli):
        with patch("sys.argv", ["talkenglish", "hello world"]):
            main()
        mock_run_cli.assert_called_once_with("hello world")

    @patch("talkenglish.main.run_cli")
    @patch("sys.stdin.isatty", return_value=False)
    @patch("sys.stdin.read", return_value="piped prompt\n")
    def test_main_runs_piped_stdin(self, mock_read, mock_isatty, mock_run_cli):
        with patch("sys.argv", ["talkenglish"]):
            main()
        mock_run_cli.assert_called_once_with("piped prompt")

    @patch("sys.stdin.isatty", return_value=False)
    @patch("sys.stdin.read", return_value="")
    def test_main_headless_empty_input_exits(self, mock_read, mock_isatty):
        with patch("sys.argv", ["talkenglish", "--headless"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
