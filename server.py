import http.server
import socketserver
import json
import os
from datetime import datetime
from urllib.parse import parse_qs

PORT = 10000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if 'chat_berichten' not in globals():
    chat_berichten = []

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/chat':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(chat_berichten).encode('utf-8'))
            return
        
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
                # Verwerk zowel JSON als normale webformulieren feilloos
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

            # Stuur de gebruiker direct en veilig terug naar de hoofdpagina (automatische verversing)
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
            return

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print("Server draait succesvol op poort", PORT)
    httpd.serve_forever()
