import socket
import threading

memoria = {} #Deve essere accessibile a tutti

def gestisci_client(client_socket, client_address):
    print("Nuovo client collegato dall'indirizzo: ", client_address)

    buffer = ""

    while True:
        try:
            dati_grezzi = client_socket.recv(1024)
            if not dati_grezzi:
                print("Il client", client_address, "ha chiuso la connessione.")
                break

            buffer += dati_grezzi.decode('ascii')

            while "\n" in buffer:
                riga_corrente, buffer = buffer.split("\n", 1)
                messaggio_pulito = riga_corrente.strip()
                if not messaggio_pulito:
                    continue

                print(f"[{client_address}] ha inviato il comando: {messaggio_pulito}")
                # ECHO function
                if messaggio_pulito.startswith("ECHO "):
                    parti = messaggio_pulito.split(" ", 1)
                    testo_da_ripetere = parti[1]
                    risposta = testo_da_ripetere + "\n"
                    client_socket.sendall(risposta.encode('ascii'))
                # PING function
                elif messaggio_pulito == "PING":
                    risposta = "PONG\n"
                    client_socket.sendall(risposta.encode('ascii'))
                # SET key
                elif messaggio_pulito.startswith("SET "):
                    parti = messaggio_pulito.split(" ", 2)
                    if len(parti) == 3:
                        chiave = parti[1]
                        valore = parti[2]
                        memoria[chiave] = valore
                        risposta = "OK\n"
                    else:
                        risposta = "ERR\n"
                    client_socket.sendall(risposta.encode('ascii'))
                # GET key
                elif messaggio_pulito.startswith("GET "):
                    parti = messaggio_pulito.split(" ", 1)
                    if len(parti) == 2:
                        chiave = parti[1]
                        if chiave in memoria:
                            risposta = memoria[chiave] + "\n"
                        else:
                            risposta = "NOT_FOUND\n"
                    else:
                        risposta = "ERR\n"
                    client_socket.sendall(risposta.encode('ascii'))

                else:
                    risposta = "ERR\n"
                    client_socket.sendall(risposta.encode('ascii'))

        except Exception as e:
            print("Errore di rete con", client_address)
            break

    client_socket.close()

# CONFIGURAZIONE E AVVIO DEL SERVER
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', 9001))
server.listen()

print("Server TCP acceso e in ascolto sulla porta 9001...")

while True:
    print("In attesa...")
    client_socket, client_address = server.accept()

    thread_client = threading.Thread(target=gestisci_client, args=(client_socket, client_address))
    thread_client.start()