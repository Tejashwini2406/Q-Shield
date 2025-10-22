import uvicorn
import logging
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
from server.database import init, get_db
from server.models import Device, TelemetryLog
from config.server_config import ServerConfig
from core.pqc_manager import PQCManager
from server.audit_logger import setup_audit_logger

# Initialize database and audit logger
init()
audit_logger = setup_audit_logger()

app = FastAPI(**ServerConfig.API_CONFIG)
pqc_manager = PQCManager()
logger = logging.getLogger("qshield")

class DeviceRegistrationRequest(BaseModel):
    device_type: str
    hardware_profile: str
    location: Optional[Dict[str, float]] = None
    public_key: str

class TelemetryData(BaseModel):
    device_id: str
    encrypted_payload: str
    signature: str
    timestamp: float

def verify_jwt_token(token: Optional[str]) -> str:
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    # Dummy verification; replace with real JWTAuthenticator logic
    return token.split()[1]

async def run_anomaly_detection(device_id: str, data: bytes):
    logger.debug(f"Anomaly detection stub for {device_id}")

async def check_geofence_violations(device_id: str, data: bytes):
    logger.debug(f"Geofence check stub for {device_id}")

@app.post("/api/v1/register")
async def register_device(req: DeviceRegistrationRequest, db=Depends(get_db)):
    try:
        # Store device
        device = Device(
            id=None,
            device_type=req.device_type,
            hardware_profile=req.hardware_profile,
            location=req.location,
            pqc_public_key=bytes.fromhex(req.public_key)
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        audit_logger.info(f"Registered device {device.id}")
        return {"device_id": device.id}
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/v1/telemetry")
async def receive_telemetry(data: TelemetryData, authorization: Optional[str]=Header(None), db=Depends(get_db)):
    device_id = verify_jwt_token(authorization)
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    payload = bytes.fromhex(data.encrypted_payload)
    sig = bytes.fromhex(data.signature)
    # Decrypt & verify
    pt = pqc_manager.decrypt_telemetry(payload, device.session_key or b"")
    if not pqc_manager.verify_signature(pt, sig, device.pqc_public_key):
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Log and process
    log = TelemetryLog(device_id=device_id, data=pt, processed=False)
    db.add(log)
    db.commit()
    await run_anomaly_detection(device_id, pt)
    await check_geofence_violations(device_id, pt)
    log.processed = True
    db.commit()

    audit_logger.info(f"Telemetry received from {device_id}")
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run("server.server:app", host=ServerConfig.HOST, port=ServerConfig.PORT, log_level="info")
