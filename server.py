import http.server
import socketserver
import json
import sqlite3
import os
from datetime import datetime

PORT = 10000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "poc_radio.db")

# Tijdelijk intern geheugen voor de live chatberichten
chat_berichten = []

def haal_gebruikers_op():
    if not os.path.exists(DB_FILE):
        print(f"Database bestand niet gevonden op locatie: {DB_FILE}")
        return []
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT naam, online, tijd, laast_gezien FROM users")
        rows = cursor.fetchall()
    except Exception as e:
        print("Database SELECT fout:", e)
        rows = []
    conn.close()
    
    gebruikers = []
    for r in rows:
        # Hier worden de kolommen nu gegarandeerd correct uitgelezen via indexnummers
        gebruikers.append({
            "naam": r[0] if len(r) > 0 and r[0] else "Onbekend",
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
            
        # API Route voor de chatbox
        elif self.path == '/api/chat':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(chat_berichten).encode('utf-8'))
        
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
                fout_bericht = f"<h1>Fout: HTML-bestand niet gevonden op locatie: {html_pad}</h1>"
                self.wfile.write(fout_bericht.encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        # Ontvang en bewaar nieuwe chatberichten
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                nieuw_bericht = {
                    "naam": data.get("naam", "Anoniem"),
                    "bericht": data.get("bericht", ""),
                    "tijd": datetime.now().strftime("%H:%M")
                }
                if nieuw_bericht["bericht"].strip():
                    chat_berichten.append(nieuw_bericht)
                
                if len(chat_berichten) > 50:
                    chat_berichten.pop(0)
            except Exception as e:
                print("Chat POST fout:", e)
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait succesvol op poort", PORT)
    httpd.serve_forever()
