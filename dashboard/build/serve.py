"""Static server for the dashboard.

``python -m http.server`` will not do, for two reasons:

* **It does not serve byte ranges.**  PMTiles reads an archive by asking for
  slices of it — that is the whole point of the format, and why a 45 MB
  archive costs a few kilobytes to draw one screen.  ``SimpleHTTPRequestHandler``
  ignores the ``Range`` header and returns the whole file with a 200, and
  pmtiles.js rejects that with "Check that your storage backend supports HTTP
  Byte Serving".  GitHub Pages and most real servers support ranges; the
  stdlib one does not, so it is added here.

* **It caches.**  ES modules are cached by URL, and a relative import inside a
  cached module is not re-fetched even on a hard reload, so an edited module
  silently keeps running its old version.  Everything is served ``no-store``:
  this is a development and workshop server, not a CDN.

Usage:  python build/serve.py [port]   (from the dashboard directory)
"""

import functools
import http.server
import os
import re
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8123
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RANGE = re.compile(r'^bytes=(\d*)-(\d*)$')
CHUNK = 64 * 1024


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        '.pmtiles': 'application/octet-stream',
        '.js': 'text/javascript',
        '.json': 'application/json',
    }

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def _parse_range(self, size):
        """(start, end) inclusive for a satisfiable Range header, else None."""
        header = self.headers.get('Range')
        if not header:
            return None
        match = RANGE.match(header.strip())
        if not match:
            return None
        first, last = match.group(1), match.group(2)
        if first:
            start = int(first)
            end = int(last) if last else size - 1
        elif last:
            # a suffix range: the last N bytes, which is how pmtiles reads the
            # header of an archive it has not seen before
            start = max(0, size - int(last))
            end = size - 1
        else:
            return None
        if start >= size or start > end:
            return None
        return start, min(end, size - 1)

    def do_GET(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path) or not os.path.exists(path):
            return super().do_GET()
        size = os.path.getsize(path)
        span = self._parse_range(size)
        if span is None:
            return super().do_GET()
        start, end = span
        length = end - start + 1
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(length))
        self.end_headers()
        with open(path, 'rb') as handle:
            handle.seek(start)
            remaining = length
            while remaining > 0:
                block = handle.read(min(CHUNK, remaining))
                if not block:
                    break
                self.wfile.write(block)
                remaining -= len(block)
        return None

    def log_message(self, fmt, *args):
        sys.stderr.write(f'{fmt % args}\n')


if __name__ == '__main__':
    handler = functools.partial(Handler, directory=ROOT)
    print(f'http://localhost:{PORT}/   (Ctrl+C to stop)', flush=True)
    http.server.ThreadingHTTPServer(('', PORT), handler).serve_forever()
