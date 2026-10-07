import json
import os
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from talkenglish.middleware import PromptMiddleware

STATIC_DIR = os.path.join(os.path.dirname(__file__), "web")

class TalkEnglishRequestHandler(SimpleHTTPRequestHandler):
    middleware: Optional[PromptMiddleware] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, format, *args):
        # ponytail: suppress default request spam in console, add logger when multi-tenant
        pass

    def do_POST(self):
        if self.path == "/api/refine":
            self.handle_refine()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def handle_refine(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0 or content_length > 1_000_000:
                self._send_json({"error": "Invalid content length"}, status=HTTPStatus.BAD_REQUEST)
                return

            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
            prompt = payload.get("prompt", "")

            if not isinstance(prompt, str):
                self._send_json({"error": "Field 'prompt' must be string"}, status=HTTPStatus.BAD_REQUEST)
                return

            if self.middleware is None:
                self.middleware = PromptMiddleware()

            result = self.middleware.process(prompt)
            self._send_json({"result": result})
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, status=HTTPStatus.BAD_REQUEST)
        except Exception as e:
            self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _send_json(self, data: dict, status: int = HTTPStatus.OK):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def run_server(host: str = "127.0.0.1", port: int = 8000, middleware: Optional[PromptMiddleware] = None):
    # ponytail: stdlib ThreadingHTTPServer used. Upgrade to uvicorn/fastapi if websocket/streaming needed
    class CustomHandler(TalkEnglishRequestHandler):
        pass

    CustomHandler.middleware = middleware
    server = ThreadingHTTPServer((host, port), CustomHandler)
    print(f"TalkEnglish Web UI running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
