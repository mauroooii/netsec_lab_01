from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse, parse_qs

notes = {}
next_id = 1

def run():
    server_address = ('', 8080)
    HTTPServer.allow_reuse_address = True
    httpd = HTTPServer(server_address, MiniAPIHandler)
    print("Server avviato e in ascolto sulla porta 8080...")
    httpd.serve_forever()

class MiniAPIHandler(BaseHTTPRequestHandler):

    def invia_json(self, status_code, dati_dizionario):
        corpo_bytes = json.dumps(dati_dizionario).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(corpo_bytes)))
        self.end_headers()
        self.wfile.write(corpo_bytes)

    def do_GET(self):
        indirizzo = urlparse(self.path)
        percorso = indirizzo.path

        if percorso == '/':
            self.send_response(200)
            self.end_headers()

        elif percorso == '/echo':
            parametri = parse_qs(indirizzo.query, keep_blank_values=True)
            if 'msg' in parametri:
                testo_decodificato = parametri['msg'][0]
                self.invia_json(200, {"msg": testo_decodificato})
            else:
                self.send_response(400)
                self.end_headers()

        elif percorso.startswith('/notes/'):
            id_str = percorso[7:]
            if not id_str.isdigit():
                self.send_response(404)
                self.end_headers()
                return

            id_nota = int(id_str)
            if id_nota in notes:
                self.invia_json(200, {"id": id_nota, "text": notes[id_nota]})
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global next_id
        indirizzo = urlparse(self.path)
        percorso = indirizzo.path

        if percorso == '/notes':
            if self.headers.get('Content-Type') != 'application/json':
                self.send_response(415)
                self.end_headers()
                return

            lunghezza = int(self.headers.get('Content-Length', 0))
            corpo_grezzo = self.rfile.read(lunghezza)

            try:
                dati = json.loads(corpo_grezzo.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                return

            if 'text' not in dati or not isinstance(dati['text'], str):
                self.send_response(400)
                self.end_headers()
                return

            id_assegnato = next_id
            notes[id_assegnato] = dati['text']
            next_id += 1

            self.invia_json(201, {"id": id_assegnato})
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        indirizzo = urlparse(self.path)
        percorso = indirizzo.path

        if percorso.startswith('/notes/'):
            id_str = percorso[7:]
            if not id_str.isdigit():
                self.send_response(404)
                self.end_headers()
                return

            id_nota = int(id_str)
            if id_nota in notes:
                del notes[id_nota]
                self.send_response(204)
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        if self.path.startswith('/notes'):
            self.send_response(405)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == '__main__':
    run()


