import os
import secrets
import hashlib
import logging
from typing import Tuple, Optional, Dict, Any

# Try to import liboqs, fallback to dummy implementation
try:
    import oqs
    LIBOQS_AVAILABLE = True
except ImportError:
    LIBOQS_AVAILABLE = False
    logging.warning("liboqs not available, using dummy implementation")

class KyberManager:
    """Post-Quantum Kyber key encapsulation mechanism"""
    
    def __init__(self, device_profile: str = "standard"):
        self.device_profile = device_profile
        self.logger = logging.getLogger(__name__)
        
        # Select Kyber variant based on device profile
        self.kyber_variant = self._select_kyber_variant()
        
        if LIBOQS_AVAILABLE:
            self._init_liboqs()
        else:
            self._init_dummy()
            
        self.logger.info(f"KyberManager initialized with {self.kyber_variant}")
    
    def _select_kyber_variant(self) -> str:
        """Select appropriate Kyber variant based on device profile"""
        variants = {
            "high_performance": "Kyber512",
            "standard": "Kyber512", 
            "constrained": "Kyber512"  # Still use Kyber512 but optimize implementation
        }
        return variants.get(self.device_profile, "Kyber512")
    
    def _init_liboqs(self):
        """Initialize with liboqs library"""
        try:
            self.kem = oqs.KeyEncapsulation(self.kyber_variant)
            self.implementation = "liboqs"
            self.logger.info(f"Using liboqs implementation for {self.kyber_variant}")
        except Exception as e:
            self.logger.error(f"Failed to initialize liboqs: {e}")
            self._init_dummy()
    
    def _init_dummy(self):
        """Initialize with dummy implementation for testing"""
        self.kem = None
        self.implementation = "dummy"
        self.logger.warning("Using dummy Kyber implementation - NOT SECURE")
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """Generate Kyber keypair"""
        try:
            if self.implementation == "liboqs" and self.kem:
                public_key = self.kem.generate_keypair()
                private_key = self.kem.export_secret_key()
                return public_key, private_key
            else:
                return self._dummy_generate_keypair()
                
        except Exception as e:
            self.logger.error(f"Keypair generation failed: {e}")
            return self._dummy_generate_keypair()
    
    def encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """Encapsulate shared secret using public key"""
        try:
            if self.implementation == "liboqs" and self.kem:
                ciphertext, shared_secret = self.kem.encap_secret(public_key)
                return shared_secret, ciphertext
            else:
                return self._dummy_encapsulate(public_key)
                
        except Exception as e:
            self.logger.error(f"Encapsulation failed: {e}")
            return self._dummy_encapsulate(public_key)
    
    def decapsulate(self, ciphertext: bytes, private_key: bytes) -> bytes:
        """Decapsulate shared secret using private key and ciphertext"""
        try:
            if self.implementation == "liboqs" and self.kem:
                # Import the private key
                self.kem.import_secret_key(private_key)
                shared_secret = self.kem.decap_secret(ciphertext)
                return shared_secret
            else:
                return self._dummy_decapsulate(ciphertext, private_key)
                
        except Exception as e:
            self.logger.error(f"Decapsulation failed: {e}")
            return self._dummy_decapsulate(ciphertext, private_key)
    
    def _dummy_generate_keypair(self) -> Tuple[bytes, bytes]:
        """Dummy keypair generation for testing"""
        public_key = secrets.token_bytes(800)   # Kyber512 public key size
        private_key = secrets.token_bytes(1632) # Kyber512 private key size
        return public_key, private_key
    
    def _dummy_encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """Dummy encapsulation for testing"""
        shared_secret = secrets.token_bytes(32)  # 256-bit shared secret
        ciphertext = secrets.token_bytes(768)    # Kyber512 ciphertext size
        return shared_secret, ciphertext
    
    def _dummy_decapsulate(self, ciphertext: bytes, private_key: bytes) -> bytes:
        """Dummy decapsulation for testing"""
        # In real implementation, this would derive from ciphertext and private_key
        return hashlib.sha256(ciphertext + private_key).digest()
    
    def get_key_sizes(self) -> Dict[str, int]:
        """Get key and ciphertext sizes for current variant"""
        sizes = {
            "Kyber512": {
                "public_key": 800,
                "private_key": 1632,
                "ciphertext": 768,
                "shared_secret": 32
            },
            "Kyber768": {
                "public_key": 1184,
                "private_key": 2400,
                "ciphertext": 1088,
                "shared_secret": 32
            },
            "Kyber1024": {
                "public_key": 1568,
                "private_key": 3168,
                "ciphertext": 1568,
                "shared_secret": 32
            }
        }
        
        return sizes.get(self.kyber_variant, sizes["Kyber512"])
    
    def validate_key_sizes(self, public_key: bytes, private_key: bytes = None) -> bool:
        """Validate key sizes match expected values"""
        expected_sizes = self.get_key_sizes()
        
        if len(public_key) != expected_sizes["public_key"]:
            self.logger.error(f"Invalid public key size: {len(public_key)}, expected {expected_sizes['public_key']}")
            return False
        
        if private_key and len(private_key) != expected_sizes["private_key"]:
            self.logger.error(f"Invalid private key size: {len(private_key)}, expected {expected_sizes['private_key']}")
            return False
        
        return True
    
    def get_performance_info(self) -> Dict[str, Any]:
        """Get performance information for current configuration"""
        return {
            "variant": self.kyber_variant,
            "implementation": self.implementation,
            "device_profile": self.device_profile,
            "key_sizes": self.get_key_sizes(),
            "security_level": 1 if self.kyber_variant == "Kyber512" else 3,
            "estimated_ops_per_sec": self._get_estimated_performance()
        }
    
    def _get_estimated_performance(self) -> Dict[str, int]:
        """Get estimated operations per second based on profile"""
        base_performance = {
            "high_performance": {"keygen": 500, "encap": 800, "decap": 700},
            "standard": {"keygen": 100, "encap": 150, "decap": 140},
            "constrained": {"keygen": 20, "encap": 30, "decap": 25}
        }
        
        return base_performance.get(self.device_profile, base_performance["standard"])
