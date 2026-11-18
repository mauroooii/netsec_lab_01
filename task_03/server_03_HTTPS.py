import ssl
import json
import uuid
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Memoria globale per le sessioni (Punto 2)
sessioni = {}

# ==========================================
# GESTORE 1: TLS Standard & Sessioni (Porta 8443)
# ==========================================
class TLSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK TLS")

        elif self.path == '/me':
            cookie_header = self.headers.get('Cookie')
            session_valida = False

            if cookie_header:
                for pezzo in cookie_header.split(';'):
                    pezzo = pezzo.strip()
                    if pezzo.startswith('session='):
                        token = pezzo.split('=')[1]
                        if token in sessioni:
                            utente = sessioni[token]
                            self.send_response(200)
                            self.send_header('Content-Type', 'application/json')
                            self.end_headers()
                            corpo_risposta = json.dumps({"user": utente})
                            self.wfile.write(corpo_risposta.encode('utf-8'))
                            session_valida = True
                            break

            if not session_valida:
                self.send_response(401)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/login':
            try:
                lunghezza = int(self.headers.get('Content-Length', 0))
                corpo_ricevuto = self.rfile.read(lunghezza).decode('utf-8')
                dati_json = json.loads(corpo_ricevuto)

                utente = dati_json.get("user")
                password = dati_json.get("password")

                if password == "netsec" and utente:
                    token = str(uuid.uuid4())
                    sessioni[token] = utente
                    self.send_response(200)
                    self.send_header('Set-Cookie', f'session={token}; Secure; HttpOnly')
                    self.end_headers()
                else:
                    self.send_response(401)
                    self.end_headers()
            except Exception:
                self.send_response(401)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


# ==========================================
# GESTORE 2: mTLS Autenticazione con Certificato (Porta 8444)
# ==========================================
class mTLSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # PUNTO 3: Rotta /whoami
        if self.path == '/whoami':
            # Estrazione del certificato che il client ha inviato durante l'handshake
            certificato_client = self.connection.getpeercert()
            common_name = "Unknown"

            # Navigazione dei campi del certificato per trovare il Common Name (CN)
            if certificato_client:
                for rdn in certificato_client.get('subject', []):
                    for chiave, valore in rdn:
                        if chiave == 'commonName':
                            common_name = valore
                            break

            # Invio del CN come testo in chiaro
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(common_name.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


# ==========================================
# FUNZIONI DI AVVIO DEI SERVER
# ==========================================
def avvia_server_tls():
    server = HTTPServer(('0.0.0.0', 8443), TLSHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    server.socket = context.wrap_socket(server.socket, server_side=True)
    print("Server TLS (Porta 8443) in ascolto...")
    server.serve_forever()

def avvia_server_mtls():
    server = HTTPServer(('0.0.0.0', 8444), mTLSHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # 1. Utilizziamo lo stesso certificato del server della porta 8443
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    # 2. Impostiamo il blocco invalicabile mTLS
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(cafile="ca.crt")

    server.socket = context.wrap_socket(server.socket, server_side=True)
    print("Server mTLS (Porta 8444) in ascolto...")
    server.serve_forever()

if __name__ == '__main__':
    HTTPServer.allow_reuse_address = True

    # Creazione dei Thread per far girare i due server in parallelo
    thread1 = threading.Thread(target=avvia_server_tls)
    thread2 = threading.Thread(target=avvia_server_mtls)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
