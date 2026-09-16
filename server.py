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
