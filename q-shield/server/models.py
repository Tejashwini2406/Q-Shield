from sqlalchemy import Column, String, Integer, Float, LargeBinary, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from server.database import Base

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_type = Column(String, nullable=False)
    hardware_profile = Column(String, nullable=False)
    location = Column(JSON, nullable=True)
    pqc_public_key = Column(LargeBinary, nullable=False)
    session_key = Column(LargeBinary, nullable=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String, nullable=False, index=True)
    data = Column(LargeBinary, nullable=False)
    processed = Column(Boolean, default=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())

class SecurityEvent(Base):
    __tablename__ = "security_events"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
