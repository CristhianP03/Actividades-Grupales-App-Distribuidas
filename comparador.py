import csv

class comparador:

    def __init__(self, archivo_csv):
        self.archivo_csv = archivo_csv

    def leer_latencias(self):
        latencias = []
        with open(self.archivo_csv, newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Saltar encabezado
            for fila in reader:
                if fila[0] == "PROMEDIO":
                    continue
                latencias.append(float(fila[1]))
        return latencias

def calcular_promedio(self, latencias):
        return sum(latencias) / len(latencias)

    def calcular_minimo(self, latencias):
        return min(latencias)

    def calcular_maximo(self, latencias):
        return max(latencias)

if __name__ == "__main__":
    tcp  = Comparador("resultados_nodo1_tcp.csv")
    grpc = Comparador("resultados_nodo1_grpc.csv")
    lat_tcp  = tcp.leer_latencias()
    lat_grpc = grpc.leer_latencias()
    print(f"TCP  → {len(lat_tcp)}  mediciones cargadas")
    print(f"gRPC → {len(lat_grpc)} mediciones cargadas")