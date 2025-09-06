from pydantic import BaseModel

#♡ Register
class RegisterRequest(BaseModel):
    device_name: str

class RegisterResponse(BaseModel):
    did: str
    jwt: str

#♡ Telemetry
class TelemetryRequest(BaseModel):
    payload: str

class TelemetryResponse(BaseModel):
    status: str
    alert_triggered: bool = False

#♡ OTA Update
class OTAUpdateRequest(BaseModel):
    did: str
    version: str
    url: str

class OTAAckRequest(BaseModel):
    did: str
    version: str

#♡ Metrics
class MetricsResponse(BaseModel):
    cpu: float
    memory: float
    db_count: int
