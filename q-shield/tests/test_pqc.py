import pytest
from core.pqc_manager import PQCManager

def test_generate_keypair():
    pqc = PQCManager(device_profile="standard")
    pub, priv = pqc.generate_device_keypair()
    assert isinstance(pub, bytes)
    assert isinstance(priv, bytes)
    assert len(pub) > 0
    assert len(priv) > 0

def test_session_key_establishment():
    pqc = PQCManager(device_profile="standard")
    pub, _ = pqc.generate_device_keypair()
    shared, cipher = pqc.establish_session_key(pub)
    assert isinstance(shared, bytes)
    assert isinstance(cipher, bytes)
    assert len(shared) == 32

def test_encrypt_decrypt():
    pqc = PQCManager(device_profile="standard")
    key = b"\x00" * 32
    data = b"hello world"
    encrypted = pqc.encrypt_telemetry(data, key)
    decrypted = pqc.decrypt_telemetry(encrypted, key)
    assert decrypted == data

def test_sign_verify():
    pqc = PQCManager(device_profile="standard")
    data = b"test message"
    pub, priv = pqc.generate_device_keypair()
    sig = pqc.sign_data(data, priv)
    assert pqc.verify_signature(data, sig, pub)
