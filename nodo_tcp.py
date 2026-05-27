import socket
import json
import threading
import sys

NODOS = {
    1: ('localhost', 5000),
    2: ('localhost', 5001),
    3: ('localhost', 5002),
}

class NodoTCP:
    def __init__(self, node_id):
        self.node_id = node_id
        self.host, self.port = NODOS[node_id]

    def _handle(self, conn):
        with conn:
            raw = conn.recv(4096)
            if not raw:
                return
            msg = json.loads(raw.decode())
            print(f"[Nodo {self.node_id}] Recibido de {msg['sender']}: '{msg['message']}'")
            resp = json.dumps({"status": "ok"})
            conn.sendall(resp.encode())

    def start_server(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(16)
        print(f"[Nodo {self.node_id}] Servidor activo en {self.host}:{self.port}")
        while True:
            conn, _ = srv.accept()
            t = threading.Thread(target=self._handle, args=(conn,), daemon=True)
            t.start()

if __name__ == "__main__":
    node_id = int(sys.argv[1])
    nodo = NodoTCP(node_id)
    nodo.start_server()