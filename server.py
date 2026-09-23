import http.server
import socketserver
import json
import sqlite3
import os
from datetime import datetime

PORT = 10000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "poc_radio.db")

def controleer_en_vul_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                naam TEXT UNIQUE NOT NULL,
                online INTEGER NOT NULL DEFAULT 0,
                laast_gezien TEXT DEFAULT '-'
            )
        ''')
        
        # HIER KUN JE JOUW EIGEN ONLINE EN OFFLINE GEBRUIKERS TOEVOEGEN!
        # Structuur: ("Naam", 1 voor Online / 0 voor Offline, "Tijdstip")
        mijn_gebruikers = [
            # --- JOUW ONLINE GEBRUIKERS (GROEN) ---
            ("ON3OSJ - Handheld", 1, "Nu online"),
            ("ROEPNAAM-1", 1, "Nu online"),
            ("ROEPNAAM-2", 1, "Nu online"),
            ("ROEPNAAM-3", 1, "Nu online"),
            
            # --- JOUW OFFLINE GEBRUIKERS (ROOD) ---
            ("ON1ZV - Repeater", 0, "23-09 12:15"),
            ("ON2ACO - Mobiel", 0, "22-09 19:40")
        ]
        
        cursor.execute("DELETE FROM users")
        cursor.executemany("INSERT OR REPLACE INTO users (naam, online, laast_gezien) VALUES (?, ?, ?)", mijn_gebruikers)
        conn.commit()
        print("Jouw eigen gebruikerslijst is succesvol geüpdatet!")
        
    except Exception as e:
        print("Database initialisatie fout:", e)
    finally:
        conn.close()

def haal_gebruikers_uit_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    gebruikers = []
    try:
        cursor.execute("SELECT naam, online, laast_gezien FROM users")
        rows = cursor.fetchall()
        for rij in rows:
            gebruikers.append({
                "naam": str(rij["naam"]),
                "online": bool(rij["online"]),
                "laast_gezien": str(rij["laast_gezien"]) if rij["laast_gezien"] else "-"
            })
    except Exception as e:
        print("Database SELECT fout:", e)
        gebruikers = [{"naam": "Database Fout", "online": False, "laast_gezien": "-"}]
    finally:
        conn.close()
    return gebruikers

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/users':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(haal_gebruikers_uit_db()).encode('utf-8'))
            return
        
        elif self.path in ['/', '/online.html', '/index.html', '/online_met_contact%20(1).html']:
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

controleer_en_vul_database()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait succesvol op poort", PORT)
    httpd.serve_forever()
