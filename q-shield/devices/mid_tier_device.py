import time
import random
from typing import Dict, Any
from devices.device_base import BaseDevice

class MidTierDevice(BaseDevice):
    """Mid-tier IoT device with moderate capabilities"""
    
    def __init__(self, device_type: str = "sensor_node",
                 location: Dict[str, float] = None):
        super().__init__(device_type, "standard", location)
        
        # Mid-tier device settings
        self.telemetry_interval = 60  # Send telemetry every minute
        self.battery_powered = True
        self.sleep_mode_enabled = True
        self.basic_sensors = True
        
        # Sensor simulation data
        self.sensor_data = {
            "temperature": 22.0,
            "humidity": 55.0,
            "battery_level": 85.0,
            "signal_strength": 75,
            "uptime": 0,
            "sensor_status": "active"
        }
        
        self.logger.info("Mid-tier device initialized with standard capabilities")
    
    def generate_telemetry_data(self) -> Dict[str, Any]:
        """Generate standard telemetry data"""
        current_time = time.time()
        
        # Simulate battery drain
        if self.battery_powered:
            self.sensor_data["battery_level"] = max(0, 
                self.sensor_data["battery_level"] - random.uniform(0.01, 0.1))
        
        # Update sensor readings
        self.sensor_data.update({
            "timestamp": current_time,
            "temperature": self.sensor_data["temperature"] + random.uniform(-1.5, 1.5),
            "humidity": max(0, min(100, self.sensor_data["humidity"] + random.uniform(-3.0, 3.0))),
            "signal_strength": max(0, min(100, self.sensor_data["signal_strength"] + random.randint(-5, 5))),
            "uptime": current_time - self.start_time if hasattr(self, 'start_time') else 0
        })
        
        # Basic telemetry structure
        telemetry = {
            **self.sensor_data,
            "device_status": self.get_device_status(),
            "power_management": self.get_power_status()
        }
        
        # Add location if GPS-enabled
        if self.device_type in ["tracker", "mobile_sensor"]:
            telemetry["location"] = self.get_current_location()
        
        return telemetry
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get basic device status"""
        status = "active"
        
        if self.sensor_data["battery_level"] < 20:
            status = "low_battery"
        elif self.sensor_data["signal_strength"] < 30:
            status = "weak_signal"
        elif random.random() < 0.02:  # 2% chance of error
            status = "sensor_error"
        
        return {
            "status": status,
            "last_reboot": time.time() - random.randint(3600, 86400),  # 1-24 hours ago
            "firmware_version": "1.2.3",
            "configuration_hash": "abc123def456"
        }
    
    def get_power_status(self) -> Dict[str, Any]:
        """Get power management information"""
        if not self.battery_powered:
            return {
                "power_source": "external",
                "power_consumption_mw": round(random.uniform(500, 1500), 2)
            }
        
        # Battery-powered device
        estimated_runtime = (self.sensor_data["battery_level"] / 100) * 720  # 30 days max
        
        return {
            "power_source": "battery",
            "battery_level": round(self.sensor_data["battery_level"], 2),
            "estimated_runtime_hours": round(estimated_runtime, 1),
            "charging_status": "not_charging",
            "power_saving_mode": self.sensor_data["battery_level"] < 30
        }
    
    def get_current_location(self) -> Dict[str, float]:
        """Simulate GPS location with small variations"""
        base_lat = self.location.get("lat", 0.0)
        base_lon = self.location.get("lon", 0.0)
        
        # Add small random variations (within 100m radius)
        lat_offset = random.uniform(-0.0009, 0.0009)  # ~100m
        lon_offset = random.uniform(-0.0009, 0.0009)
        
        return {
            "lat": round(base_lat + lat_offset, 6),
            "lon": round(base_lon + lon_offset, 6),
            "accuracy": random.randint(5, 20),  # meters
            "altitude": round(random.uniform(50, 200), 1)  # meters
        }
    
    def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process commands from server"""
        cmd_type = command.get("type", "")
        
        if cmd_type == "update_telemetry_interval":
            new_interval = command.get("interval", 60)
            self.telemetry_interval = max(30, min(600, new_interval))  # 30s to 10min
            return {"status": "success", "new_interval": self.telemetry_interval}
        
        elif cmd_type == "sleep":
            duration = command.get("duration", 300)  # 5 minutes default
            self.logger.info(f"Entering sleep mode for {duration} seconds")
            return {"status": "success", "sleep_duration": duration}
        
        elif cmd_type == "calibrate_sensors":
            self.logger.info("Calibrating sensors")
            # Simulate calibration
            time.sleep(2)
            return {"status": "success", "calibration_result": "sensors calibrated"}
        
        elif cmd_type == "update_location":
            new_location = command.get("location", {})
            if "lat" in new_location and "lon" in new_location:
                self.location = new_location
                return {"status": "success", "new_location": self.location}
        
        elif cmd_type == "factory_reset":
            self.logger.info("Factory reset requested")
            return {"status": "success", "message": "Factory reset will be performed on next reboot"}
        
        return {"status": "error", "message": f"Unknown or unsupported command: {cmd_type}"}
    
    def enter_sleep_mode(self, duration: int):
        """Enter power-saving sleep mode"""
        self.logger.info(f"Entering sleep mode for {duration} seconds")
        # In a real implementation, this would reduce power consumption
        time.sleep(min(duration, 60))  # Simulate but don't actually sleep too long
        
    def check_battery_level(self) -> bool:
        """Check if battery level is sufficient for operation"""
        if self.battery_powered and self.sensor_data["battery_level"] < 5:
            self.logger.warning("Critical battery level, entering emergency mode")
            return False
        return True
