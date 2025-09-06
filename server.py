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
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64, secrets, os, jwt, hvac
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse
import secrets
from fastapi import Request  
#♡ PostgreSQL DB session and models
from db import SessionLocal, Device, Telemetry, Alert, OTAUpdate, EventLog, BatchLog, AnomalyLog, init_db, get_db

#♡ Initialize database
init_db()
db = SessionLocal()

app = FastAPI(title="QShield+ Backend", version="1.0.0")
#♡ Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded,
    lambda request, exc: JSONResponse({"detail": "Too many requests"}, status_code=429))
security = HTTPBearer()

#♡ Vault client config (replace with HSM/KMS if needed)
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root-token")
vault_client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

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
    device_pub_pem: str  # ♡ PEM from device

class RegisterResponse(BaseModel):
    did: str
    jwt: str
    encrypted_aes_key_b64: str  # ♡ AES encrypted with device public key

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

#♡ Load/generate RSA keypair (Vault-backed)
CURRENT_PRIVATE_KEY_PEM = None
CURRENT_PUBLIC_KEY_PEM = None

def load_jwt_keys_from_vault():
    global CURRENT_PRIVATE_KEY_PEM, CURRENT_PUBLIC_KEY_PEM
    try:
        resp = vault_client.secrets.kv.v2.read_secret_version(
            path="jwt_keys", mount_point="qshield-jwt")
        data = resp["data"]["data"]
        CURRENT_PRIVATE_KEY_PEM = data["private_pem"].encode()
        CURRENT_PUBLIC_KEY_PEM = data["public_pem"].encode()
    except Exception:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        CURRENT_PRIVATE_KEY_PEM = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        CURRENT_PUBLIC_KEY_PEM = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

load_jwt_keys_from_vault()

def create_jwt_rs256(did: str, role: str = "device") -> str:
    payload = {
        "sub": did,
        "role": role,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    }
    return jwt.encode(payload, CURRENT_PRIVATE_KEY_PEM, algorithm="RS256")

def verify_jwt_rs256(token: str) -> dict:
    try:
        return jwt.decode(token, CURRENT_PUBLIC_KEY_PEM, algorithms=["RS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
#♡ Role-based access control
def require_role(required_role: str):
    def checker(token: HTTPAuthorizationCredentials = Depends(security)):
        claims = verify_jwt_rs256(token.credentials)
        role = claims.get("role")
        if role != required_role and role != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return claims
    return checker

#♡ register endpoint
@app.post("/register", response_model=RegisterResponse)
def register_device(req: RegisterRequest):
    try:
        db = next(get_db())
        did = f"did:device:{secrets.token_urlsafe(6)}"
        aes_key = secrets.token_bytes(32)

        # Store device in DB
        device = Device(did=did, name=req.device_name, aes_key=aes_key)
        db.add(device)
        db.commit()
        db.refresh(device)

        # Load device public key
        device_pub = serialization.load_pem_public_key(req.device_pub_pem.encode())

        # Encrypt AES key
        encrypted_aes = device_pub.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        encrypted_aes_b64 = base64.b64encode(encrypted_aes).decode()

        jwt_token = create_jwt_rs256(did)
        return RegisterResponse(did=did, jwt=jwt_token, encrypted_aes_key_b64=encrypted_aes_b64)
    except Exception as e:
        logging.exception("Device registration failed")
        raise HTTPException(status_code=500, detail=f"Device registration failed: {str(e)}")

#♡ telemetry endpoint
@app.post("/telemetry", response_model=TelemetryResponse)
def telemetry(req: TelemetryRequest, token=Depends(security)):
    #♡ Verify JWT and extract DID
    try:
        claims = verify_jwt_rs256(token.credentials)
        did = claims["sub"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    db = next(get_db())
    device = db.query(Device).filter(Device.did == did).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    aes_key = device.aes_key

    payload = req.payload
    #♡ Decrypt telemetry
    try:
        plaintext = decrypt_aes_gcm(
            aes_key,
            bytes.fromhex(payload["nonce"]),
            bytes.fromhex(payload["ciphertext"]),
            bytes.fromhex(payload["tag"])
        )
        data = json.loads(plaintext)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")

    #♡ Store telemetry in DB
    telemetry_entry = Telemetry(did=did, data=data)
    db.add(telemetry_entry)

    #♡ Example alert: if latitude > 80
    alert_triggered = False
    if data.get("lat", 0) > 80:
        alert = Alert(did=did, alert_type="LatitudeThreshold", severity="Medium")
        db.add(alert)
        alert_triggered = True

    db.commit()
    return TelemetryResponse(status="ok", alert_triggered=alert_triggered)

#=== Blockchain and IPFS integrated logging of single events ===
@app.post("/log_event")
def log_event(payload: LogEntryIn, token=Depends(security)):
    verify_jwt(token.credentials)
    db = next(get_db())

    log_entry_db = EventLog(
        did=payload.did,
        event_type=payload.eventType,
        details=payload.details
    )
    db.add(log_entry_db)
    db.commit()

    #♡ Upload to IPFS & blockchain as before
    files = {"file": ("log.json", json.dumps(payload.dict()))}
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
    db = next(get_db())

    anomaly_entry = AnomalyLog(
        did=data.did,
        source=data.source,
        anomaly_type=data.anomaly_type,
        confidence=data.confidence,
        details=data.details
    )
    db.add(anomaly_entry)
    db.commit()

    #♡ Upload to IPFS & blockchain as before
    files = {"file": ("anomaly.json", json.dumps(data.dict()))}
    try:
        resp = requests.post("http://127.0.0.1:5001/api/v0/add", files=files, timeout=5)
        resp.raise_for_status()
        cid = resp.json()["Hash"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IPFS upload failed: {e}")

    tx_hash = log_event_to_blockchain(data.did, "AIAnomaly", f"CID:{cid}")
    return {"message": "AI anomaly logged successfully", "ipfs_cid": cid, "transaction_hash": tx_hash}

#♡ Sanitize exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse({"detail": exc.detail if isinstance(exc.detail, str) else "Error"},
                        status_code=exc.status_code)

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    logging.exception("Internal server error")
    return JSONResponse({"detail": "Internal server error"}, status_code=500)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

