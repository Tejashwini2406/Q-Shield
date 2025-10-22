import time
import random
from typing import Dict, Any
from devices.device_base import BaseDevice

class HighEndDevice(BaseDevice):
    """High-end IoT device with crypto acceleration and advanced capabilities"""
    
    def __init__(self, device_type: str = "gateway", 
                 location: Dict[str, float] = None):
        super().__init__(device_type, "high_performance", location)
        
        # High-end device specific settings
        self.telemetry_interval = 30  # Send telemetry every 30 seconds
        self.max_concurrent_connections = 100
        self.advanced_sensors = True
        self.ml_processing = True
        self.edge_computing = True
        
        # Sensor simulation data
        self.sensor_data = {
            "temperature": 25.0,
            "humidity": 60.0,
            "pressure": 1013.25,
            "air_quality": 150,
            "noise_level": 45.0,
            "light_intensity": 300,
            "motion_detected": False,
            "power_consumption": 50.0,
            "cpu_usage": 30.0,
            "memory_usage": 40.0,
            "network_throughput": 100.0,
            "connected_devices": 25
        }
        
        self.logger.info("High-end device initialized with advanced capabilities")
    
    def start(self):
        success = self.register_with_server()
        if success:
            self.is_registered = True
        return success

    def generate_telemetry_data(self) -> Dict[str, Any]:
        """Generate comprehensive telemetry data"""
        current_time = time.time()
        
        # Simulate sensor readings with realistic variations
        self.sensor_data.update({
            "timestamp": current_time,
            "temperature": self.sensor_data["temperature"] + random.uniform(-2.0, 2.0),
            "humidity": max(0, min(100, self.sensor_data["humidity"] + random.uniform(-5.0, 5.0))),
            "pressure": self.sensor_data["pressure"] + random.uniform(-2.0, 2.0),
            "air_quality": max(0, self.sensor_data["air_quality"] + random.randint(-10, 10)),
            "noise_level": max(0, self.sensor_data["noise_level"] + random.uniform(-5.0, 5.0)),
            "light_intensity": max(0, self.sensor_data["light_intensity"] + random.randint(-50, 50)),
            "motion_detected": random.choice([True, False]) if random.random() < 0.1 else False,
            "power_consumption": max(0, self.sensor_data["power_consumption"] + random.uniform(-5.0, 5.0)),
            "cpu_usage": max(0, min(100, self.sensor_data["cpu_usage"] + random.uniform(-10.0, 10.0))),
            "memory_usage": max(0, min(100, self.sensor_data["memory_usage"] + random.uniform(-5.0, 5.0))),
            "network_throughput": max(0, self.sensor_data["network_throughput"] + random.uniform(-20.0, 20.0)),
            "connected_devices": max(0, self.sensor_data["connected_devices"] + random.randint(-3, 3))
        })
        
        # Add computed metrics
        telemetry = {
            **self.sensor_data,
            "device_health": self.calculate_device_health(),
            "security_events": self.get_security_events(),
            "network_status": self.get_network_status(),
            "crypto_performance": self.get_crypto_performance()
        }
        
        return telemetry
    
    def calculate_device_health(self) -> Dict[str, Any]:
        """Calculate overall device health metrics"""
        cpu_health = 100 - self.sensor_data["cpu_usage"]
        memory_health = 100 - self.sensor_data["memory_usage"]
        power_health = 100 if self.sensor_data["power_consumption"] < 80 else 50
        
        overall_health = (cpu_health + memory_health + power_health) / 3
        
        return {
            "overall_score": round(overall_health, 2),
            "cpu_health": round(cpu_health, 2),
            "memory_health": round(memory_health, 2),
            "power_health": round(power_health, 2),
            "status": "healthy" if overall_health > 70 else "warning" if overall_health > 40 else "critical"
        }
    
    def get_security_events(self) -> Dict[str, Any]:
        """Simulate security event detection"""
        events = []
        
        # Simulate occasional security events
        if random.random() < 0.05:  # 5% chance
            events.append({
                "type": "anomaly_detected",
                "severity": "medium",
                "description": "Unusual network traffic pattern detected"
            })
        
        if random.random() < 0.02:  # 2% chance
            events.append({
                "type": "authentication_failure",
                "severity": "high",
                "description": "Multiple failed authentication attempts"
            })
        
        return {
            "event_count": len(events),
            "events": events,
            "last_scan": time.time()
        }
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get network connectivity status"""
        return {
            "connection_type": "ethernet",
            "signal_strength": random.randint(80, 100),
            "bandwidth_usage": self.sensor_data["network_throughput"],
            "packet_loss": round(random.uniform(0, 2.0), 2),
            "latency_ms": random.randint(10, 50),
            "active_connections": self.sensor_data["connected_devices"]
        }
    
    def get_crypto_performance(self) -> Dict[str, Any]:
        """Get cryptographic operation performance metrics"""
        return {
            "pqc_operations_per_sec": random.randint(800, 1200),
            "aes_operations_per_sec": random.randint(5000, 8000),
            "key_generation_time_ms": round(random.uniform(0.5, 2.0), 2),
            "encryption_time_ms": round(random.uniform(0.1, 0.5), 2),
            "hardware_acceleration": True
        }
    
    def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process commands from server"""
        cmd_type = command.get("type", "")
        
        if cmd_type == "update_telemetry_interval":
            new_interval = command.get("interval", 30)
            self.telemetry_interval = max(10, min(300, new_interval))  # 10s to 5min
            return {"status": "success", "new_interval": self.telemetry_interval}
        
        elif cmd_type == "security_scan":
            return {
                "status": "success",
                "scan_results": {
                    "threats_detected": random.randint(0, 3),
                    "vulnerabilities": random.randint(0, 2),
                    "scan_duration": random.randint(30, 120)
                }
            }
        
        elif cmd_type == "reboot":
            self.logger.info("Received reboot command")
            return {"status": "success", "message": "Reboot scheduled"}
        
        elif cmd_type == "update_location":
            new_location = command.get("location", {})
            if "lat" in new_location and "lon" in new_location:
                self.location = new_location
                return {"status": "success", "new_location": self.location}
        
        return {"status": "error", "message": f"Unknown command: {cmd_type}"}
    
    def run_edge_analytics(self) -> Dict[str, Any]:
        """Run edge analytics on collected data"""
        # Simulate edge ML processing
        return {
            "anomaly_score": round(random.uniform(0, 1), 3),
            "prediction_confidence": round(random.uniform(0.7, 0.99), 3),
            "patterns_detected": random.randint(0, 5),
            "processing_time_ms": round(random.uniform(10, 50), 2)
        }
