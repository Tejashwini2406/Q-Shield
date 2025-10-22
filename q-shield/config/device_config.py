import os
from typing import Dict, Any, List

class DeviceConfig:
    """Configuration for IoT devices and hardware profiles"""
    
    # Device Types
    DEVICE_TYPES = [
        "sensor_node",
        "gateway",
        "actuator",
        "camera",
        "environmental_monitor",
        "security_device",
        "smart_meter"
    ]
    
    # Hardware Profiles
    HARDWARE_PROFILES = {
        "high_performance": {
            "min_ram_mb": 512,
            "min_flash_mb": 64,
            "cpu_arch": ["x86_64", "arm64", "armv8"],
            "crypto_acceleration": True,
            "secure_element": True,
            "description": "High-end IoT devices with crypto acceleration"
        },
        "standard": {
            "min_ram_mb": 64,
            "min_flash_mb": 16,
            "cpu_arch": ["armv7", "armv8", "cortex-m4", "cortex-m7"],
            "crypto_acceleration": False,
            "secure_element": False,
            "description": "Standard IoT devices with moderate resources"
        },
        "constrained": {
            "min_ram_mb": 16,
            "min_flash_mb": 4,
            "cpu_arch": ["cortex-m0", "cortex-m3", "8051", "avr"],
            "crypto_acceleration": False,
            "secure_element": False,
            "description": "Resource-constrained IoT devices"
        }
    }
    
    # Memory Requirements (in KB)
    MEMORY_REQUIREMENTS = {
        "kyber512": {
            "public_key": 800,
            "private_key": 1632,
            "ciphertext": 768,
            "shared_secret": 32
        },
        "dilithium2": {
            "public_key": 1312,
            "private_key": 2528,
            "signature": 2420
        },
        "aes_gcm": {
            "key": 32,
            "iv": 12,
            "tag": 16
        }
    }
    
    # Device Registration Settings
    MAX_DEVICES_PER_GATEWAY = 100
    DEVICE_HEARTBEAT_INTERVAL = 300  # 5 minutes
    DEVICE_TIMEOUT_MULTIPLIER = 3    # 15 minutes before timeout
    
    # Telemetry Configuration
    TELEMETRY_SETTINGS = {
        "max_payload_size": 4096,      # bytes
        "compression_enabled": True,
        "encryption_mandatory": True,
        "signature_required": True,
        "batch_size": 10,
        "flush_interval": 30           # seconds
    }
    
    # Geo-fencing Configuration
    GEOFENCE_CONFIG = {
        "enabled": True,
        "default_radius_meters": 1000,
        "violation_threshold": 3,      # consecutive violations
        "alert_cooldown": 300          # 5 minutes between alerts
    }
    
    @classmethod
    def get_profile_requirements(cls, profile: str) -> Dict[str, Any]:
        """Get hardware requirements for profile"""
        return cls.HARDWARE_PROFILES.get(profile, cls.HARDWARE_PROFILES["standard"])
    
    @classmethod
    def is_compatible(cls, device_specs: Dict[str, Any], profile: str) -> bool:
        """Check if device specs meet profile requirements"""
        requirements = cls.get_profile_requirements(profile)
        
        ram_ok = device_specs.get("ram_mb", 0) >= requirements["min_ram_mb"]
        flash_ok = device_specs.get("flash_mb", 0) >= requirements["min_flash_mb"]
        arch_ok = device_specs.get("cpu_arch") in requirements["cpu_arch"]
        
        return ram_ok and flash_ok and arch_ok
