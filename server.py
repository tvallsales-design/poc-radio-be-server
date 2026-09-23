import http.server
import socketserver
import json
import sqlite3
import os

PORT = 10000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "poc_radio.db")

def controleer_en_vul_database():
    """Zorgt ervoor dat de database en tabel altijd bestaan en gevuld zijn met testdata."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Maak de tabel aan als deze nog niet bestaat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                naam TEXT NOT NULL,
                online INTEGER NOT NULL DEFAULT 0,
                laast_gezien TEXT DEFAULT '-'
            )
        ''')
        
        # Controleer of de tabel leeg is
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            print("Database is leeg. We voegen nu automatisch drie voorbeeldradio's toe...")
            test_data = [
                ("ON3OSJ - Handheld", 1, "Nu online"),
                ("ON1ZV - Repeater", 0, "23-09 12:15"),
                ("ON2ACO - Mobiel", 0, "22-09 19:40")
            ]
            cursor.executemany("INSERT INTO users (naam, online, laast_gezien) VALUES (?, ?, ?)", test_data)
            conn.commit()
            print("Voorbeeldradio's succesvol toegevoegd aan de database!")
    except Exception as e:
        print("Fout bij het initialiseren van de database:", e)
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
                "naam": str(rij["naam"]) if rij["naam"] else "Onbekend",
                "online": bool(rij["online"]),
                "laast_gezien": str(rij["laast_gezien"]) if rij["laast_gezien"] else "-"
            })
    except Exception as e:
        print("Database SELECT fout (We proberen een alternatieve kolomnaam):", e)
        try:
            # Fallback voor als de kolom in je eigen database per ongeluk mét een 't' gespeld staat (laatst_gezien)
            cursor.execute("SELECT naam, online, laatst_gezien FROM users")
            rows = cursor.fetchall()
            for rij in rows:
                gebruikers.append({
                    "naam": str(rij["naam"]) if rij["naam"] else "Onbekend",
                    "online": bool(rij["online"]),
                    "laast_gezien": str(rij["laatst_gezien"]) if rij["laatst_gezien"] else "-"
                })
        except Exception as fallback_e:
            print("Beide SQL queries zijn mislukt:", fallback_e)
            gebruikers = [{"naam": "Database Tabel Fout", "online": False, "laast_gezien": "-"}]
    finally:
        conn.close()
        
    return gebruikers

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # API Route voor live gebruikers
        if self.path == '/api/users':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(haal_gebruikers_uit_db()).encode('utf-8'))
            return
        
        # Website hoofdpagina Routes
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

# Voer de database-check uit vóórdat de server opstart
controleer_en_vul_database()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait succesvol op poort", PORT)
    httpd.serve_forever()
