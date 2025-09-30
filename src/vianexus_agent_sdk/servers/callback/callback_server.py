import json
import time
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class CallbackHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler to capture OAuth callback."""

    def __init__(self, request, client_address, server, callback_data):
        """Initialize with callback data storage."""
        self.callback_data = callback_data
        super().__init__(request, client_address, server)

    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        logging.debug(f"Received callback: {self.path}")
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)

        if "code" in query_params:
            self.callback_data["authorization_code"] = query_params["code"][0]
            self.callback_data["state"] = query_params.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.callback_data).encode())
        elif "error" in query_params:
            self.callback_data["error"] = query_params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.callback_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class CallbackServer():
    """Simple server to handle OAuth callbacks."""

    def __init__(self, port=3000):
        self.port = port
        self.server = None
        self.thread = None
        self.callback_data = {"authorization_code": None, "state": None, "error": None}
        self._running = False

    def _create_handler_with_data(self):
        """Create a handler class with access to callback data."""
        callback_data = self.callback_data

        class DataCallbackHandler(CallbackHandler):
            def __init__(self, request, client_address, server):
                super().__init__(request, client_address, server, callback_data)

        return DataCallbackHandler

    def start(self):
        """Start the callback server in a background thread."""
        if self._running:
            logging.warning("Callback server is already running")
            return

        try:
            handler_class = self._create_handler_with_data()
            self.server = HTTPServer(("localhost", self.port), handler_class)
            self.thread = threading.Thread(target=self._serve_forever, daemon=True)
            self.thread.start()
            self._running = True
            logging.debug(f"Started callback server on http://localhost:{self.port}")
        except OSError as e:
            if e.errno == 98:  # Address already in use
                raise RuntimeError(f"Port {self.port} is already in use. Please try again or use a different port.") from e
            else:
                raise e

    def _serve_forever(self):
        """Serve forever in a thread-safe manner."""
        try:
            self.server.serve_forever()
        except Exception as e:
            logging.error(f"Callback server error: {e}")

    def stop(self):
        """Stop the callback server."""
        if not self._running:
            return

        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)
                if self.thread.is_alive():
                    logging.warning("Callback server thread did not stop gracefully")
        except Exception as e:
            logging.error(f"Error stopping callback server: {e}")
        finally:
            self._running = False
            self.server = None
            self.thread = None

    def wait_for_callback(self, timeout=300):
        """Wait for OAuth callback with timeout."""
        if not self._running:
            raise RuntimeError("Callback server is not running")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.callback_data["authorization_code"]:
                return self.callback_data["authorization_code"]
            elif self.callback_data["error"]:
                raise Exception(f"OAuth error: {self.callback_data['error']}")
            time.sleep(0.1)
        raise Exception("Timeout waiting for OAuth callback")

    def get_state(self):
        """Get the received state parameter."""
        return self.callback_data["state"]

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.stop()