import json
import time
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from core.pqc_manager import PQCManager
from config.device_config import DeviceConfig

class BaseDevice(ABC):
    """Base class for all IoT devices with PQC capabilities"""
    
    def __init__(self, device_type: str, hardware_profile: str, 
                 location: Optional[Dict[str, float]] = None):
        self.device_id = str(uuid.uuid4())
        self.device_type = device_type
        self.hardware_profile = hardware_profile
        self.location = location or {"lat": 0.0, "lon": 0.0}
        self.logger = logging.getLogger(f"{__name__}.{self.device_id}")
        
        # Initialize PQC manager based on hardware profile
        self.pqc_manager = PQCManager(hardware_profile)
        
        # Device state
        self.is_registered = False
        self.session_key = None
        self.public_key = None
        self.private_key = None
        self.server_url = "http://localhost:8000"
        
        # Telemetry settings
        self.telemetry_interval = 60  # seconds
        self.last_telemetry_time = 0
        self.telemetry_buffer = []
        
        self.logger.info(f"Initialized {device_type} device with profile {hardware_profile}")
    
    @abstractmethod
    def generate_telemetry_data(self) -> Dict[str, Any]:
        """Generate device-specific telemetry data"""
        pass
    
    @abstractmethod
    def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process command from server"""
        pass
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """Generate PQC keypair for device registration"""
        try:
            public_key, private_key = self.pqc_manager.generate_device_keypair()
            self.public_key = public_key
            self.private_key = private_key
            self.logger.info("Generated PQC keypair")
            return public_key, private_key
        except Exception as e:
            self.logger.error(f"Failed to generate keypair: {e}")
            raise
    
    def register_with_server(self) -> bool:
        """Register device with Q-Shield server"""
        try:
            import requests
            
            # Generate keypair if not exists
            if not self.public_key or not self.private_key:
                self.generate_keypair()
            
            registration_data = {
                "device_type": self.device_type,
                "hardware_profile": self.hardware_profile,
                "location": self.location,
                "public_key": self.public_key.hex(),
                "device_specs": self.get_device_specs()
            }
            
            response = requests.post(
                f"{self.server_url}/api/v1/register",
                json=registration_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.device_id = result.get("device_id", self.device_id)
                self.is_registered = True
                self.logger.info(f"Successfully registered with server, ID: {self.device_id}")
                return True
            else:
                self.logger.error(f"Registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            return False
    
    def establish_session_key(self, server_public_key: bytes) -> bool:
        """Establish session key with server using PQC"""
        try:
            shared_secret, ciphertext = self.pqc_manager.establish_session_key(server_public_key)
            self.session_key = shared_secret
            self.logger.info("Established session key with server")
            return True
        except Exception as e:
            self.logger.error(f"Failed to establish session key: {e}")
            return False
    
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using session key"""
        if not self.session_key:
            raise ValueError("No session key available")
        
        return self.pqc_manager.encrypt_telemetry(data, self.session_key)
    
    def sign_data(self, data: bytes) -> bytes:
        """Sign data using device private key"""
        if not self.private_key:
            raise ValueError("No private key available")
        
        return self.pqc_manager.sign_data(data, self.private_key)
    
    def send_telemetry(self) -> bool:
        """Send encrypted telemetry to server"""
        try:
            current_time = time.time()
            
            # Check if it's time to send telemetry
            if current_time - self.last_telemetry_time < self.telemetry_interval:
                return False
            
            # Generate telemetry data
            telemetry_data = self.generate_telemetry_data()
            telemetry_json = json.dumps(telemetry_data).encode('utf-8')
            
            # Encrypt and sign telemetry
            encrypted_payload = self.encrypt_data(telemetry_json)
            signature = self.sign_data(telemetry_json)
            
            # Prepare telemetry packet
            telemetry_packet = {
                "device_id": self.device_id,
                "encrypted_payload": encrypted_payload.hex(),
                "signature": signature.hex(),
                "timestamp": current_time
            }
            
            # Send to server
            import requests
            response = requests.post(
                f"{self.server_url}/api/v1/telemetry",
                json=telemetry_packet,
                headers={"Authorization": f"Bearer {self.get_jwt_token()}"},
                timeout=30
            )
            
            if response.status_code == 200:
                self.last_telemetry_time = current_time
                self.logger.debug("Telemetry sent successfully")
                return True
            else:
                self.logger.error(f"Telemetry failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Telemetry error: {e}")
            return False
    
    def get_jwt_token(self) -> str:
        """Get JWT token for authentication"""
        # This would normally be obtained during registration/authentication
        return "dummy_jwt_token"
    
    def get_device_specs(self) -> Dict[str, Any]:
        """Get device hardware specifications"""
        caps = self.pqc_manager.hardware_caps.get_capability_summary()
        return {
            "ram_mb": caps.get("memory_mb", 64),
            "flash_mb": 16,  # Default
            "cpu_arch": caps.get("architecture", "unknown"),
            "crypto_acceleration": caps.get("crypto_acceleration", False),
            "secure_element": caps.get("secure_element", False)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get device status"""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "hardware_profile": self.hardware_profile,
            "is_registered": self.is_registered,
            "has_session_key": self.session_key is not None,
            "location": self.location,
            "last_telemetry": self.last_telemetry_time,
            "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0
        }
    
    def start(self):
        """Start device operation"""
        self.start_time = time.time()
        self.logger.info("Device started")
        
        if not self.is_registered:
            if not self.register_with_server():
                self.logger.error("Failed to register with server")
                return False
        
        return True
    
    def stop(self):
        """Stop device operation"""
        self.logger.info("Device stopped")
