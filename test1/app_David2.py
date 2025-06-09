# app_David2.py
from flask import Flask, render_template, jsonify
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report
from scapy.all import sniff, IP
import threading
import time

app = Flask(__name__)

captured_data = []
start_time = None
latest_prediction = {}

# Função de captura para treino
def process_packet(packet):
    global start_time
    if packet.haslayer(IP):
        packet_size = len(packet)
        protocol_map = {6: 1, 17: 2, 1: 3}
        protocol = protocol_map.get(packet[IP].proto, 3)
        current_time = packet.time
        if start_time is None:
            start_time = current_time
        elapsed = max(current_time - start_time, 0.001)
        packet_frequency = 1 / elapsed
        start_time = current_time
        captured_data.append([packet_size, protocol, packet_frequency])

# Treinar modelo
df = pd.read_csv('captura_real2.csv')
X = df[['packet_size', 'protocol', 'packet_frequency']]
y = df['label']
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
mlp = MLPClassifier(hidden_layer_sizes=(10, 5), max_iter=1000, random_state=42)
mlp.fit(X_train, y_train)

def predict_realtime(packet):
    global start_time, latest_prediction
    if packet.haslayer(IP):
        packet_size = len(packet)
        protocol_map = {6: 1, 17: 2, 1: 3}
        protocol = protocol_map.get(packet[IP].proto, 3)
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
        latest_prediction = {
            "size": packet_size,
            "protocol": protocol,
            "frequency": round(packet_frequency, 2),
            "prediction": int(prediction)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start_sniff():
    thread = threading.Thread(target=lambda: sniff(prn=predict_realtime, store=False))
    thread.daemon = True
    thread.start()
    return jsonify({"status": "sniffing started"})

@app.route('/latest')
def get_latest():
    return jsonify(latest_prediction)

if __name__ == '__main__':
    app.run(debug=True)
