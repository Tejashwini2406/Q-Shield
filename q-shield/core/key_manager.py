import os
import secrets
import hashlib
from typing import Dict, Tuple, Optional, Any
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.hashes import SHA256
import logging
import time

class KeyManager:
    """Secure key storage and management for PQC keys"""
    
    def __init__(self, storage_path: str = "keys/"):
        self.storage_path = storage_path
        self.logger = logging.getLogger(__name__)
        self._ensure_storage_directory()
        self._key_cache = {}
    
    def _ensure_storage_directory(self):
        """Ensure key storage directory exists"""
        os.makedirs(self.storage_path, exist_ok=True)
        # Set restrictive permissions on key directory
        try:
            os.chmod(self.storage_path, 0o700)
        except OSError:
            self.logger.warning("Could not set restrictive permissions on key directory")
    
    def generate_session_key(self, key_size: int = 32) -> bytes:
        """Generate cryptographically secure session key"""
        return secrets.token_bytes(key_size)
    
    def derive_key(self, shared_secret: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
        """Derive key using HKDF"""
        hkdf = HKDF(
            algorithm=SHA256(),
            length=length,
            salt=salt,
            info=info
        )
        return hkdf.derive(shared_secret)
    
    def store_keypair(self, device_id: str, public_key: bytes, private_key: bytes, 
                     algorithm: str = "kyber512") -> bool:
        """Store key pair securely"""
        try:
            # Create device-specific directory
            device_dir = os.path.join(self.storage_path, device_id)
            os.makedirs(device_dir, exist_ok=True)
            os.chmod(device_dir, 0o700)
            
            # Store public key
            pub_path = os.path.join(device_dir, f"{algorithm}_public.key")
            with open(pub_path, 'wb') as f:
                f.write(public_key)
            os.chmod(pub_path, 0o644)
            
            # Store private key with restrictive permissions
            priv_path = os.path.join(device_dir, f"{algorithm}_private.key")
            with open(priv_path, 'wb') as f:
                f.write(private_key)
            os.chmod(priv_path, 0o600)
            
            # Cache keys in memory
            self._key_cache[f"{device_id}_{algorithm}_public"] = public_key
            self._key_cache[f"{device_id}_{algorithm}_private"] = private_key
            
            self.logger.info(f"Stored {algorithm} keypair for device {device_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store keypair: {e}")
            return False
    
    def load_keypair(self, device_id: str, algorithm: str = "kyber512") -> Tuple[Optional[bytes], Optional[bytes]]:
        """Load key pair from storage"""
        try:
            # Check cache first
            pub_cache_key = f"{device_id}_{algorithm}_public"
            priv_cache_key = f"{device_id}_{algorithm}_private"
            
            if pub_cache_key in self._key_cache and priv_cache_key in self._key_cache:
                return self._key_cache[pub_cache_key], self._key_cache[priv_cache_key]
            
            # Load from disk
            device_dir = os.path.join(self.storage_path, device_id)
            
            pub_path = os.path.join(device_dir, f"{algorithm}_public.key")
            priv_path = os.path.join(device_dir, f"{algorithm}_private.key")
            
            public_key = None
            private_key = None
            
            if os.path.exists(pub_path):
                with open(pub_path, 'rb') as f:
                    public_key = f.read()
            
            if os.path.exists(priv_path):
                with open(priv_path, 'rb') as f:
                    private_key = f.read()
            
            # Cache loaded keys
            if public_key and private_key:
                self._key_cache[pub_cache_key] = public_key
                self._key_cache[priv_cache_key] = private_key
            
            return public_key, private_key
            
        except Exception as e:
            self.logger.error(f"Failed to load keypair: {e}")
            return None, None
    
    def store_session_key(self, device_id: str, session_key: bytes, expiration: int) -> bool:
        """Store session key with expiration"""
        try:
            session_data = {
                'key': session_key,
                'expiration': expiration,
                'created': int(time.time())
            }
            
            cache_key = f"{device_id}_session"
            self._key_cache[cache_key] = session_data
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store session key: {e}")
            return False
    
    def get_session_key(self, device_id: str) -> Optional[bytes]:
        """Retrieve valid session key"""
        try:
            cache_key = f"{device_id}_session"
            
            if cache_key not in self._key_cache:
                return None
            
            session_data = self._key_cache[cache_key]
            current_time = int(time.time())
            
            if current_time > session_data['expiration']:
                # Key expired, remove from cache
                del self._key_cache[cache_key]
                return None
            
            return session_data['key']
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve session key: {e}")
            return None
    
    def rotate_keys(self, device_id: str, algorithm: str = "kyber512") -> bool:
        """Rotate device keys"""
        try:
            # Remove old keys from cache
            pub_cache_key = f"{device_id}_{algorithm}_public"
            priv_cache_key = f"{device_id}_{algorithm}_private"
            
            if pub_cache_key in self._key_cache:
                del self._key_cache[pub_cache_key]
            if priv_cache_key in self._key_cache:
                del self._key_cache[priv_cache_key]
            
            # Archive old keys (rename with timestamp)
            device_dir = os.path.join(self.storage_path, device_id)
            timestamp = int(time.time())
            
            pub_path = os.path.join(device_dir, f"{algorithm}_public.key")
            priv_path = os.path.join(device_dir, f"{algorithm}_private.key")
            
            if os.path.exists(pub_path):
                archived_pub = os.path.join(device_dir, f"{algorithm}_public_{timestamp}.key.archived")
                os.rename(pub_path, archived_pub)
            
            if os.path.exists(priv_path):
                archived_priv = os.path.join(device_dir, f"{algorithm}_private_{timestamp}.key.archived")
                os.rename(priv_path, archived_priv)
            
            self.logger.info(f"Rotated keys for device {device_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rotate keys: {e}")
            return False
    
    def delete_device_keys(self, device_id: str) -> bool:
        """Securely delete all keys for a device"""
        try:
            device_dir = os.path.join(self.storage_path, device_id)
            
            if os.path.exists(device_dir):
                # Remove from cache
                keys_to_remove = [k for k in self._key_cache.keys() if k.startswith(device_id)]
                for key in keys_to_remove:
                    del self._key_cache[key]
                
                # Securely delete files
                for filename in os.listdir(device_dir):
                    filepath = os.path.join(device_dir, filename)
                    if os.path.isfile(filepath):
                        # Overwrite file with random data before deletion
                        with open(filepath, 'r+b') as f:
                            length = f.seek(0, 2)
                            f.seek(0)
                            f.write(os.urandom(length))
                            f.flush()
                            os.fsync(f.fileno())
                        os.remove(filepath)
                
                os.rmdir(device_dir)
                
            self.logger.info(f"Deleted all keys for device {device_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete device keys: {e}")
            return False
    
    def get_key_info(self, device_id: str) -> Dict[str, Any]:
        """Get information about stored keys"""
        info = {
            'device_id': device_id,
            'algorithms': [],
            'has_session_key': False,
            'cached_keys': 0
        }
        
        try:
            device_dir = os.path.join(self.storage_path, device_id)
            
            if os.path.exists(device_dir):
                for filename in os.listdir(device_dir):
                    if filename.endswith('.key') and not filename.endswith('.archived'):
                        algorithm = filename.split('_')[0]
                        if algorithm not in info['algorithms']:
                            info['algorithms'].append(algorithm)
            
            # Check cache
            session_key = f"{device_id}_session"
            if session_key in self._key_cache:
                info['has_session_key'] = True
            
            info['cached_keys'] = len([k for k in self._key_cache.keys() if k.startswith(device_id)])
            
        except Exception as e:
            self.logger.error(f"Failed to get key info: {e}")
        
        return info
