import csv

class Comparador:

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

    prom_tcp  = tcp.calcular_promedio(lat_tcp)
    prom_grpc = grpc.calcular_promedio(lat_grpc)
    min_tcp   = tcp.calcular_minimo(lat_tcp)
    min_grpc  = grpc.calcular_minimo(lat_grpc)
    max_tcp   = tcp.calcular_maximo(lat_tcp)
    max_grpc  = grpc.calcular_maximo(lat_grpc)

    print("==============================================")
    print("     COMPARACION TCP vs gRPC — LATENCIA      ")
    print("==============================================")
    print(f"{'Protocolo':<12} {'Promedio':>10} {'Minimo':>10} {'Maximo':>10}")
    print("----------------------------------------------")
    print(f"{'TCP':<12} {prom_tcp:>10.4f} {min_tcp:>10.4f} {max_tcp:>10.4f}")
    print(f"{'gRPC':<12} {prom_grpc:>10.4f} {min_grpc:>10.4f} {max_grpc:>10.4f}")
    print("==============================================")
    ganador = "TCP" if prom_tcp < prom_grpc else "gRPC"
    print(f"  Protocolo mas rapido: {ganador}")
    print("==============================================")