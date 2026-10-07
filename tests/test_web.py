import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock
from talkenglish.web_server import TalkEnglishRequestHandler

class TestWebServer(unittest.TestCase):
    def test_refine_api_endpoint(self):
        body = json.dumps({"prompt": "سلام دنیا"}).encode("utf-8")
        mock_middleware = MagicMock()
        mock_middleware.process.return_value = "Hello world"

        class TestHandler(TalkEnglishRequestHandler):
            middleware = mock_middleware
            def __init__(self):
                self.requestline = "POST /api/refine HTTP/1.1"
                self.request_version = "HTTP/1.1"
                self.rfile = BytesIO(body)
                self.wfile = BytesIO()
                self.headers = {"Content-Length": str(len(body))}
                self.path = "/api/refine"

        handler = TestHandler()
        handler.handle_refine()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("200 OK", output)
        self.assertIn('"result": "Hello world"', output)
        mock_middleware.process.assert_called_once_with("سلام دنیا")

    def test_refine_bad_json(self):
        class TestHandler(TalkEnglishRequestHandler):
            def __init__(self):
                self.requestline = "POST /api/refine HTTP/1.1"
                self.request_version = "HTTP/1.1"
                self.rfile = BytesIO(b"bad json")
                self.wfile = BytesIO()
                self.headers = {"Content-Length": "8"}
                self.path = "/api/refine"

        handler = TestHandler()
        handler.handle_refine()
        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("400 Bad Request", output)
        self.assertIn("Invalid JSON", output)

    def test_refine_invalid_prompt_type(self):
        body = json.dumps({"prompt": 12345}).encode("utf-8")
        class TestHandler(TalkEnglishRequestHandler):
            def __init__(self):
                self.requestline = "POST /api/refine HTTP/1.1"
                self.request_version = "HTTP/1.1"
                self.rfile = BytesIO(body)
                self.wfile = BytesIO()
                self.headers = {"Content-Length": str(len(body))}
                self.path = "/api/refine"

        handler = TestHandler()
        handler.handle_refine()
        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("400 Bad Request", output)
        self.assertIn("Field 'prompt' must be string", output)

if __name__ == "__main__":
    unittest.main()
