import socket
import json
import threading
import time
import csv
import sys

# Configuración de los tres nodos
NODOS = {
    1: ('localhost', 5000),
    2: ('localhost', 5001),
    3: ('localhost', 5002),
}

class NodoTCP:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.host, self.port = NODOS[node_id]
        self.lamport_clock = 0
        self.lock = threading.Lock()

    # Reloj de Lamport
    def _tick(self) -> int:
        """Incrementa el reloj antes de enviar un mensaje."""
        with self.lock:
            self.lamport_clock += 1
            return self.lamport_clock

    def _update(self, received_ts: int) -> int:
        """Actualiza el reloj al recibir: max(local, received) + 1."""
        with self.lock:
            self.lamport_clock = max(self.lamport_clock, received_ts) + 1
            return self.lamport_clock

    # Servidor (hilo en segundo plano)
    def _handle(self, conn: socket.socket):
        """Maneja una conexión entrante."""
        with conn:
            raw = conn.recv(4096)
            if not raw:
                return
            msg = json.loads(raw.decode())
            new_clock = self._update(msg['timestamp'])
            print(f"[Nodo {self.node_id}] ← {msg['sender']} | "
                  f"msg='{msg['message']}' | Lamport={new_clock}")
            resp = json.dumps({"responder": self.node_id, "timestamp": new_clock})
            conn.sendall(resp.encode())

    def start_server(self):
        """Inicia el servidor TCP en un hilo separado."""
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(16)
        print(f"[Nodo {self.node_id}] Servidor activo en {self.host}:{self.port}")
        while True:
            conn, _ = srv.accept()
            t = threading.Thread(target=self._handle, args=(conn,), daemon=True)
            t.start()

    # Cliente
    def send_to(self, target_id: int, message: str):
        """Envía un mensaje JSON al nodo destino y actualiza el reloj."""
        host, port = NODOS[target_id]
        ts = self._tick()
        payload = json.dumps({
            "sender": self.node_id,
            "timestamp": ts,
            "message": message
        }).encode()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(payload)
            resp = json.loads(s.recv(4096).decode())
            self._update(resp['timestamp'])

    # Lógica principal
    def run_exchanges(self, count: int = 20):
        """Ejecuta <count> intercambios rotando entre los demás nodos."""
        targets = [nid for nid in NODOS if nid != self.node_id]
        print(f"\n[Nodo {self.node_id}] ── {count} INTERCAMBIOS ──")
        for i in range(count):
            target = targets[i % len(targets)]
            self.send_to(target, f"intercambio_{i + 1}")
            print(f"  [{i + 1:>2}/{count}] → Nodo {target} | Lamport={self.lamport_clock}")

    def measure_latency(self, count: int = 100) -> tuple[list[float], float]:
        """Mide la latencia de <count> envíos con time.perf_counter()."""
        target = [nid for nid in NODOS if nid != self.node_id][0]
        latencies: list[float] = []
        print(f"\n[Nodo {self.node_id}] ── {count} ENVÍOS PARA LATENCIA → Nodo {target} ──")

        for i in range(count):
            start = time.perf_counter()
            self.send_to(target, f"latencia_{i + 1}")
            elapsed = (time.perf_counter() - start) * 1000  # ms
            latencies.append(elapsed)

        avg = sum(latencies) / len(latencies)
        print(f"  Latencia promedio: {avg:.4f} ms")
        return latencies, avg

    def save_csv(self, latencies: list[float], avg: float):
        """Guarda los resultados en un archivo CSV."""
        filename = f"resultados_nodo{self.node_id}_tcp.csv"
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["envio", "latencia_ms"])
            for i, lat in enumerate(latencies, 1):
                writer.writerow([i, round(lat, 4)])
            writer.writerow(["PROMEDIO", round(avg, 4)])
        print(f"\n  Resultados guardados en '{filename}'")


# Punto de entrada

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("1", "2", "3"):
        print("Uso: python nodo_tcp.py <1|2|3>")
        sys.exit(1)
    node_id = int(sys.argv[1])
    nodo = NodoTCP(node_id)
    # El servidor corre siempre en segundo plano
    server_thread = threading.Thread(target=nodo.start_server, daemon=True)
    server_thread.start()

    if node_id == 1:
        # Espera a que los otros nodos estén listos
        print("[Nodo 1] Esperando que los nodos 2 y 3 estén listos... (3s)")
        time.sleep(3)
        nodo.run_exchanges(20)
        latencies, avg = nodo.measure_latency(100)
        nodo.save_csv(latencies, avg)
    else:
        # Nodos 2 y 3: solo sirven peticiones
        print(f"[Nodo {node_id}] Listo. Esperando mensajes del Nodo 1...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n[Nodo {node_id}] Detenido.")

if __name__ == "__main__":
    main()