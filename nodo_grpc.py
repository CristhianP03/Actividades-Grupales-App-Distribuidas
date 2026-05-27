import grpc
import sys
import threading
from concurrent import futures
import nodo_pb2
import nodo_pb2_grpc

PUERTOS = {1: 6000, 2: 6001, 3: 6002}


class NodoGRPC(nodo_pb2_grpc.NodoServiceServicer):

    def __init__(self, node_id):
        self.node_id = node_id
        self.lamport = 0
        self.lock    = threading.Lock()

    def update(self, received_ts):
        with self.lock:
            self.lamport = max(self.lamport, received_ts) + 1
            return self.lamport

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

if __name__ == "__main__":
    node_id = int(sys.argv[1])
    nodo   = NodoGRPC(node_id)
    server = nodo.start_server()
    print(f"[Nodo {node_id}] Esperando mensajes...")
    server.wait_for_termination()