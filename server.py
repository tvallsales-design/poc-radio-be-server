import http.server
import socketserver
import json
import sqlite3
import os

PORT = 10000
DB_FILE = "poc_radio.db"

def haal_gebruikers_op():
    if not os.path.exists(DB_FILE):
        return []
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS users (naam TEXT PRIMARY KEY, online INTEGER, tijd TEXT, laast_gezien TEXT)")
        cursor.execute("SELECT naam, online, tijd, laast_gezien FROM users")
        rows = cursor.fetchall()
    except:
        rows = []
    conn.close()
    
    gebruikers = []
    for r in rows:
        gebruikers.append({"naam": r[0], "online": bool(r[1]), "tijd": r[2], "laast_gezien": r[3]})
    return gebruikers

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/users':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(haal_gebruikers_op()).encode('utf-8'))
        elif self.path == '/' or self.path == '/online.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            with open('online.html', 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
        else:
            super().do_GET()

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait op poort", PORT)
    httpd.serve_forever()
