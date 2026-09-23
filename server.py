import http.server
import socketserver
import json
import sqlite3
import os

PORT = 10000
DB_FILE = "poc_radio.db"

# Zoek de exacte map op waar dit script (server.py) staat op de Render-server
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def haal_gebruikers_op():
    db_pad = os.path.join(BASE_DIR, DB_FILE)
    conn = sqlite3.connect(db_pad)
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
            "naam": r,
            "online": bool(r),
            "tijd": r if r else "-",
            "laast_gezien": r if r else "-"
        })
    return gebruikers

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # API Route voor de gebruikers
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
            
            # Koppel het absolute pad naar online.html aan de serveromgeving
            html_pad = os.path.join(BASE_DIR, 'online.html')
            
            if os.path.exists(html_pad):
                with open(html_pad, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                # Als het bestand echt ontbreekt in de repository, laat dit dan duidelijk zien
                zelf_gemaakte_fout = f"<h1>Fout: online.html kon niet worden gevonden op locatie: {html_pad}</h1>"
                self.wfile.write(zelf_gemaakte_fout.encode('utf-8'))
        else:
            # Fallback
            super().do_GET()

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait succesvol op poort", PORT)
    httpd.serve_forever()
