from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import jwt
from datetime import datetime, timezone, timedelta
import time
from fastapi import HTTPException

SECRET_KEY = "supersecretkey" 

#♡ AES-GCM Encryption
def encrypt_aes_gcm(aes_key: bytes, plaintext: str):
    nonce = get_random_bytes(12)
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
    return ciphertext, nonce, tag

#♡ AES-GCM Decryption
def decrypt_aes_gcm(aes_key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes):
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode()

#♡ JWT Creation
def create_jwt(did: str):
    payload = {
        "sub": did,
        "exp": int(time.time()) + 24 * 3600  # ♡ numeric timestamp
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

#♡ JWT Verification
def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise Exception("JWT expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid JWT")


