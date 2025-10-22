import os
import logging
import time
from typing import Dict, Any, Tuple, Optional
from core.hardware_detector import HardwareCapabilities
from core.key_manager import KeyManager
from core.crypto_primitives import CryptoPrimitives
import oqs
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


class PQCManager:
    """Universal Post-Quantum Cryptography Manager"""
    
    def __init__(self, device_profile: str = "auto"):
        self.logger = logging.getLogger(__name__)
        
        try:
            self.hardware_caps = HardwareCapabilities()
            self.device_profile = self._determine_profile(device_profile)
            self.key_manager = KeyManager()
            self.crypto = CryptoPrimitives()
            
            # Initialize with dummy managers for now
            self.kem = DummyKyberManager(self.device_profile)
            self.sig = DummyDilithiumManager(self.device_profile)
            self.symmetric = DummySymmetricManager(self.hardware_caps)
            
            self.logger.info(f"PQCManager initialized with profile: {self.device_profile}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PQCManager: {e}")
            # Initialize with safe defaults
            self.device_profile = "standard"
            self.kem = DummyKyberManager(self.device_profile)
            self.sig = DummyDilithiumManager(self.device_profile)
            self.symmetric = DummySymmetricManager(None)
    
    def _determine_profile(self, profile: str) -> str:
        """Automatically determine device profile based on capabilities"""
        if profile != "auto":
            return profile
            
        try:
            if self.hardware_caps.capabilities.get('has_crypto_acceleration', False):
                print("Profile determined: high_performance")
                return "high_performance"
            elif self.hardware_caps.has_sufficient_memory():
                print("Profile determined: standard")
                return "standard"
            else:
                print("Profile determined: constrained")
                return "constrained"
        except Exception as e:
            print(f"Error determining profile: {e}")
            return "standard"

    def generate_device_keypair(self) -> Tuple[bytes, bytes]:
        """Generate a Post-Quantum keypair (public, private)."""
        return self.kem.generate_keypair()

    def establish_session_key(self, peer_public: bytes) -> Tuple[bytes, bytes]:
        shared_raw, ciphertext = self.kem.encapsulate(peer_public)
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"qshield session",
        )
        shared = hkdf.derive(shared_raw)
        return shared, ciphertext
    
    def encrypt_telemetry(self, data: bytes, session_key: bytes) -> bytes:
        """Encrypt telemetry data using optimal symmetric algorithm"""
        return self.symmetric.encrypt(data, session_key)
    
    def decrypt_telemetry(self, encrypted_data: bytes, session_key: bytes) -> bytes:
        """Decrypt telemetry data"""
        return self.symmetric.decrypt(encrypted_data, session_key)

    def sign(self, data: bytes, private_key: bytes) -> bytes:
        """Sign data using Dilithium."""
        return self.sig.sign(data, private_key)

    def verify(self, data: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify Dilithium signature."""
        return self.sig.verify(data, signature, public_key)

    def sign_data(self, data: bytes, private_key: bytes) -> bytes:
        """Alias to sign() for backward compatibility."""
        return self.sign(data, private_key)

    def verify_signature(self, data: bytes, signature: bytes, public_key: bytes) -> bool:
        """Alias to verify() for backward compatibility."""
        return self.verify(data, signature, public_key)



# Dummy manager classes for testing
class DummyKyberManager:
    def __init__(self, device_profile):
        self.device_profile = device_profile
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        return b"kyber_public_key", b"kyber_private_key"
    
    def encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        return b"shared_secret", b"ciphertext"


class DummyDilithiumManager:
    def __init__(self, device_profile):
        self.device_profile = device_profile
    
    def sign(self, data: bytes, private_key: bytes) -> bytes:
        return b"dilithium_signature"
    
    def verify(self, data: bytes, signature: bytes, public_key: bytes) -> bool:
        return True


class DummySymmetricManager:
    def __init__(self, hardware_caps: Optional[HardwareCapabilities]):
        self.hardware_caps = hardware_caps
    
    def encrypt(self, data: bytes, key: bytes) -> bytes:
        return data  # Dummy encryption
    
    def decrypt(self, encrypted_data: bytes, key: bytes) -> bytes:
        return encrypted_data  # Dummy decryption
