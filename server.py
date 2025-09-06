import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from datetime import datetime, timezone
from pydantic import BaseModel
import json

from security import create_jwt, verify_jwt, decrypt_aes_gcm, encrypt_aes_gcm

app = FastAPI(title="QShield+ Backend", version="1.0.0")
security = HTTPBearer()

#♡ In-memory DB
DEVICES = {}
TELEMETRY = {}

#♡ Pydantic models
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

#♡ Device Registration
@app.post("/register", response_model=RegisterResponse)
def register_device(req: RegisterRequest):
    import secrets
    did = f"did:device:{secrets.token_urlsafe(6)}"
    aes_key = secrets.token_bytes(32)
    DEVICES[did] = {"name": req.device_name, "aes_key": aes_key}
    jwt_token = create_jwt(did)
    return RegisterResponse(did=did, jwt=jwt_token, aes_key=aes_key.hex())

#♡ Telemetry
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
    if data.get("lat") > 80:  # ♡ simple geofence example
        alert_triggered = True

    return TelemetryResponse(status="ok", alert_triggered=alert_triggered)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
