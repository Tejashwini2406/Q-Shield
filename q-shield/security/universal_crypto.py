from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
import os
import logging
from core.hardware_detector import HardwareCapabilities

class CryptoInterface(ABC):
    """Abstract interface for all cryptographic operations"""
    
    @abstractmethod
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """Generate public/private key pair"""
        pass
    
    @abstractmethod
    def encrypt(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data"""
        pass
    
    @abstractmethod
    def decrypt(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Decrypt data"""
        pass
    
    @abstractmethod
    def sign(self, data: bytes, private_key: bytes) -> bytes:
        """Sign data"""
        pass
    
    @abstractmethod
    def verify(self, data: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify signature"""
        pass

class UniversalCryptoProvider:
    """Provides cryptographic operations across all device types"""
    
    def __init__(self, device_profile: str):
        self.device_profile = device_profile
        self.logger = logging.getLogger(__name__)
        self.hardware_caps = HardwareCapabilities()
        self._setup_crypto_context()
    
    def _setup_crypto_context(self):
        """Setup cryptographic context based on device profile"""
        self.crypto_config = self._get_profile_config()
        self.logger.info(f"Configured crypto for {self.device_profile} profile")
        
        if self.device_profile == "high_performance":
            self._setup_high_performance()
        elif self.device_profile == "standard":
            self._setup_standard()
        else:
            self._setup_constrained()
    
    def _setup_high_performance(self):
        """Setup for devices with crypto acceleration"""
        self.logger.info("Configuring for high-performance device")
        self.use_hardware_accel = True
        self.kyber_variant = "kyber512"
        self.dilithium_variant = "dilithium2"
        self.symmetric_cipher = "aes_gcm"
    
    def _setup_standard(self):
        """Setup for standard IoT devices"""
        self.logger.info("Configuring for standard device")
        self.use_hardware_accel = False
        self.kyber_variant = "kyber512"
        self.dilithium_variant = "dilithium2"
        self.symmetric_cipher = "chacha20_poly1305"
    
    def _setup_constrained(self):
        """Setup for resource-constrained devices"""
        self.logger.info("Configuring for constrained device")
        self.use_hardware_accel = False
        self.kyber_variant = "kyber512_compact"
        self.dilithium_variant = "dilithium2_compact"
        self.symmetric_cipher = "chacha20_poly1305"
    
    def _get_profile_config(self) -> Dict[str, Any]:
        """Get configuration for the current profile"""
        configs = {
            "high_performance": {
                "key_cache_size": 1000,
                "async_operations": True,
                "hardware_rng": True,
                "batch_operations": True
            },
            "standard": {
                "key_cache_size": 100,
                "async_operations": False,
                "hardware_rng": False,
                "batch_operations": False
            },
            "constrained": {
                "key_cache_size": 10,
                "async_operations": False,
                "hardware_rng": False,
                "batch_operations": False
            }
        }
        
        return configs.get(self.device_profile, configs["standard"])
    
    def get_optimal_parameters(self) -> Dict[str, Any]:
        """Get optimal cryptographic parameters for current profile"""
        return {
            "kyber_variant": self.kyber_variant,
            "dilithium_variant": self.dilithium_variant,
            "symmetric_cipher": self.symmetric_cipher,
            "use_hardware_accel": self.use_hardware_accel,
            "config": self.crypto_config
        }
    
    def estimate_performance(self, operation: str) -> Dict[str, float]:
        """Estimate performance for cryptographic operations"""
        # Base performance estimates in operations per second
        base_performance = {
            "high_performance": {
                "kyber_keygen": 500,
                "kyber_encap": 800,
                "kyber_decap": 700,
                "dilithium_sign": 300,
                "dilithium_verify": 600,
                "aes_encrypt": 50000,
                "chacha_encrypt": 30000
            },
            "standard": {
                "kyber_keygen": 100,
                "kyber_encap": 150,
                "kyber_decap": 140,
                "dilithium_sign": 60,
                "dilithium_verify": 120,
                "aes_encrypt": 10000,
                "chacha_encrypt": 15000
            },
            "constrained": {
                "kyber_keygen": 20,
                "kyber_encap": 30,
                "kyber_decap": 25,
                "dilithium_sign": 10,
                "dilithium_verify": 20,
                "aes_encrypt": 2000,
                "chacha_encrypt": 3000
            }
        }
        
        profile_perf = base_performance.get(self.device_profile, base_performance["standard"])
        
        return {
            "operations_per_second": profile_perf.get(operation, 100),
            "estimated_latency_ms": 1000 / profile_perf.get(operation, 100),
            "memory_usage_kb": self._estimate_memory_usage(operation),
            "power_consumption_mw": self._estimate_power_consumption(operation)
        }
    
    def _estimate_memory_usage(self, operation: str) -> float:
        """Estimate memory usage for operation"""
        memory_estimates = {
            "kyber_keygen": 4.0,
            "kyber_encap": 2.0,
            "kyber_decap": 2.0,
            "dilithium_sign": 8.0,
            "dilithium_verify": 4.0,
            "aes_encrypt": 0.5,
            "chacha_encrypt": 0.3
        }
        
        base_memory = memory_estimates.get(operation, 1.0)
        
        # Scale based on profile
        multipliers = {
            "high_performance": 1.5,  # More memory for performance
            "standard": 1.0,
            "constrained": 0.7        # Optimized for less memory
        }
        
        return base_memory * multipliers.get(self.device_profile, 1.0)
    
    def _estimate_power_consumption(self, operation: str) -> float:
        """Estimate power consumption for operation"""
        power_estimates = {
            "kyber_keygen": 50.0,
            "kyber_encap": 30.0,
            "kyber_decap": 30.0,
            "dilithium_sign": 80.0,
            "dilithium_verify": 40.0,
            "aes_encrypt": 5.0,
            "chacha_encrypt": 8.0
        }
        
        base_power = power_estimates.get(operation, 20.0)
        
        # Hardware acceleration reduces power consumption
        if self.use_hardware_accel and operation in ["aes_encrypt"]:
            base_power *= 0.5
        
        return base_power
