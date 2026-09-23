import http.server
import socketserver
import json
import sqlite3
import os
from datetime import datetime
from urllib.parse import parse_qs

PORT = 10000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "poc_radio.db")

# Veilig intern geheugen voor live chatberichten
if 'chat_berichten' not in globals():
    chat_berichten = []

def haal_gebruikers_uit_db():
    if not os.path.exists(DB_FILE):
        print("Database bestand nog niet gevonden op locatie:", DB_FILE)
        return []
        
    conn = sqlite3.connect(DB_FILE)
    # Dit zorgt ervoor dat we kolommen via hun NAAM kunnen aanroepen in plaats van nummers!
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    gebruikers = []
    
    try:
        cursor.execute("SELECT naam, online, laast_gezien FROM users")
        rows = cursor.fetchall()
        for rij in rows:
            # Volkomen veilig tegen tekstfiltering: we gebruiken tekst-keys!
            gebruikers.append({
                "naam": str(rij["naam"]) if rij["naam"] else "Onbekend",
                "online": bool(rij["online"]),
                "laast_gezien": str(rij["laast_gezien"]) if rij["laast_gezien"] else "-"
            })
    except Exception as e:
        print("Database SELECT fout (Tabel of kolommen missen mogelijk):", e)
        gebruikers = [{"naam": "Database Leeg / Fout", "online": False, "laast_gezien": "-"}]
    finally:
        conn.close()
        
    return gebruikers

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # API Route voor live gebruikers
        if self.path == '/api/users':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(haal_gebruikers_out_db()).encode('utf-8'))
            return
            
        # API Route voor de chatbox
        elif self.path == '/api/chat':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(chat_berichten).encode('utf-8'))
            return
        
        # Website hoofdpagina Routes
        elif self.path in ['/', '/online.html', '/index.html'] or 'online_met_contact' in self.path:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_pad = os.path.join(BASE_DIR, 'online_met_contact (1).html')
            if os.path.exists(html_pad):
                with open(html_pad, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.wfile.write(b"<h1>Fout: HTML-bestand niet gevonden!</h1>")
            return
            
        super().do_GET()

    def do_POST(self):
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                content_type = self.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    data = json.loads(post_data.decode('utf-8'))
                    naam = data.get("naam", "Anoniem")
                    bericht = data.get("bericht", "")
                else:
                    data = parse_qs(post_data.decode('utf-8'))
                    naam = data.get("naam", ["Anoniem"])[0]
                    bericht = data.get("bericht", [""])[0]

                if bericht.strip():
                    chat_berichten.append({
                        "naam": naam,
                        "bericht": bericht,
                        "tijd": datetime.now().strftime("%H:%M")
                    })
                if len(chat_berichten) > 50:
                    chat_berichten.pop(0)
            except Exception as e:
                print("Fout bij verwerken POST:", e)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            return

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait succesvol op poort", PORT)
    httpd.serve_forever()
