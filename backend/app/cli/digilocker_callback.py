"""Local-demo callback relay. Tunnel this port, not the application or backend."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import UUID


def callback_handler(frontend_url: str) -> type[BaseHTTPRequestHandler]:
    target = urlsplit(frontend_url)
    if (
        target.scheme != "http"
        or target.hostname not in {"localhost", "127.0.0.1"}
        or target.username
        or target.password
        or target.query
        or target.fragment
    ):
        raise ValueError("The demo callback must return to a local HTTP frontend URL.")

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            request = urlsplit(self.path)
            if request.path != "/callback":
                self.send_error(404)
                return
            try:
                verification = str(UUID(parse_qs(request.query)["verification"][0]))
            except (KeyError, ValueError, IndexError):
                self.send_error(400, "Missing or invalid verification reference")
                return
            # Forward only our record ID; provider tokens and codes never reach the frontend.
            self.send_response(303)
            self.send_header(
                "Location", frontend_url + "?" + urlencode({"verification": verification})
            )
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()

        def log_message(self, *_args):
            pass

    return CallbackHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--frontend-url", default="http://localhost:3000/dashboard/profile")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), callback_handler(args.frontend_url))
    print(f"DigiLocker demo callback listening on 127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
