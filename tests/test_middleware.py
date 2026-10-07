import unittest
from unittest.mock import MagicMock
from talkenglish.middleware import PromptMiddleware

class TestPromptMiddleware(unittest.TestCase):
    def test_english_bypasses_translator(self):
        mock_translator = MagicMock()
        middleware = PromptMiddleware(translator=mock_translator)

        result = middleware.process("Fix typo in README.md")
        self.assertEqual(result, "Fix typo in README.md")
        mock_translator.translate.assert_not_called()

    def test_non_english_calls_translator(self):
        mock_translator = MagicMock()
        mock_translator.translate.return_value = "Run tests in /tests/test_api.py"
        middleware = PromptMiddleware(translator=mock_translator)

        result = middleware.process("تست‌های /tests/test_api.py را اجرا کن")
        self.assertEqual(result, "Run tests in /tests/test_api.py")
        mock_translator.translate.assert_called_once_with("تست‌های /tests/test_api.py را اجرا کن")

if __name__ == "__main__":
    unittest.main()
