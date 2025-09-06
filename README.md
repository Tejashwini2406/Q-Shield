# **Q-Shield+**

### **A Quantum-Resistant Cybersecurity Framework for Smart City IoT**

Q-Shield+ is a quantum-resistant cybersecurity framework for smart city IoT devices, designed to protect against next-generation threats like quantum decryption, spoofing, and AI-driven attacks. The system uses Kyber-based post-quantum cryptography for secure device-to-server communication, DID \+ JWT authentication for decentralized trust, and AES-GCM for encrypted telemetry. Real-time telemetry is analyzed by an edge anomaly detector (fast response) and a cloud-based LSTM model (slow, coordinated attack detection). Security is further enhanced with geo-fencing enforcement (devices restricted to allowed zones), blockchain-based logging for tamper-proof audits, and secure OTA updates with key rotation. A central dashboard allows operators to monitor live telemetry, alerts, and device compliance, making Q-Shield+ a future-proof IoT security solution for smart cities.

## **Table of Contents**

1. [Overview](https://www.google.com/search?q=%23overview)  
2. [Core Features](https://www.google.com/search?q=%23core-features)  
3. [System Architecture](https://www.google.com/search?q=%23system-architecture)  
4. [Technology Stack](https://www.google.com/search?q=%23technology-stack)  
5. [Project Structure](https://www.google.com/search?q=%23project-structure)  
6. [Setup and Installation](https://www.google.com/search?q=%23setup-and-installation)  
7. [Running the System](https://www.google.com/search?q=%23running-the-system)  
8. [API Endpoints](https://www.google.com/search?q=%23api-endpoints)

## **Overview**

The advent of quantum computing poses a significant threat to classical cryptographic standards, rendering current security measures for critical infrastructure, like smart cities, vulnerable. Simultaneously, the increasing sophistication of AI-driven cyberattacks requires a more intelligent and dynamic defense mechanism.

Q-Shield+ addresses these challenges by creating a multi-layered, defense-in-depth security framework. It hardens the entire IoT lifecycle from device registration to data transmission and analysis, ensuring integrity, confidentiality, and resilience against both classical and quantum adversaries.

## **Core Features**

* **Post-Quantum Cryptography (PQC):** Implements **Kyber**, a NIST-selected quantum-resistant algorithm, for key exchange, ensuring that secure communication channels remain confidential even against future quantum computers.  
* **Decentralized Identity (DID) & JWT:** Each device is assigned a unique DID, registered on a private blockchain. Authentication is managed through short-lived JWTs, preventing traditional spoofing and replay attacks.  
* **Two-Stage AI Anomaly Detection:**  
  * **Edge Detector:** A lightweight Isolation Forest model (edge\_detector.py) runs on the server for immediate, real-time analysis of every telemetry packet. It provides a rapid first line of defense.  
  * **Cloud Detector:** A more powerful LSTM Autoencoder model (cloud\_detector.py) is triggered for deeper analysis of data sequences when the edge model flags a potential threat. This allows for the detection of slow, coordinated, and complex attacks.  
* **Blockchain-Immutable Ledger:** All critical events, such as device registrations, high-severity alerts, and OTA updates, are logged as transactions on a private Ethereum blockchain, creating a tamper-proof, auditable trail.  
* **End-to-End Encrypted Telemetry:** Device data is encrypted at the source using AES-GCM, with symmetric keys securely exchanged using PQC, ensuring data confidentiality in transit.  
* **Geo-Fencing Enforcement:** The system can be configured to trigger alerts if a device reports telemetry from outside a predefined geographical boundary.

## **System Architecture**

The Q-Shield+ framework operates on a multi-tier model that is both efficient and robust.

1. **Device Layer:** An IoT device (simulated by device\_simulator.py) securely registers with the backend, receives a DID and cryptographic keys, and begins sending encrypted telemetry.  
2. **Backend Server (Fast Lane):** The FastAPI server (server.py) receives the encrypted data. For every packet, it performs:  
   * Authentication and Decryption.  
   * **Edge AI Analysis:** The telemetry is immediately scored by the EdgeAnomalyDetector.  
3. **Backend Server (Slow Lane):**  
   * The server maintains a short-term history of telemetry for each device.  
   * If the Edge Detector reports a 'medium' or 'high' severity anomaly, the server triggers the **Cloud AI Analysis**.  
   * The CloudAnomalyDetector analyzes the full sequence of recent data points to confirm the threat and identify complex patterns.  
4. **Persistence & Logging:**  
   * All telemetry data is stored in a PostgreSQL database.  
   * Confirmed high-severity anomalies and critical system events are logged to the blockchain for immutability.  
5. **Monitoring & Management Layer:**  
   * A **React-based central dashboard** allows operators to view live device data, monitor AI-driven alerts, and manage device compliance in real-time.

## **Technology Stack**

| Category | Technology / Library |
| :---- | :---- |
| **Frontend** | **React, Tailwind CSS** |
| **Backend** | FastAPI, Uvicorn, SQLAlchemy |
| **AI / Machine Learning** | TensorFlow (Keras), Scikit-learn, Pandas, NumPy |
| **Blockchain** | Web3.py, Hardhat (for local development), Solidity |
| **Database** | PostgreSQL |
| **Security & Crypto** | PyJWT, Cryptography (for AES/RSA), hvac (for HashiCorp Vault), PQC (Kyber) |
| **API & Validation** | Pydantic, SlowAPI (for rate limiting) |

## **Project Structure**

q-shield-plus/  
│  
├── frontend/                \# React dashboard application  
│  
├── contracts/  
│   ├── artifacts/  
│   └── DIDRegistry.sol        \# Smart contract for device identity  
│  
├── models/  
│   ├── saved\_models/  
│   │   ├── isolation\_forest\_model.pkl  
│   │   ├── lstm\_autoencoder.h5  
│   │   └── scaler.joblib  
│   ├── cloud\_detector.py      \# Module for the LSTM Autoencoder  
│   ├── edge\_detector.py       \# Module for the Isolation Forest model  
│   └── train\_lstm\_cloud.py    \# Training script for the cloud model  
│  
├── data/  
│   └── anomaly-free.csv       \# Sample data for training  
│  
├── server.py                \# Main FastAPI backend application  
├── device\_simulator.py      \# Simulates an IoT device sending data  
├── db.py                    \# Database session and model definitions  
├── security.py              \# Helper functions for crypto and JWT  
├── README.md                \# This file  
└── requirements.txt         \# Python dependencies

## **Setup and Installation**

### **Prerequisites**

* Python 3.10+  
* PostgreSQL Server  
* Node.js & npm (for Hardhat and React)  
* Docker (optional, for running dependencies)

### **Installation Steps**

1. **Clone the repository:**  
   git clone https://github.com/Tejashwini2406/Q-Shield.git  
   cd q-shield-plus

2. **Set up the Backend:**  
   \# Set up a Python virtual environment  
   python \-m venv .venv  
   source .venv/bin/activate  \# On Windows: .venv\\Scripts\\activate

   \# Install Python dependencies  
   pip install \-r requirements.txt

3. **Set up the Blockchain Environment:**  
   cd contracts  
   npm install  
   npx hardhat node  \# This starts a local Hardhat blockchain node

4. **Deploy the Smart Contract (in a new terminal):**  
   cd contracts  
   npx hardhat run scripts/deploy.js \--network localhost

   *Note: Ensure the deployed contract address in server.py matches the output.*  
5. **Set up the Frontend:**  
   cd frontend  
   npm install

6. Configure Environment Variables:  
   Create a .env file in the root directory for backend secrets and a .env.local in the frontend directory for frontend configurations.

## **Running the System**

Run each component in a separate terminal, in the following order:

1. **Start the Blockchain:** (If not already running from setup)  
   cd contracts  
   npx hardhat node

2. **Start the Q-Shield+ Server:**  
   \# Ensure you are in the project root with the virtual environment active  
   uvicorn server:app \--host 0.0.0.0 \--port 8000 \--reload

3. **Start the Frontend Dashboard:**  
   cd frontend  
   npm start

4. **Run the Device Simulator:**  
   \# Ensure you are in the project root with the virtual environment active  
   python device\_simulator.py

   You will see the simulator sending data, and you can monitor the results on the live dashboard.

## **API Endpoints**

* POST /register: Registers a new device and returns its DID, JWT, and an encrypted AES key.  
* POST /telemetry: The main endpoint for devices to send encrypted telemetry data. It performs the two-stage AI analysis and returns the results.  
* POST /log\_anomaly: An endpoint for explicitly logging detected anomalies to the database and blockchain.  
* POST /log\_batch: Logs a batch of events to IPFS and anchors its Merkle root on the blockchain.
