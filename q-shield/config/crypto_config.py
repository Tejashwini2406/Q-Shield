import os
from typing import Dict, Any

class CryptoConfig:
    """Configuration for cryptographic operations"""
    
    # PQC Algorithm Selection
    KYBER_VARIANT = "kyber512"
    DILITHIUM_VARIANT = "dilithium2"
    
    # Symmetric Encryption Preferences
    AES_KEY_SIZE = 256
    CHACHA20_POLY1305_KEY_SIZE = 32
    
    # Hardware Acceleration Settings
    USE_HARDWARE_ACCELERATION = True
    FALLBACK_TO_SOFTWARE = True
    
    # Key Management
    KEY_ROTATION_INTERVAL = 3600  # 1 hour in seconds
    SESSION_KEY_LIFETIME = 1800   # 30 minutes in seconds
    
    # Security Levels
    SECURITY_PROFILES = {
        "high_performance": {
            "kyber": "kyber512",
            "dilithium": "dilithium2",
            "symmetric": "aes_gcm",
            "use_hardware": True
        },
        "standard": {
            "kyber": "kyber512",
            "dilithium": "dilithium2", 
            "symmetric": "chacha20_poly1305",
            "use_hardware": False
        },
        "constrained": {
            "kyber": "kyber512_compact",
            "dilithium": "dilithium2_compact",
            "symmetric": "chacha20_poly1305",
            "use_hardware": False
        }
    }
    
    # JWT Configuration
    JWT_SECRET = os.environ.get("JWT_SECRET", "qshield_jwt_secret_key")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_MINUTES = 60
    
    # PQC Library Settings
    OQS_ENABLED = True
    LIBOQS_PATH = os.environ.get("LIBOQS_PATH", "/usr/local/lib")
    
    @classmethod
    def get_profile_config(cls, profile: str) -> Dict[str, Any]:
        """Get configuration for specific security profile"""
        return cls.SECURITY_PROFILES.get(profile, cls.SECURITY_PROFILES["standard"])
    
    @classmethod
    def is_hardware_available(cls) -> bool:
        """Check if hardware acceleration is available"""
        # This would be implemented with actual hardware detection
        return cls.USE_HARDWARE_ACCELERATION
