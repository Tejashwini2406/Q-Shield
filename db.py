from sqlalchemy import create_engine, Column, String, DateTime, Boolean, JSON, Integer, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

DATABASE_URL="postgresql://qshield_user:qshield_pass@localhost:5432/qshield"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#♡ Device table
class Device(Base):
    __tablename__ = "devices"
    did = Column(String, primary_key=True, index=True)
    name = Column(String)
    aes_key = Column(String)
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#♡ Telemetry table
class Telemetry(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    did = Column(String)
    data = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#♡ Alert table
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    did = Column(String)
    alert_type = Column(String)
    severity = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#♡ OTA Updates table
class OTAUpdate(Base):
    __tablename__ = "ota_updates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    did = Column(String)
    version = Column(String)
    url = Column(String)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#♡ Init DB
def init_db():
    Base.metadata.create_all(bind=engine)

#♡ Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
