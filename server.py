import os
import json
import sqlite3
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

PORT = int(os.environ.get("PORT", "10000"))
DB_FILE = os.environ.get("DB_FILE", "poc_radio.db")


def get_radios():
    if not os.path.exists(DB_FILE):
        return []

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute("SELECT * FROM radios").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


class Handler(SimpleHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path).path

        if path in ("/api/radios", "/api/public/radios"):
            try:
                radios = get_radios()
                data = json.dumps(radios).encode("utf-8")

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/json; charset=utf-8"
                )
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            except Exception as e:
                data = json.dumps(
                    {"error": str(e)}
                ).encode("utf-8")

                self.send_response(500)
                self.send_header(
                    "Content-Type",
                    "application/json; charset=utf-8"
                )
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

        if path == "/online":
            self.path = "/online.html"

        return super().do_GET()


if __name__ == "__main__":
    print(
        f"POC RADIO BE server gestart op poort {PORT}",
        flush=True
    )

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
