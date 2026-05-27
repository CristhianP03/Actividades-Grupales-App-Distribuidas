import grpc
import time
import csv
import sys
import threading
from concurrent import futures
import nodo_pb2
import nodo_pb2_grpc

PUERTOS = {1: 6000, 2: 6001, 3: 6002}

class NodoGRPC(nodo_pb2_grpc.NodoServiceServicer):
    def __init__(self, node_id):
        self.node_id    = node_id
        self.lamport    = 0
        self.lock       = threading.Lock()

    # Reloj de Lamport
    def tick(self):
        with self.lock:
            self.lamport += 1
            return self.lamport

    def update(self, received_ts):
        with self.lock:
            self.lamport = max(self.lamport, received_ts) + 1
            return self.lamport

    # Servidor (método del Servicer)
    def Enviar(self, request, context):
        new_clock = self.update(request.timestamp)
        print(f"[Nodo {self.node_id}] ← {request.sender} | "
              f"msg='{request.message}' | Lamport={new_clock}")
        return nodo_pb2.Respuesta(
            responder=str(self.node_id),
            timestamp=new_clock
        )

    def start_server(self):
        port   = PUERTOS[self.node_id]
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        nodo_pb2_grpc.add_NodoServiceServicer_to_server(self, server)
        server.add_insecure_port(f"[::]:{port}")
        server.start()
        print(f"[Nodo {self.node_id}] Servidor gRPC activo en puerto {port}")
        return server

    # Cliente
    def send_to(self, target_id, message):
        port    = PUERTOS[target_id]
        ts      = self.tick()
        channel = grpc.insecure_channel(f"localhost:{port}")
        stub    = nodo_pb2_grpc.NodoServiceStub(channel)
        msg     = nodo_pb2.Mensaje(
            sender    = f"Nodo{self.node_id}",
            timestamp = ts,
            message   = message
        )
        resp = stub.Enviar(msg)
        self.update(resp.timestamp)
        channel.close()

    # 20 Intercambios
    def run_exchanges(self, count=20):
        targets = sorted(k for k in PUERTOS if k != self.node_id)
        print(f"\n[Nodo {self.node_id}] ── {count} INTERCAMBIOS gRPC ──")
        for i in range(count):
            target = targets[i % len(targets)]
            self.send_to(target, f"intercambio_{i+1}")
            print(f"  [{i+1:>2}/{count}] → Nodo {target} | Lamport={self.lamport}")

    # 100 Envíos para medir latencia
    def measure_latency(self, count=100):
        target    = sorted(k for k in PUERTOS if k != self.node_id)[0]
        latencies = []
        print(f"\n[Nodo {self.node_id}] ── {count} ENVÍOS LATENCIA → Nodo {target} ──")
        for i in range(count):
            start = time.perf_counter()
            self.send_to(target, f"latencia_{i+1}")
            latencies.append((time.perf_counter() - start) * 1000)
        avg = sum(latencies) / len(latencies)
        print(f"  Latencia promedio: {avg:.4f} ms")
        return latencies, avg

    # Guardar CSV
    def save_csv(self, latencies, avg):
        filename = f"resultados_nodo{self.node_id}_grpc.csv"
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["envio", "latencia_ms"])
            for i, lat in enumerate(latencies, 1):
                writer.writerow([i, round(lat, 4)])
            writer.writerow(["PROMEDIO", round(avg, 4)])
        print(f"\n  CSV guardado: {filename}")


# Main
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("1", "2", "3"):
        print("Uso: python nodo_grpc.py <1|2|3>")
        sys.exit(1)

    node_id = int(sys.argv[1])
    nodo    = NodoGRPC(node_id)
    server  = nodo.start_server()

    if node_id == 1:
        print("[Nodo 1] Esperando que nodos 2 y 3 estén listos... (3s)")
        time.sleep(3)
        nodo.run_exchanges(20)
        latencies, avg = nodo.measure_latency(100)
        nodo.save_csv(latencies, avg)
    else:
        print(f"[Nodo {node_id}] Listo. Esperando mensajes...")
        server.wait_for_termination()