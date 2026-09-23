import http.server
import socketserver
import json
import sqlite3
import os

PORT = 10000
DB_FILE = "poc_radio(20260916 181056).db"  # We koppelen hem direct aan je back-up!

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def haal_gebruikers_op():
    db_pad = os.path.join(BASE_DIR, DB_FILE)
    if not os.path.exists(db_pad):
        return []
    conn = sqlite3.connect(db_pad)
    cursor = conn.cursor()
    try:
        # Haal de namen en status op uit je database
        cursor.execute("SELECT naam, online, tijd, laast_gezien FROM users")
        rows = cursor.fetchall()
    except:
        rows = []
    conn.close()
    
    gebruikers = []
    for r in rows:
        gebruikers.append({
            "naam": r[0] if len(r) > 0 else "Onbekend",
            "online": bool(r[1]) if len(r) > 1 else False,
            "tijd": r[2] if len(r) > 2 and r[2] else "-",
            "laast_gezien": r[3] if len(r) > 3 and r[3] else "-"
        })
    return gebruikers

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/users':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(haal_gebruikers_op()).encode('utf-8'))
        
        elif self.path in ['/', '/online.html', '/index.html']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_pad = os.path.join(BASE_DIR, 'online.html')
            if os.path.exists(html_pad):
                with open(html_pad, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.wfile.write(b"<h1>online.html niet gevonden</h1>")
        else:
            super().do_GET()

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait op poort", PORT)
    httpd.serve_forever()
