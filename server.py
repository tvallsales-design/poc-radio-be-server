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
        gebruikers.append({
            "naam": r[0],
            "online": bool(r[1]),
            "tijd": r[2] if r[2] else "-",
            "laast_gezien": r[3] if r[3] else "-"
        })
    return gebruikers

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Als er gezocht wordt naar de API, geef de gebruikerslijst door
        if self.path == '/api/users':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(haal_gebruikers_op()).encode('utf-8'))
        
        # Als de website geladen wordt (via / of /online.html), toon de HTML-pagina
        elif self.path == '/' or self.path == '/online.html' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Controleer of het bestand online.html lokaal bestaat om in te laden
            bestandsnaam = 'online.html'
            if os.path.exists(bestandsnaam):
                with open(bestandsnaam, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.wfile.write(b"<h1>online.html niet gevonden op de server</h1>")
        else:
            # Fallback voor stylesheets of afbeeldingen
            super().do_GET()

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait succesvol op poort", PORT)
    httpd.serve_forever()
