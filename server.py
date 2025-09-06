import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import json
import requests
import logging
from uuid import uuid4
from web3 import Web3
import hashlib
from typing import List
from security import create_jwt, verify_jwt, decrypt_aes_gcm, encrypt_aes_gcm

app = FastAPI(title="QShield+ Backend", version="1.0.0")
security = HTTPBearer()

#♡ Original in-memory DB (do not change) ♡
DEVICES = {}
TELEMETRY = {}

#=== Blockchain and IPFS Setup and Helpers ===
HARDHAT_RPC_URL = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
ADMIN_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

w3 = Web3(Web3.HTTPProvider(HARDHAT_RPC_URL))
admin_account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

try:
    with open("./contracts/artifacts/contracts/DIDRegistry.sol/DIDRegistry.json") as f:
        contract_json = json.load(f)
        contract_abi = contract_json["abi"]
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
except FileNotFoundError:
    logging.warning("Contract ABI file not found. Deploy contracts before running.")
    contract = None

#♡ Original Pydantic models ♡
class RegisterRequest(BaseModel):
    device_name: str

class RegisterResponse(BaseModel):
    did: str
    jwt: str
    aes_key: str

class TelemetryRequest(BaseModel):
    payload: dict

class TelemetryResponse(BaseModel):
    status: str
    alert_triggered: bool = False

class LogEntryIn(BaseModel):
    did: str
    eventType: str
    details: str

class LogBatchIn(BaseModel):
    entries: List[LogEntryIn]

#♡ AI anomaly input model ♡
class AnomalyLogIn(BaseModel):
    did: str
    source: str  # e.g., "edge" or "cloud"
    anomaly_type: str
    confidence: float
    details: str

#=== Merkle Tree Utilities ===
def hash_leaf(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def hash_pair(a: str, b: str) -> str:
    return hashlib.sha256((a + b).encode()).hexdigest()

def build_merkle_root(leaves: List[str]) -> str:
    if len(leaves) == 1:
        return leaves[0]
    if len(leaves) % 2 == 1:
        leaves.append(leaves[-1])
    paired = [hash_pair(leaves[i], leaves[i + 1]) for i in range(0, len(leaves), 2)]
    return build_merkle_root(paired)

#=== Blockchain logging helper functions ===
def log_event_to_blockchain(did_str: str, event_type: str, details: str):
    if not contract:
        logging.error("Smart contract not loaded, cannot log event.")
        return None
    try:
        func = contract.functions.createDID(
            did_str,
            f"{event_type}: {details}",
            admin_account.address
        )
        tx_count = w3.eth.get_transaction_count(admin_account.address)
        gas_estimate = func.estimateGas({'from': admin_account.address})
        tx = func.buildTransaction({
            'from': admin_account.address,
            'nonce': tx_count,
            'gas': int(gas_estimate * 1.2),
            'gasPrice': w3.toWei('1', 'gwei'),
            'chainId': w3.eth.chain_id
        })
        signed_tx = w3.eth.account.sign_transaction(tx, ADMIN_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logging.info(f"Blockchain event logged: {tx_hash.hex()}")
        return tx_hash.hex()
    except Exception as e:
        logging.error(f"Error logging event: {e}")
        return None

#♡ Original device registration endpoint ♡
@app.post("/register", response_model=RegisterResponse)
def register_device(req: RegisterRequest):
    import secrets
    did = f"did:device:{secrets.token_urlsafe(6)}"
    aes_key = secrets.token_bytes(32)
    DEVICES[did] = {"name": req.device_name, "aes_key": aes_key}
    jwt_token = create_jwt(did)
    #=== Log device registration event on blockchain ===
    tx_hash = log_event_to_blockchain(did, "DeviceRegistration", f"Registered device {req.device_name}")
    return RegisterResponse(did=did, jwt=jwt_token, aes_key=aes_key.hex())

#♡ Original telemetry endpoint (with encryption handling) ♡
@app.post("/telemetry", response_model=TelemetryResponse)
def telemetry(req: TelemetryRequest, token=Depends(security)):
    did = verify_jwt(token.credentials)
    if did not in DEVICES:
        raise HTTPException(404, "Device not found")
    aes_key = DEVICES[did]["aes_key"]
    payload = req.payload
    try:
        plaintext = decrypt_aes_gcm(
            aes_key,
            bytes.fromhex(payload["nonce"]),
            bytes.fromhex(payload["ciphertext"]),
            bytes.fromhex(payload["tag"])
        )
        data = json.loads(plaintext)
    except Exception as e:
        raise HTTPException(400, f"Decryption failed: {str(e)}")
    TELEM = TELEMETRY.get(did, [])
    TELEM.append(data)
    TELEMETRY[did] = TELEM
    alert_triggered = False
    if data.get("lat", 0) > 80:
        alert_triggered = True
    return TelemetryResponse(status="ok", alert_triggered=alert_triggered)

#=== Blockchain and IPFS integrated logging of single events ===
@app.post("/log_event")
def log_event(payload: LogEntryIn, token=Depends(security)):
    verify_jwt(token.credentials)
    log_entry = {
        "did": payload.did,
        "eventType": payload.eventType,
        "details": payload.details,
        "timestamp": datetime.utcnow().isoformat()
    }
    files = {"file": ("log.json", json.dumps(log_entry))}
    try:
        resp = requests.post("http://127.0.0.1:5001/api/v0/add", files=files, timeout=5)
        resp.raise_for_status()
        cid = resp.json()["Hash"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IPFS upload failed: {e}")
    tx_hash = log_event_to_blockchain(payload.did, payload.eventType, f"CID:{cid}")
    return {"message": "Event logged", "ipfs_cid": cid, "tx_hash": tx_hash}

#=== Batch event logging using Merkle tree with blockchain proof ===
@app.post("/log_batch")
def log_batch(batch: LogBatchIn, token=Depends(security)):
    verify_jwt(token.credentials)
    json_logs = []
    for entry in batch.entries:
        log_entry = {
            "did": entry.did,
            "eventType": entry.eventType,
            "details": entry.details,
            "timestamp": datetime.utcnow().isoformat()
        }
        json_logs.append(json.dumps(log_entry))
    leaves = [hashlib.sha256(log.encode()).hexdigest() for log in json_logs]
    merkle_root = build_merkle_root(leaves)
    batch_json = json.dumps(batch.dict())
    files = {"file": ("batch_logs.json", batch_json)}
    try:
        resp = requests.post("http://127.0.0.1:5001/api/v0/add", files=files, timeout=10)
        resp.raise_for_status()
        batch_cid = resp.json()["Hash"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IPFS batch upload failed: {e}")
    tx_hash = log_event_to_blockchain("batch", "MerkleRoot", merkle_root)
    return {
        "message": "Batch logged with Merkle root",
        "batch_ipfs_cid": batch_cid,
        "merkle_root": merkle_root,
        "transaction_hash": tx_hash,
    }

#=== AI anomaly logging integrated with blockchain and IPFS ===
@app.post("/log_anomaly")
def log_anomaly(data: AnomalyLogIn, token=Depends(security)):
    verify_jwt(token.credentials)
    log_entry = {
        "did": data.did,
        "source": data.source,
        "anomalyType": data.anomaly_type,
        "confidence": data.confidence,
        "details": data.details,
        "timestamp": datetime.utcnow().isoformat()
    }
    files = {"file": ("anomaly.json", json.dumps(log_entry))}
    try:
        resp = requests.post("http://127.0.0.1:5001/api/v0/add", files=files, timeout=5)
        resp.raise_for_status()
        cid = resp.json()["Hash"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IPFS upload failed: {e}")
    tx_hash = log_event_to_blockchain(data.did, "AIAnomaly", f"CID:{cid}")
    return {"message": "AI anomaly logged successfully", "ipfs_cid": cid, "transaction_hash": tx_hash}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

