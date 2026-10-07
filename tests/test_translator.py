import io
import json
import unittest
from unittest.mock import patch
from talkenglish.translator import PromptTranslator

class TestTranslator(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_successful_translation(self, mock_urlopen):
        mock_response = io.BytesIO(json.dumps({
            "choices": [{"message": {"content": "Refactor auth_handler in /app/auth.py"}}]
        }).encode("utf-8"))
        mock_urlopen.return_value.__enter__.return_value = mock_response

        translator = PromptTranslator(api_key="test-key", api_base="http://localhost:8000/v1")
        result = translator.translate("تابع auth_handler در /app/auth.py را بازنویسی کن")

        self.assertEqual(result, "Refactor auth_handler in /app/auth.py")
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("urllib.request.urlopen")
    def test_sse_event_stream_fallback(self, mock_urlopen):
        sse_payload = (
            'data: {"choices":[{"delta":{"content":"Write "}}]}\n\n'
            'data: {"choices":[{"delta":{"content":"factorial function."}}]}\n\n'
            'data: [DONE]\n'
        )
        mock_response = io.BytesIO(sse_payload.encode("utf-8"))
        mock_urlopen.return_value.__enter__.return_value = mock_response

        translator = PromptTranslator(api_key="test-key", api_base="http://localhost:8000/v1")
        result = translator.translate("یک تابع فاکتوریل بنویس")

        self.assertEqual(result, "Write factorial function.")

    @patch("urllib.request.urlopen")
    def test_network_failure_fallback(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection refused")

        translator = PromptTranslator(api_key="test-key", api_base="http://localhost:8000/v1")
        original = "تابع خراب"
        result = translator.translate(original)

        self.assertEqual(result, original)

if __name__ == "__main__":
    unittest.main()
