import http.server
import socketserver
import json
import os
from datetime import datetime

PORT = 10000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Dit zorgt ervoor dat chatberichten WEL netjes in het geheugen bewaard blijven
if 'chat_berichten' not in globals():
    chat_berichten = []

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        # Dit geeft je browser direct toestemming om data te sturen naar de server
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # API Routes
        if self.path == '/api/chat':
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
        # Ontvang en bewaar nieuwe chatberichten feilloos
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
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "berichten": chat_berichten}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait succesvol op poort", PORT)
    httpd.serve_forever()
