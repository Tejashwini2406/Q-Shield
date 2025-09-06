from sqlalchemy import create_engine, Column, String, LargeBinary, DateTime, Boolean, JSON, Integer, text, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone

#♡ PostgreSQL connection
DATABASE_URL = "postgresql://qshield_user:qshield_pass@localhost:5432/qshield"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#♡ Device table
class Device(Base):
    __tablename__ = "devices"
    did = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    aes_key = Column(LargeBinary, nullable=False)  
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#♡ Telemetry table
class Telemetry(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    did = Column(String, ForeignKey("devices.did"))
    data = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    device = relationship("Device")

#♡ Alert table
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    did = Column(String, ForeignKey("devices.did"))
    alert_type = Column(String)
    severity = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    device = relationship("Device")

#♡ OTA Updates table
class OTAUpdate(Base):
    __tablename__ = "ota_updates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    did = Column(String, ForeignKey("devices.did"))
    version = Column(String)
    url = Column(String)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    device = relationship("Device")

#♡ Event log table
class EventLog(Base):
    __tablename__ = "event_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    did = Column(String, ForeignKey("devices.did"))
    event_type = Column(String, nullable=False)
    details = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    device = relationship("Device")

#♡ Batch log table
class BatchLog(Base):
    __tablename__ = "batch_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    merkle_root = Column(String, nullable=False)
    batch_cid = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

#♡ AI anomaly table
class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    did = Column(String, ForeignKey("devices.did"))
    source = Column(String, nullable=False)
    anomaly_type = Column(String, nullable=False)
    confidence = Column(Integer, nullable=False)
    details = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    device = relationship("Device")

#♡ Initialize all tables
def init_db():
    Base.metadata.create_all(bind=engine)

#♡ DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()