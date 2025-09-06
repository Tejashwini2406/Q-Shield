import time
import json
import requests
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
import random
from security import encrypt_aes_gcm

#♡ Backend URL
BACKEND_URL = "http://127.0.0.1:8000"

#♡ Device info
DEVICE_NAME = "Sensor A"

#♡ MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(f"qshield/ota/{did}")

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    print(f"[OTA Update Received] {payload}")
    ack = {"did": did, "version": payload["version"]}
    requests.post(f"{BACKEND_URL}/ota_ack", json=ack)
    print(f"OTA Ack sent for version={payload['version']}")

#♡ Register device
register_response = requests.post(f"{BACKEND_URL}/register", json={"device_name": DEVICE_NAME}).json()
did = register_response["did"]
jwt_token = register_response["jwt"]
aes_key = bytes.fromhex(register_response["aes_key"])
print("Register:", register_response)

#♡ MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()
print(f"Listening for OTA updates on qshield/ota/{did}...")

while True:
    telemetry_data = {
        "temperature": random.randint(20, 30),
        "humidity": random.randint(40, 60),
        "pressure": random.randint(980, 1050),
        "battery": random.randint(50, 100),
        "lat": random.uniform(0, 100),
        "lon": random.uniform(0, 100),
        "altitude": random.randint(0, 500),
        "edge_score": round(random.random(), 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    ciphertext, nonce, tag = encrypt_aes_gcm(aes_key, json.dumps(telemetry_data))
    payload = {
        "ciphertext": ciphertext.hex(),
        "nonce": nonce.hex(),
        "tag": tag.hex()
    }
    headers = {"Authorization": f"Bearer {jwt_token}"}
    resp = requests.post(f"{BACKEND_URL}/telemetry", json={"payload": payload}, headers=headers)

    #♡ Print full telemetry + backend response
    print("Sent telemetry:", telemetry_data)
    print("Backend response:", resp.json())
    print("-" * 60)

    time.sleep(5)
