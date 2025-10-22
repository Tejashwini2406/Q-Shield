import pytest
from devices.device_base import BaseDevice
from devices.high_end_device import HighEndDevice
from devices.mid_tier_device import MidTierDevice
from devices.constrained_device import ConstrainedDevice

def test_high_end_device_registration(monkeypatch):
    dev = HighEndDevice()
    monkeypatch.setattr(dev, 'register_with_server', lambda: True)
    assert dev.start() is True
    assert dev.is_registered

def test_mid_tier_telemetry_generation():
    dev = MidTierDevice()
    assert isinstance(dev.generate_telemetry_data(), dict)
    telemetry = dev.generate_telemetry_data()
    assert 'temperature' in telemetry or 'value' in telemetry

def test_constrained_device_compression():
    dev = ConstrainedDevice(device_type="temperature_sensor")
    data = dev.generate_telemetry_data()
    compressed = dev.compress_telemetry(data)
    assert isinstance(compressed, (bytes, bytearray))
    assert len(compressed) <= dev.max_payload_size + 10
