import os
from typing import Dict, Any

class ServerConfig:
    """Configuration for Q-Shield server components"""
    
    # Server Settings
    HOST = os.environ.get("QSHIELD_HOST", "0.0.0.0")
    PORT = int(os.environ.get("QSHIELD_PORT", "8000"))
    DEBUG = os.environ.get("QSHIELD_DEBUG", "False").lower() == "true"
    
    # Database Configuration
    DATABASE_CONFIG = {
        "url": os.environ.get("DATABASE_URL", "sqlite:///qshield.db"),
        "echo": DEBUG,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 3600
    }
    
    # API Configuration
    API_CONFIG = {
        "title": "Q-Shield Universal PQC IoT Platform",
        "description": "Post-Quantum Cryptography enabled IoT telemetry platform",
        "version": "1.0.0",
        "docs_url": "/docs" if DEBUG else None,
        "redoc_url": "/redoc" if DEBUG else None,
        "openapi_url": "/openapi.json" if DEBUG else None
    }
    
    # Security Settings
    SECURITY_CONFIG = {
        "cors_origins": [
            "http://localhost:3000",
            "http://localhost:8080",
            "https://qshield.local"
        ],
        "rate_limit": {
            "registration": "10/minute",
            "telemetry": "1000/minute",
            "api_calls": "100/minute"
        },
        "encryption_mandatory": True,
        "signature_verification": True
    }
    
    # Logging Configuration  
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG" if DEBUG else "INFO",
                "formatter": "detailed",
                "filename": "logs/qshield.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "qshield": {
                "level": "DEBUG" if DEBUG else "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            }
        }
    }
    
    # Performance Monitoring
    PERFORMANCE_CONFIG = {
        "enable_metrics": True,
        "metrics_endpoint": "/metrics",
        "response_time_buckets": [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        "memory_monitoring": True,
        "cpu_monitoring": True
    }
    
    # Anomaly Detection
    ANOMALY_CONFIG = {
        "enabled": True,
        "model_path": "models/",
        "batch_size": 32,
        "detection_threshold": 0.8,
        "update_interval": 3600,  # 1 hour
        "alert_channels": ["email", "webhook", "sms"]
    }
    
    # Geo-fencing
    GEOFENCE_CONFIG = {
        "enabled": True,
        "default_center": {"lat": 12.9716, "lon": 77.5946},  # Bangalore
        "default_radius": 1000,  # meters
        "violation_actions": ["alert", "log", "block"]
    }
    
    # MQTT Configuration (if using MQTT)
    MQTT_CONFIG = {
        "enabled": False,
        "broker_host": os.environ.get("MQTT_HOST", "localhost"),
        "broker_port": int(os.environ.get("MQTT_PORT", "1883")),
        "username": os.environ.get("MQTT_USER", ""),
        "password": os.environ.get("MQTT_PASS", ""),
        "topics": {
            "telemetry": "qshield/telemetry/+",
            "commands": "qshield/commands/+",
            "alerts": "qshield/alerts/+"
        }
    }
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL"""
        return cls.DATABASE_CONFIG["url"]
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return not cls.DEBUG
