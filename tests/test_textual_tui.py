import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Button, TextArea
from talkenglish.tui import TalkEnglishApp

class TestTextualTUI(unittest.IsolatedAsyncioTestCase):
    async def test_app_composition_has_no_buttons(self):
        mock_mw = MagicMock()
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            input_area = app.query_one("#input-text", TextArea)
            output_area = app.query_one("#output-text", TextArea)
            buttons = list(app.query(Button))

            self.assertIsNotNone(input_area)
            self.assertIsNotNone(output_area)
            self.assertEqual(len(buttons), 0, "No buttons should exist in the TUI")
            self.assertEqual(input_area.text, "")
            self.assertEqual(output_area.text, "")

    async def test_clear_shortcut(self):
        mock_mw = MagicMock()
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            input_area = app.query_one("#input-text", TextArea)
            input_area.text = "Sample prompt to clear"
            await pilot.press("ctrl+k")
            self.assertEqual(input_area.text, "")

    async def test_refine_empty_notifies_warning(self):
        mock_mw = MagicMock()
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            with patch.object(app, "notify") as mock_notify:
                await pilot.press("ctrl+j")
                mock_mw.process.assert_not_called()
                mock_notify.assert_called_with("Input prompt is empty.", severity="warning")

    async def test_refine_shortcut_success(self):
        mock_mw = MagicMock()
        mock_mw.process.return_value = "Refactored engineering prompt"
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            input_area = app.query_one("#input-text", TextArea)
            output_area = app.query_one("#output-text", TextArea)

            input_area.text = "یک تسک تستی"
            await pilot.press("ctrl+j")
            await pilot.pause(0.2)

            self.assertEqual(output_area.text, "Refactored engineering prompt")
            mock_mw.process.assert_called_once_with("یک تسک تستی")

    @patch("talkenglish.tui.copy_to_system_clipboard", return_value=True)
    async def test_copy_shortcut(self, mock_copy_system):
        mock_mw = MagicMock()
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            output_area = app.query_one("#output-text", TextArea)
            output_area.text = "Text to copy"
            with patch.object(app, "copy_to_clipboard") as mock_clipboard:
                await pilot.press("ctrl+y")
                mock_clipboard.assert_called_once_with("Text to copy")
            mock_copy_system.assert_called_once_with("Text to copy")

    async def test_duplicate_refine_prevented_while_busy(self):
        mock_mw = MagicMock()
        mock_mw.process.side_effect = lambda text: "Done"
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            input_area = app.query_one("#input-text", TextArea)
            input_area.text = "تست"
            app.is_busy = True
            with patch.object(app, "notify") as mock_notify:
                await pilot.press("ctrl+j")
                mock_mw.process.assert_not_called()
                mock_notify.assert_called_with("Already refining prompt...", severity="warning")

if __name__ == "__main__":
    unittest.main()
