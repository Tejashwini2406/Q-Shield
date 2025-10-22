import os
import secrets
import logging
from typing import Tuple, Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from core.hardware_detector import HardwareCapabilities

class SymmetricCryptoManager:
    """Symmetric encryption manager with algorithm selection based on hardware"""
    
    def __init__(self, hardware_caps: Optional[HardwareCapabilities] = None):
        self.logger = logging.getLogger(__name__)
        self.hardware_caps = hardware_caps or HardwareCapabilities()
        
        # Select optimal symmetric cipher
        self.cipher_type = self._select_cipher()
        self._init_cipher()
        
        self.logger.info(f"SymmetricCryptoManager initialized with {self.cipher_type}")
    
    def _select_cipher(self) -> str:
        """Select optimal symmetric cipher based on hardware capabilities"""
        if self.hardware_caps.capabilities.get('aes_ni', False):
            return "aes_gcm"
        elif self.hardware_caps.capabilities.get('has_crypto_acceleration', False):
            return "aes_gcm"
        else:
            return "chacha20_poly1305"
    
    def _init_cipher(self):
        """Initialize cipher instances"""
        try:
            if self.cipher_type == "aes_gcm":
                self.cipher_class = AESGCM
                self.key_size = 32  # 256-bit
                self.nonce_size = 12  # 96-bit
            else:  # chacha20_poly1305
                self.cipher_class = ChaCha20Poly1305
                self.key_size = 32  # 256-bit
                self.nonce_size = 12  # 96-bit
                
            self.logger.info(f"Initialized {self.cipher_type} cipher")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cipher: {e}")
            raise
    
    def generate_key(self) -> bytes:
        """Generate symmetric encryption key"""
        return secrets.token_bytes(self.key_size)
    
    def generate_nonce(self) -> bytes:
        """Generate nonce for encryption"""
        return secrets.token_bytes(self.nonce_size)
    
    def encrypt(self, plaintext: bytes, key: bytes, 
                associated_data: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Encrypt plaintext, returns (ciphertext, nonce)"""
        try:
            if len(key) != self.key_size:
                raise ValueError(f"Invalid key size: {len(key)}, expected {self.key_size}")
            
            cipher = self.cipher_class(key)
            nonce = self.generate_nonce()
            
            ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
            
            self.logger.debug(f"Encrypted {len(plaintext)} bytes using {self.cipher_type}")
            return ciphertext, nonce
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: bytes, key: bytes, nonce: bytes,
                associated_data: Optional[bytes] = None) -> bytes:
        """Decrypt ciphertext"""
        try:
            if len(key) != self.key_size:
                raise ValueError(f"Invalid key size: {len(key)}, expected {self.key_size}")
            
            if len(nonce) != self.nonce_size:
                raise ValueError(f"Invalid nonce size: {len(nonce)}, expected {self.nonce_size}")
            
            cipher = self.cipher_class(key)
            plaintext = cipher.decrypt(nonce, ciphertext, associated_data)
            
            self.logger.debug(f"Decrypted {len(ciphertext)} bytes using {self.cipher_type}")
            return plaintext
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_with_nonce_prepended(self, plaintext: bytes, key: bytes,
                                   associated_data: Optional[bytes] = None) -> bytes:
        """Encrypt and prepend nonce to ciphertext for easy storage/transmission"""
        ciphertext, nonce = self.encrypt(plaintext, key, associated_data)
        return nonce + ciphertext
    
    def decrypt_with_nonce_prepended(self, data: bytes, key: bytes,
                                   associated_data: Optional[bytes] = None) -> bytes:
        """Decrypt data with prepended nonce"""
        if len(data) < self.nonce_size:
            raise ValueError("Data too short to contain nonce")
        
        nonce = data[:self.nonce_size]
        ciphertext = data[self.nonce_size:]
        
        return self.decrypt(ciphertext, key, nonce, associated_data)
    
    def get_cipher_info(self) -> Dict[str, Any]:
        """Get information about current cipher configuration"""
        return {
            "cipher_type": self.cipher_type,
            "key_size": self.key_size,
            "nonce_size": self.nonce_size,
            "hardware_acceleration": self.hardware_caps.capabilities.get('aes_ni', False),
            "authenticated_encryption": True,
            "performance_profile": self.hardware_caps.get_performance_profile()
        }
    
    def benchmark_performance(self, data_size: int = 1024, iterations: int = 100) -> Dict[str, float]:
        """Benchmark encryption/decryption performance"""
        import time
        
        # Generate test data
        test_data = secrets.token_bytes(data_size)
        test_key = self.generate_key()
        
        # Benchmark encryption
        start_time = time.time()
        for _ in range(iterations):
            ciphertext, nonce = self.encrypt(test_data, test_key)
        encrypt_time = time.time() - start_time
        
        # Benchmark decryption
        start_time = time.time()
        for _ in range(iterations):
            decrypted = self.decrypt(ciphertext, test_key, nonce)
        decrypt_time = time.time() - start_time
        
        # Calculate metrics
        total_bytes = data_size * iterations
        encrypt_throughput = total_bytes / encrypt_time / (1024 * 1024)  # MB/s
        decrypt_throughput = total_bytes / decrypt_time / (1024 * 1024)  # MB/s
        
        return {
            "cipher_type": self.cipher_type,
            "data_size_bytes": data_size,
            "iterations": iterations,
            "encrypt_time_seconds": encrypt_time,
            "decrypt_time_seconds": decrypt_time,
            "encrypt_throughput_mbps": round(encrypt_throughput, 2),
            "decrypt_throughput_mbps": round(decrypt_throughput, 2),
            "encrypt_ops_per_second": round(iterations / encrypt_time, 2),
            "decrypt_ops_per_second": round(iterations / decrypt_time, 2)
        }
    
    def derive_key_from_shared_secret(self, shared_secret: bytes, 
                                    salt: bytes = None, 
                                    info: bytes = b"") -> bytes:
        """Derive symmetric key from shared secret using HKDF"""
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes
        
        if salt is None:
            salt = b"\x00" * 32  # Default salt
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=salt,
            info=info
        )
        
        return hkdf.derive(shared_secret)
    
    def constant_time_compare(self, a: bytes, b: bytes) -> bool:
        """Constant-time comparison to prevent timing attacks"""
        import hmac
        return hmac.compare_digest(a, b)
