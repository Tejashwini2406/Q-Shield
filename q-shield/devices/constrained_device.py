import time
import random
from typing import Dict, Any
from devices.device_base import BaseDevice

class ConstrainedDevice(BaseDevice):
    """Resource-constrained IoT device with minimal capabilities"""
    
    def __init__(self, device_type: str = "basic_sensor",
                 location: Dict[str, float] = None):
        super().__init__(device_type, "constrained", location)
        
        # Constrained device settings
        self.telemetry_interval = 300  # Send telemetry every 5 minutes
        self.minimal_data = True
        self.low_power_mode = True
        self.limited_processing = True
        
        # Simple sensor data
        self.sensor_data = {
            "value": 0.0,
            "status": 1,  # 0=error, 1=ok, 2=warning
            "counter": 0
        }
        
        # Resource constraints
        self.max_payload_size = 64  # bytes
        self.max_telemetry_fields = 5
        
        self.logger.info("Constrained device initialized with minimal capabilities")
    
    def generate_telemetry_data(self) -> Dict[str, Any]:
        """Generate minimal telemetry data to fit resource constraints"""
        current_time = time.time()
        
        # Increment counter
        self.sensor_data["counter"] = (self.sensor_data["counter"] + 1) % 65536
        
        # Simulate simple sensor reading based on device type
        if self.device_type == "temperature_sensor":
            self.sensor_data["value"] = round(20 + random.uniform(-5, 10), 1)
        elif self.device_type == "humidity_sensor":
            self.sensor_data["value"] = round(50 + random.uniform(-15, 20), 1)
        elif self.device_type == "motion_sensor":
            self.sensor_data["value"] = 1 if random.random() < 0.1 else 0  # 10% motion
        elif self.device_type == "door_sensor":
            self.sensor_data["value"] = 1 if random.random() < 0.05 else 0  # 5% open
        else:
            # Generic sensor
            self.sensor_data["value"] = round(random.uniform(0, 100), 1)
        
        # Simulate occasional sensor errors
        if random.random() < 0.01:  # 1% chance
            self.sensor_data["status"] = 0  # Error
        elif random.random() < 0.05:  # 5% chance
            self.sensor_data["status"] = 2  # Warning
        else:
            self.sensor_data["status"] = 1  # OK
        
        # Create minimal telemetry packet
        telemetry = {
            "t": int(current_time),  # timestamp (abbreviated)
            "v": self.sensor_data["value"],  # value
            "s": self.sensor_data["status"],  # status
            "c": self.sensor_data["counter"]  # counter
        }
        
        # Add battery level if battery-powered
        if self.device_type in ["wireless_sensor", "battery_sensor"]:
            battery_level = max(10, 100 - (self.sensor_data["counter"] * 0.01))
            telemetry["b"] = round(battery_level, 1)
        
        return telemetry
    
    def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process simple commands within resource constraints"""
        cmd_type = command.get("type", "")
        
        # Only support essential commands due to resource constraints
        if cmd_type == "ping":
            return {"status": "ok"}
        
        elif cmd_type == "reset_counter":
            self.sensor_data["counter"] = 0
            return {"status": "ok", "counter": 0}
        
        elif cmd_type == "update_interval":
            new_interval = command.get("interval", 300)
            # Constrain to reasonable limits for low-power operation
            self.telemetry_interval = max(60, min(3600, new_interval))  # 1min to 1hour
            return {"status": "ok", "interval": self.telemetry_interval}
        
        elif cmd_type == "sleep":
            # Enter deep sleep mode
            duration = min(command.get("duration", 600), 3600)  # Max 1 hour
            return {"status": "ok", "sleep": duration}
        
        elif cmd_type == "calibrate":
            # Simple calibration - reset to baseline
            if self.device_type not in ["motion_sensor", "door_sensor"]:
                self.sensor_data["value"] = 0.0
            return {"status": "ok"}
        
        # Reject complex commands to save resources
        return {"status": "error", "msg": "unsupported"}
    
    def compress_telemetry(self, telemetry: Dict[str, Any]) -> bytes:
        """Simple compression for telemetry data"""
        # Very basic compression - just pack essential values
        import struct
        
        try:
            # Pack timestamp (4 bytes), value (2 bytes scaled), status (1 byte), counter (2 bytes)
            timestamp = int(telemetry.get("t", time.time()))
            value = int(telemetry.get("v", 0) * 10)  # Scale by 10 for 1 decimal precision
            status = int(telemetry.get("s", 1))
            counter = int(telemetry.get("c", 0))
            battery = int(telemetry.get("b", 100))
            
            packed = struct.pack('>IHBHB', timestamp, value, status, counter, battery)
            return packed
            
        except Exception as e:
            self.logger.error(f"Compression failed: {e}")
            # Fallback to JSON
            import json
            return json.dumps(telemetry).encode('utf-8')
    
    def send_telemetry(self) -> bool:
        """Override to use compression and minimal protocol"""
        try:
            current_time = time.time()
            
            # Check interval
            if current_time - self.last_telemetry_time < self.telemetry_interval:
                return False
            
            # Generate minimal telemetry
            telemetry_data = self.generate_telemetry_data()
            
            # Compress if possible
            if len(str(telemetry_data)) > self.max_payload_size:
                payload = self.compress_telemetry(telemetry_data)
            else:
                import json
                payload = json.dumps(telemetry_data).encode('utf-8')
            
            # Simple encryption (XOR for minimal resource usage)
            if self.session_key:
                encrypted_payload = self.simple_encrypt(payload)
            else:
                encrypted_payload = payload
            
            # Create minimal packet
            packet = {
                "id": self.device_id[-8:],  # Use only last 8 chars to save space
                "data": encrypted_payload.hex(),
                "t": int(current_time)
            }
            
            # In a real implementation, this would use a lightweight protocol
            # like CoAP, MQTT-SN, or custom UDP protocol
            self.logger.debug(f"Sending telemetry: {len(payload)} bytes")
            
            self.last_telemetry_time = current_time
            return True
            
        except Exception as e:
            self.logger.error(f"Telemetry error: {e}")
            return False
    
    def simple_encrypt(self, data: bytes) -> bytes:
        """Simple XOR encryption for constrained devices"""
        if not self.session_key:
            return data
        
        # Use first 16 bytes of session key for XOR
        key = self.session_key[:16]
        encrypted = bytearray()
        
        for i, byte in enumerate(data):
            encrypted.append(byte ^ key[i % len(key)])
        
        return bytes(encrypted)
    
    def enter_deep_sleep(self, duration: int):
        """Enter deep sleep mode to conserve battery"""
        self.logger.info(f"Entering deep sleep for {duration} seconds")
        # In real implementation, this would power down most components
        # For simulation, we just mark the time
        self.sleep_start_time = time.time()
        self.sleep_duration = duration
    
    def is_sleeping(self) -> bool:
        """Check if device is in sleep mode"""
        if not hasattr(self, 'sleep_start_time'):
            return False
        
        return (time.time() - self.sleep_start_time) < self.sleep_duration
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        return {
            "memory_used_bytes": random.randint(2048, 8192),  # 2-8KB
            "flash_used_bytes": random.randint(4096, 16384),  # 4-16KB
            "cpu_usage_percent": random.randint(5, 25),       # 5-25%
            "power_mode": "low_power" if self.low_power_mode else "normal",
            "last_telemetry_size": random.randint(32, 64)    # bytes
        }
