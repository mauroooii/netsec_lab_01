import asyncio, hashlib
from hypercorn.config import Config
from hypercorn.asyncio import serve

async def app(scope, receive, send):
    if scope['type'] == 'http':
        percorso = scope['path']
        metodo = scope['method'] # POST o GET

        if percorso == '/hash' and metodo == 'POST':
            corpo_completo = b""
            aspetta_altri_dati = True

            while aspetta_altri_dati:
                messaggio = await receive()
                if messaggio['type'] == 'http.request':
                    corpo_completo += messaggio.get('body', b"")
                    aspetta_altri_dati = messaggio.get('more_body', False)

            hash_stringa = hashlib.sha256(corpo_completo).hexdigest()
            risposta_bytes = hash_stringa.encode('utf-8')

            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({
                'type': 'http.response.body',
                'body': risposta_bytes
            })

        elif percorso == '/' and metodo == 'GET':
            headers = [(b'alt-svc', b'h3=":4433"')]
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': headers
            })
            await send({
                'type': 'http.response.body',
                'body': b""
            })

        elif percorso == '/proto' and metodo == 'GET':
            versione = scope.get('http_version', '1.1')

            if versione == '3':
                testo_risposta = "HTTP/3"
            elif versione == '2':
                testo_risposta = "HTTP/2"
            else:
                testo_risposta = "HTTP/1.1"

            corpo_bytes = testo_risposta.encode('utf-8')

            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({
                'type': 'http.response.body',
                'body': corpo_bytes
            })

        else:
            await send({
                'type': 'http.response.start',
                'status': 404,
                'headers': []
            })
            await send({
                'type': 'http.response.body',
                'body': b""
            })

# Server configuration
config = Config()
config.bind = ["0.0.0.0:4433"]
config.quic_bind = ["0.0.0.0:4433"]
config.certfile = "server.crt"
config.keyfile = "server.key"

# Server startup
if __name__ == "__main__":
    print("Server HTTPS (TCP) e HTTP/3 (UDP) avviati sulla porta 4433...")
    asyncio.run(serve(app, config))

