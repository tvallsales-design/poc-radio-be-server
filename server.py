import http.server
import socketserver
import json
import os
from datetime import datetime

PORT = 10000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tijdelijk geheugen voor live chatberichten
chat_berichten = []

# Ingebouwde testlijst om te kijken of de verbinding met je dashboard werkt
test_gebruikers = [
    {"naam": "ON3OSJ - Handheld", "online": True, "tijd": "18:30", "laast_gezien": "Nu online"},
    {"naam": "ON1ZV - Repeater", "online": False, "tijd": "12:15", "laast_gezien": "23-09 12:15"},
    {"naam": "ON2ACO - Mobiel", "online": False, "tijd": "Yesterday", "laast_gezien": "22-09 19:40"}
]

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # API Route voor gebruikers
        if self.path == '/api/users':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(test_gebruikers).encode('utf-8'))
            
        # API Route voor de chatbox
        elif self.path == '/api/chat':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(chat_berichten).encode('utf-8'))
        
        # Website hoofdpagina Route
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
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait succesvol op poort", PORT)
    httpd.serve_forever()
