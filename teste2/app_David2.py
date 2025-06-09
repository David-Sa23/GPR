from flask import Flask, render_template, jsonify
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report
from scapy.all import sniff, IP, Ether
from mac_vendor_lookup import MacLookup
import threading

app = Flask(__name__)

captured_data = []
start_time = None
latest_predictions = []
sniffing = False

# Setup vendor lookup
mac_lookup = MacLookup()
try:
    mac_lookup.update_vendors()
except Exception:
    pass

def get_vendor(mac):
    try:
        return mac_lookup.lookup(mac)
    except Exception:
        return "Desconhecido"

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
    global start_time, latest_predictions, sniffing
    if not sniffing:
        return
    if packet.haslayer(IP) and packet.haslayer(Ether):
        packet_size = len(packet)
        proto_map = {6: 1, 17: 2, 1: 3}
        protocol = proto_map.get(packet[IP].proto, 3)
        current_time = packet.time
        if start_time is None:
            start_time = current_time
        elapsed = max(current_time - start_time, 0.001)
        freq = 1 / elapsed
        start_time = current_time

        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        src_mac = packet[Ether].src
        dst_mac = packet[Ether].dst

        src_vendor = get_vendor(src_mac)
        dst_vendor = get_vendor(dst_mac)

        input_data = pd.DataFrame([[packet_size, protocol, freq]],
                                  columns=['packet_size', 'protocol', 'packet_frequency'])
        input_scaled = scaler.transform(input_data)
        pred = int(mlp.predict(input_scaled)[0])

        latest_predictions.append({
            "src": f"{src_ip} ({src_vendor})",
            "dst": f"{dst_ip} ({dst_vendor})",
            "size": packet_size,
            "protocol": protocol,
            "frequency": round(freq, 2),
            "prediction": pred
        })

        latest_predictions[:] = latest_predictions[-100:]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start_sniff():
    global sniffing
    sniffing = True
    thread = threading.Thread(target=lambda: sniff(prn=predict_realtime, store=False))
    thread.daemon = True
    thread.start()
    return jsonify({"status": "sniffing started"})

@app.route('/stop')
def stop_sniff():
    global sniffing
    sniffing = False
    return jsonify({"status": "sniffing stopped"})

@app.route('/latest')
def get_latest():
    return jsonify(latest_predictions)

@app.route('/metrics')
def get_metrics():
    report = classification_report(y_test, mlp.predict(X_test), output_dict=True)
    return jsonify({
        "accuracy": round(report["accuracy"] * 100, 2),
        "precision": round(report["1"]["precision"] * 100, 2),
        "recall": round(report["1"]["recall"] * 100, 2),
        "f1": round(report["1"]["f1-score"] * 100, 2)
    })

if __name__ == '__main__':
    app.run(debug=True)
