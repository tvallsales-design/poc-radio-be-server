import os,json
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse
PORT=int(os.environ.get("PORT","10000"))
radios=[]
class H(SimpleHTTPRequestHandler):
 def do_GET(self):
  p=urlparse(self.path).path
  if p=="/api/public/radios":
   b=json.dumps(radios).encode(); self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(b); return
  if p=="/online": self.path="/online.html"
  if p=="/": self.path="/index.html"
  return super().do_GET()
if __name__=="__main__": ThreadingHTTPServer(("0.0.0.0",PORT),H).serve_forever()
