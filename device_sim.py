import os
import time
import json
import base64
import random
import threading
import requests
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from security import encrypt_aes_gcm

# ♡ Backend URL
BACKEND_URL = "http://127.0.0.1:8000"

# ♡ Device simulator worker
def simulate_device(device_name):
    priv_pem = f"{device_name}_private.pem"
    pub_pem = f"{device_name}_pub.pem"

    # ♡ Generate RSA key pair if missing
    if not (os.path.exists(priv_pem) and os.path.exists(pub_pem)):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with open(priv_pem, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        public_key = private_key.public_key()
        with open(pub_pem, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        print(f"[{device_name}] Generated key pair: {priv_pem}, {pub_pem}")

    # ♡ Load keys
    with open(priv_pem, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    with open(pub_pem, "r") as f:
        device_pub_pem = f.read()

    # ♡ Register device
    resp = requests.post(
        f"{BACKEND_URL}/register",
        json={"device_name": device_name, "device_pub_pem": device_pub_pem}
    )
    print(f"[{device_name}] Server response:", resp.status_code, resp.text)
    if resp.status_code != 200:
        return

    reg = resp.json()
    did, jwt_token, encrypted_aes_b64 = reg["did"], reg["jwt"], reg["encrypted_aes_key_b64"]

    # ♡ Decrypt AES key
    encrypted_aes_bytes = base64.b64decode(encrypted_aes_b64)
    aes_key = private_key.decrypt(
        encrypted_aes_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    print(f"[{device_name}] Register success. DID: {did}")

    # ♡ MQTT setup
    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        print(f"[{device_name}] Connected to MQTT broker (code {rc})")
        client.subscribe(f"qshield/ota/{did}")

    def on_message(client, userdata, msg):
        payload = json.loads(msg.payload.decode())
        print(f"[{device_name}] OTA Update: {payload}")
        ack = {"did": did, "version": payload["version"]}
        requests.post(f"{BACKEND_URL}/ota_ack", json=ack)
        print(f"[{device_name}] OTA Ack sent for version={payload['version']}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_start()
    print(f"[{device_name}] Listening for OTA on qshield/ota/{did}...")

    # ♡ Telemetry loop
    while True:
        telemetry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current": random.randint(50, 100),
            "pressure": random.randint(980, 1050),
            "temperature": random.randint(20, 30),
            "thermocouple": random.randint(40, 60),
            "voltage": random.randint(980, 1050),
            "lat": random.uniform(0, 100),
            "lon": random.uniform(0, 100),
            "altitude": random.randint(0, 500),
            "edge_score": round(random.random(), 2),
        }
        ciphertext, nonce, tag = encrypt_aes_gcm(aes_key, json.dumps(telemetry))
        payload = {"ciphertext": ciphertext.hex(), "nonce": nonce.hex(), "tag": tag.hex()}
        headers = {"Authorization": f"Bearer {jwt_token}"}
        resp = requests.post(f"{BACKEND_URL}/telemetry", json={"payload": payload}, headers=headers)

        print(f"[{device_name}] Sent telemetry: {telemetry}")
        try:
            print(f"[{device_name}] Backend response:", resp.json())
        except:
            print(f"[{device_name}] Backend response (raw):", resp.text)
        print("-" * 60)
        time.sleep(5)

# ♡ Main launcher
if __name__ == "__main__":
    device_names = ["SensorA", "SensorB", "SensorC"]  # add more here
    threads = []
    for name in device_names:
        t = threading.Thread(target=simulate_device, args=(name,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
