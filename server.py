import http.server
import socketserver
import json
import sqlite3
import os

PORT = 10000

# Dit zorgt ervoor dat Python ALTIJD naar de juiste hoofdmap kijkt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# We gebruiken de actieve database uit je lijst
DB_FILE = os.path.join(BASE_DIR, "poc_radio.db")

def haal_gebruikers_op():
    if not os.path.exists(DB_FILE):
        return []
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
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
        # API Route voor gebruikers
        if self.path == '/api/users':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(haal_gebruikers_op()).encode('utf-8'))
        
        # Website hoofdpagina Routes
        elif self.path in ['/', '/online.html', '/index.html']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Koppel het absolute pad naar online.html
            html_pad = os.path.join(BASE_DIR, 'online.html')
            
            if os.path.exists(html_pad):
                with open(html_pad, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                # Mocht hij het bestand écht niet vinden, dan zien we nu precies waar hij zoekt
                fout_bericht = f"<h1>Fout: online.html niet gevonden op locatie: {html_pad}</h1>"
                self.wfile.write(fout_bericht.encode('utf-8'))
        else:
            super().do_GET()

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait succesvol op poort", PORT)
    httpd.serve_forever()
