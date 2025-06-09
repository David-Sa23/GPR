import pandas as pd
from scapy.all import sniff, IP
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
import time

# Charger les donn�es �tiquet�es
df = pd.read_csv('captura_real2.csv')
X = df[['packet_size', 'protocol', 'packet_frequency']]
y = df['label']

# Entra�ner le mod�le
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
model = MLPClassifier(hidden_layer_sizes=(10, 5), max_iter=1000, random_state=42)
model.fit(X_scaled, y)

start_time = None  # Pour le calcul de fr�quence

# Fonction de pr�diction en temps r�el
def predict_realtime(packet):
    global start_time
    if packet.haslayer(IP):
        packet_size = len(packet)
        protocol = {6: 1, 17: 2, 1: 3}.get(packet[IP].proto, 3)

        current_time = packet.time
        if start_time is None:
            start_time = current_time
        elapsed = max(current_time - start_time, 0.001)
        frequency = 1 / elapsed
        start_time = current_time

        input_data = pd.DataFrame([[packet_size, protocol, frequency]],
                                  columns=['packet_size', 'protocol', 'packet_frequency'])
        input_scaled = scaler.transform(input_data)
        prediction = model.predict(input_scaled)[0]

        status = "? Anormal" if prediction == 1 else "? Normal"
        message = f"Taille={packet_size}, Protocole={protocol}, Fr�q={frequency:.2f} ? {status}"
        print(message)

        # �criture dans le journal
        with open("logs.txt", "a") as f:
            f.write(message + "\n")

print("? D�marrage de la d�tection en temps r�el (Ctrl+C pour arr�ter)...")
sniff(prn=predict_realtime)
