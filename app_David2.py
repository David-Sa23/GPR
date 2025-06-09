import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report
from scapy.all import sniff, IP
import time

# Variáveis globais para captura
captured_data = []
start_time = None

# Função para processar cada pacote
def process_packet(packet):
    global start_time
    if packet.haslayer(IP):
        packet_size = len(packet)
        protocol_map = {6: 1, 17: 2, 1: 3}  # TCP, UDP, ICMP
        protocol = protocol_map.get(packet[IP].proto, 3)

        current_time = packet.time
        if start_time is None:
            start_time = current_time

        elapsed = max(current_time - start_time, 0.001)
        packet_frequency = 1 / elapsed  # frequência baseada no tempo entre pacotes

        start_time = current_time

        # Guarda os dados capturados
        captured_data.append([packet_size, protocol, packet_frequency])
        print(f"Capturado: Tamanho={packet_size}, Protocolo={protocol}, Freq={packet_frequency:.2f}")

# Captura de pacotes reais (ex: 100 pacotes)
print("A capturar pacotes reais por 30 segundos...")
sniff(timeout=30, prn=process_packet)

# # Guardar em CSV para futura análise/rotulagem manual
# df_real = pd.DataFrame(captured_data, columns=['packet_size', 'protocol', 'packet_frequency'])
# df_real['label'] = 0  # <- INICIALMENTE assume-se tudo como normal
# df_real.to_csv('captura_real2.csv', index=False)
# print("Captura guardada em 'captura_real2.csv'. Por favor, rotula os pacotes (coluna 'label') com 0 ou 1.")

# # Esperar pela rotulagem manual (podes abrir o CSV no Excel e editar a coluna 'label')
# input("Depois de rotulares o ficheiro 'captura_real.csv', pressiona ENTER para continuar...")

# Ler os dados rotulados
df = pd.read_csv('captura_real2.csv')
X = df[['packet_size', 'protocol', 'packet_frequency']]
y = df['label']

# Treinar o modelo
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

mlp = MLPClassifier(hidden_layer_sizes=(10, 5), max_iter=1000, random_state=42)
mlp.fit(X_train, y_train)

# Avaliar
y_pred = mlp.predict(X_test)
print("\n=== Avaliação do Modelo ===")
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Usar o modelo em tempo real (captura contínua)
def predict_realtime(packet):
    if packet.haslayer(IP):
        packet_size = len(packet)
        protocol_map = {6: 1, 17: 2, 1: 3}
        protocol = protocol_map.get(packet[IP].proto, 3)

        global start_time
        current_time = packet.time
        if start_time is None:
            start_time = current_time
        elapsed = max(current_time - start_time, 0.001)
        packet_frequency = 1 / elapsed
        start_time = current_time

        input_data = pd.DataFrame([[packet_size, protocol, packet_frequency]],
                                  columns=['packet_size', 'protocol', 'packet_frequency'])
        input_scaled = scaler.transform(input_data)
        prediction = mlp.predict(input_scaled)[0]
        print(f"➡️  Pacote: Tamanho={packet_size}, Protocolo={protocol}, Freq={packet_frequency:.2f} → "
              f"{'🔴 Anómalo' if prediction == 1 else '🟢 Normal'}")

# Ativa predição em tempo real
print("\nA monitorizar tráfego em tempo real (Ctrl+C para parar)...")
sniff(prn=predict_realtime)
