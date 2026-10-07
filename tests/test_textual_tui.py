import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Button, TextArea
from talkenglish.tui import TalkEnglishApp

class TestTextualTUI(unittest.IsolatedAsyncioTestCase):
    async def test_app_composition(self):
        mock_mw = MagicMock()
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            input_area = app.query_one("#input-text", TextArea)
            output_area = app.query_one("#output-text", TextArea)
            btn_refine = app.query_one("#btn-refine", Button)
            btn_clear = app.query_one("#btn-clear", Button)
            btn_copy = app.query_one("#btn-copy", Button)

            self.assertIsNotNone(input_area)
            self.assertIsNotNone(output_area)
            self.assertIsNotNone(btn_refine)
            self.assertIsNotNone(btn_clear)
            self.assertIsNotNone(btn_copy)
            self.assertEqual(input_area.text, "")
            self.assertEqual(output_area.text, "")

    async def test_clear_button(self):
        mock_mw = MagicMock()
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            input_area = app.query_one("#input-text", TextArea)
            input_area.text = "Sample prompt to clear"
            await pilot.click("#btn-clear")
            self.assertEqual(input_area.text, "")

    async def test_refine_empty_notifies_warning(self):
        mock_mw = MagicMock()
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            with patch.object(app, "notify") as mock_notify:
                await pilot.click("#btn-refine")
                mock_mw.process.assert_not_called()
                mock_notify.assert_called_with("Input prompt is empty.", severity="warning")

    async def test_refine_success(self):
        mock_mw = MagicMock()
        mock_mw.process.return_value = "Refactored engineering prompt"
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            input_area = app.query_one("#input-text", TextArea)
            output_area = app.query_one("#output-text", TextArea)

            input_area.text = "یک تسک تستی"
            await pilot.click("#btn-refine")
            # Wait for background worker thread to finish
            await pilot.pause(0.2)

            self.assertEqual(output_area.text, "Refactored engineering prompt")
            mock_mw.process.assert_called_once_with("یک تسک تستی")

    async def test_copy_button(self):
        mock_mw = MagicMock()
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            output_area = app.query_one("#output-text", TextArea)
            output_area.text = "Text to copy"
            with patch.object(app, "copy_to_clipboard") as mock_clipboard:
                await pilot.click("#btn-copy")
                mock_clipboard.assert_called_once_with("Text to copy")

    async def test_refine_error_handles_cleanly(self):
        mock_mw = MagicMock()
        mock_mw.process.side_effect = RuntimeError("Upstream API error")
        app = TalkEnglishApp(middleware=mock_mw)
        async with app.run_test() as pilot:
            input_area = app.query_one("#input-text", TextArea)
            input_area.text = "Prompt failing"
            with patch.object(app, "notify") as mock_notify:
                await pilot.click("#btn-refine")
                await pilot.pause(0.2)
                mock_notify.assert_any_call("Refinement error: Upstream API error", severity="error")

if __name__ == "__main__":
    unittest.main()
