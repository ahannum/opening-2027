"""Redraw the phone player's frames.

Run from the repo root:

    python3 tools/export_player.py

then open http://localhost:8010/tools/export-player.html. The page draws every Polka and Waltz story
with the planner and this server writes them into app/frames/ and app/stories.js. Commit and push
those files to update the player on GitHub Pages.
"""
import http.server
import os
import shutil
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
PORT = 8010


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(url.query)
        if url.path == "/reset":
            shutil.rmtree(os.path.join(APP, "frames"), ignore_errors=True)
            return self._done()
        if url.path != "/save" or "path" not in query:
            return self._fail(404)
        rel = query["path"][0]
        dest = os.path.realpath(os.path.join(APP, rel))
        # Only app/stories.js and files under app/frames/ can be written.
        allowed = dest == os.path.join(APP, "stories.js") or dest.startswith(os.path.join(APP, "frames") + os.sep)
        if not allowed:
            return self._fail(400)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as handle:
            handle.write(self.rfile.read(int(self.headers["Content-Length"])))
        self._done()

    def _done(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def _fail(self, code):
        self.send_response(code)
        self.end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Open http://localhost:{PORT}/tools/export-player.html")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
