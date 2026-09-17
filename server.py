import os
import json
import sqlite3
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

PORT = int(os.environ.get("PORT", "10000"))
DB_FILE = os.environ.get("DB_FILE", "poc_radio.db")


def db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_chat():
    conn = db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_radios():
    if not os.path.exists(DB_FILE):
        return []

    conn = db_connection()

    try:
        rows = conn.execute("""
            SELECT *
            FROM radios
            ORDER BY
                CASE
                    WHEN LOWER(status) = 'online' THEN 0
                    ELSE 1
                END,
                name COLLATE NOCASE
        """).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def get_chat_messages():
    conn = db_connection()

    try:
        rows = conn.execute("""
            SELECT id, name, message, created_at
            FROM chat_messages
            ORDER BY id DESC
            LIMIT 50
        """).fetchall()

        # oudste bericht eerst tonen
        return [dict(row) for row in reversed(rows)]

    finally:
        conn.close()


def add_chat_message(name, message):

    name = str(name).strip()[:40]
    message = str(message).strip()[:500]

    if not name:
        raise ValueError("Naam ontbreekt.")

    if not message:
        raise ValueError("Bericht ontbreekt.")

    created_at = datetime.now().strftime("%d-%m-%Y %H:%M")

    conn = db_connection()

    try:
        conn.execute("""
            INSERT INTO chat_messages
            (name, message, created_at)
            VALUES (?, ?, ?)
        """, (name, message, created_at))

        conn.commit()

    finally:
        conn.close()


class Handler(SimpleHTTPRequestHandler):

    def send_json(self, data, status=200):

        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()
        self.wfile.write(body)


    def do_GET(self):

        path = urlparse(self.path).path

        # RADIO LIJST
        if path in (
            "/api/radios",
            "/api/public/radios"
        ):

            try:
                self.send_json(get_radios())

            except Exception as e:
                self.send_json(
                    {"error": str(e)},
                    500
                )

            return


        # CHATBERICHTEN
        if path == "/api/chat":

            try:
                self.send_json(
                    get_chat_messages()
                )

            except Exception as e:
                self.send_json(
                    {"error": str(e)},
                    500
                )

            return


        # ONLINE PAGINA
        if path == "/online":
            self.path = "/online.html"


        return super().do_GET()


    def do_POST(self):

        path = urlparse(self.path).path

        if path != "/api/chat":
            self.send_json(
                {"error": "Niet gevonden"},
                404
            )
            return


        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            raw = self.rfile.read(length)

            data = json.loads(
                raw.decode("utf-8")
            )

            name = data.get("name", "")
            message = data.get("message", "")

            add_chat_message(
                name,
                message
            )

            self.send_json({
                "ok": True
            })

        except ValueError as e:

            self.send_json(
                {"error": str(e)},
                400
            )

        except Exception as e:

            self.send_json(
                {"error": str(e)},
                500
            )


if __name__ == "__main__":

    init_chat()

    print(
        f"POC RADIO BE server gestart op poort {PORT}",
        flush=True
    )

    server = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        Handler
    )

    server.serve_forever()
