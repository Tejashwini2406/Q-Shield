import os
import hashlib
import hmac
import secrets
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

class CryptoPrimitives:
    """Low-level cryptographic primitives"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_random_bytes(self, length: int) -> bytes:
        """Generate cryptographically secure random bytes"""
        return secrets.token_bytes(length)
    
    def generate_salt(self, length: int = 16) -> bytes:
        """Generate cryptographic salt"""
        return self.generate_random_bytes(length)
    
    def generate_nonce(self, length: int = 12) -> bytes:
        """Generate nonce for AEAD encryption"""
        return self.generate_random_bytes(length)
    
    # Hash functions
    def sha256(self, data: bytes) -> bytes:
        """SHA-256 hash"""
        return hashlib.sha256(data).digest()
    
    def sha512(self, data: bytes) -> bytes:
        """SHA-512 hash"""
        return hashlib.sha512(data).digest()
    
    def blake2b(self, data: bytes, digest_size: int = 64) -> bytes:
        """BLAKE2b hash"""
        return hashlib.blake2b(data, digest_size=digest_size).digest()
    
    def blake2s(self, data: bytes, digest_size: int = 32) -> bytes:
        """BLAKE2s hash"""
        return hashlib.blake2s(data, digest_size=digest_size).digest()
    
    # HMAC functions
    def hmac_sha256(self, key: bytes, data: bytes) -> bytes:
        """HMAC-SHA256"""
        return hmac.new(key, data, hashlib.sha256).digest()
    
    def hmac_sha512(self, key: bytes, data: bytes) -> bytes:
        """HMAC-SHA512"""
        return hmac.new(key, data, hashlib.sha512).digest()
    
    def verify_hmac(self, key: bytes, data: bytes, signature: bytes, hash_func=hashlib.sha256) -> bool:
        """Verify HMAC signature"""
        try:
            expected = hmac.new(key, data, hash_func).digest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            self.logger.error(f"HMAC verification failed: {e}")
            return False
    
    # Key derivation
    def pbkdf2_derive_key(self, password: bytes, salt: bytes, iterations: int = 100000, 
                         key_length: int = 32, hash_algorithm=hashes.SHA256()) -> bytes:
        """Derive key using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hash_algorithm,
            length=key_length,
            salt=salt,
            iterations=iterations
        )
        return kdf.derive(password)
    
    # Symmetric encryption with AES-GCM
    def aes_gcm_encrypt(self, plaintext: bytes, key: bytes, 
                       associated_data: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Encrypt with AES-GCM, returns (ciphertext, nonce)"""
        try:
            aesgcm = AESGCM(key)
            nonce = self.generate_nonce(12)  # 96-bit nonce for GCM
            ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
            return ciphertext, nonce
        except Exception as e:
            self.logger.error(f"AES-GCM encryption failed: {e}")
            raise
    
    def aes_gcm_decrypt(self, ciphertext: bytes, key: bytes, nonce: bytes,
                       associated_data: Optional[bytes] = None) -> bytes:
        """Decrypt with AES-GCM"""
        try:
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)
            return plaintext
        except Exception as e:
            self.logger.error(f"AES-GCM decryption failed: {e}")
            raise
    
    # Symmetric encryption with ChaCha20-Poly1305
    def chacha20_poly1305_encrypt(self, plaintext: bytes, key: bytes,
                                 associated_data: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Encrypt with ChaCha20-Poly1305, returns (ciphertext, nonce)"""
        try:
            chacha = ChaCha20Poly1305(key)
            nonce = self.generate_nonce(12)  # 96-bit nonce
            ciphertext = chacha.encrypt(nonce, plaintext, associated_data)
            return ciphertext, nonce
        except Exception as e:
            self.logger.error(f"ChaCha20-Poly1305 encryption failed: {e}")
            raise
    
    def chacha20_poly1305_decrypt(self, ciphertext: bytes, key: bytes, nonce: bytes,
                                 associated_data: Optional[bytes] = None) -> bytes:
        """Decrypt with ChaCha20-Poly1305"""
        try:
            chacha = ChaCha20Poly1305(key)
            plaintext = chacha.decrypt(nonce, ciphertext, associated_data)
            return plaintext
        except Exception as e:
            self.logger.error(f"ChaCha20-Poly1305 decryption failed: {e}")
            raise
    
    # Constant-time comparison
    def constant_time_compare(self, a: bytes, b: bytes) -> bool:
        """Constant-time comparison to prevent timing attacks"""
        return hmac.compare_digest(a, b)
    
    # Secure random number generation
    def secure_random_int(self, min_val: int, max_val: int) -> int:
        """Generate cryptographically secure random integer"""
        return secrets.randbelow(max_val - min_val + 1) + min_val
    
    def secure_random_choice(self, sequence):
        """Cryptographically secure random choice"""
        return secrets.choice(sequence)
    
    # Key stretching
    def stretch_key(self, key: bytes, target_length: int, info: bytes = b"") -> bytes:
        """Stretch key to target length using HKDF-like approach"""
        if len(key) >= target_length:
            return key[:target_length]
        
        stretched = key
        counter = 0
        
        while len(stretched) < target_length:
            counter += 1
            stretched += self.sha256(key + counter.to_bytes(4, 'big') + info)
        
        return stretched[:target_length]
    
    # Zero memory (for sensitive data cleanup)
    def zero_memory(self, data: bytearray):
        """Securely zero memory containing sensitive data"""
        for i in range(len(data)):
            data[i] = 0
    
    def create_secure_buffer(self, size: int) -> bytearray:
        """Create a secure buffer that can be zeroed"""
        return bytearray(size)
