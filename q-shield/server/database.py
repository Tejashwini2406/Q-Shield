from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.server_config import ServerConfig

Base = declarative_base()
_engine = None
_SessionLocal = None

def init():
    global _engine, _SessionLocal
    url = ServerConfig.get_database_url()
    _engine = create_engine(url, echo=ServerConfig.DEBUG)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    Base.metadata.create_all(bind=_engine)

def get_db():
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
