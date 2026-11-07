"""Draw every Polka and Waltz part as JPEGs for Google Slides, into deck/.

The GitHub workflow (.github/workflows/deck-frames.yml) runs this on every push that changes a
routine, so normally there's nothing to do by hand. To run it yourself, from the repo root:

    python3 tools/export_deck.py              # then open http://localhost:8010/tools/export-deck.html
    python3 tools/export_deck.py --headless   # draws without a window (needs: pip install playwright)

Only parts whose frames changed are redrawn. The frames land in deck/<part id>/NN.jpg with a list in
deck/frames.json; once pushed they're at https://ahannum.github.io/opening-2027/deck/, where the
Ground Truth decks' fillFrames() script picks them up.
"""
import http.server
import os
import shutil
import sys
import threading
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(ROOT, "deck")
PORT = 8010


def inside_deck(rel):
    dest = os.path.realpath(os.path.join(DECK, rel))
    return dest if dest.startswith(DECK + os.sep) else None


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(url.query)
        # Only files and folders inside deck/ can be written or removed.
        if url.path == "/remove" and "dir" in query:
            dest = inside_deck(query["dir"][0])
            if not dest:
                return self._reply(400)
            shutil.rmtree(dest, ignore_errors=True)
            return self._reply(200)
        if url.path == "/save" and "path" in query:
            dest = inside_deck(query["path"][0])
            if not dest:
                return self._reply(400)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as handle:
                handle.write(self.rfile.read(int(self.headers["Content-Length"])))
            return self._reply(200)
        self._reply(404)

    def _reply(self, code):
        self.send_response(code)
        self.end_headers()
        if code == 200:
            self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


def headless(server):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda message: print("page:", message.text) if message.type == "error" else None)
        page.goto(f"http://127.0.0.1:{PORT}/tools/export-deck.html?auto")
        page.wait_for_function("document.title === 'done' || document.title === 'failed'", timeout=600_000)
        print(page.inner_text("#status"))
        for line in page.locator("#log li").all_inner_texts():
            print(" ", line)
        ok = page.title() == "done"
        browser.close()
    server.shutdown()
    return ok


if __name__ == "__main__":
    os.makedirs(DECK, exist_ok=True)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    if "--headless" in sys.argv:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        sys.exit(0 if headless(server) else 1)
    print(f"Open http://localhost:{PORT}/tools/export-deck.html")
    server.serve_forever()
