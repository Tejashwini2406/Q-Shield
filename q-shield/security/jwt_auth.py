import jwt
import time
import secrets
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class JWTAuthenticator:
    """JWT-based authentication for IoT devices"""
    
    def __init__(self, secret_key: Optional[str] = None, 
                 algorithm: str = "HS256",
                 default_expiration: int = 3600):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = algorithm
        self.default_expiration = default_expiration  # seconds
        self.logger = logging.getLogger(__name__)
        
        # Token blacklist for logout/revocation
        self.blacklisted_tokens = set()
        
        self.logger.info(f"JWTAuthenticator initialized with {algorithm}")
    
    def create_token(self, device_id: str, device_type: str = "device",
                    custom_claims: Optional[Dict[str, Any]] = None,
                    expires_in: Optional[int] = None) -> str:
        """Create JWT token for device authentication"""
        try:
            current_time = datetime.utcnow()
            expiration_time = current_time + timedelta(
                seconds=expires_in or self.default_expiration
            )
            
            # Standard JWT claims
            payload = {
                "sub": device_id,           # Subject (device ID)
                "iat": current_time,        # Issued at
                "exp": expiration_time,     # Expiration
                "iss": "qshield-server",    # Issuer
                "aud": "qshield-devices",   # Audience
                "device_type": device_type,
                "token_type": "access"
            }
            
            # Add custom claims
            if custom_claims:
                payload.update(custom_claims)
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            self.logger.debug(f"Created token for device {device_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"Token creation failed: {e}")
            raise
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            # Check if token is blacklisted
            if token in self.blacklisted_tokens:
                raise jwt.InvalidTokenError("Token has been revoked")
            
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="qshield-devices",
                issuer="qshield-server"
            )
            
            self.logger.debug(f"Verified token for device {payload.get('sub')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token has expired")
            raise
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token: {e}")
            raise
    
    def refresh_token(self, token: str) -> str:
        """Refresh an existing token (extend expiration)"""
        try:
            # Verify current token (will raise exception if invalid)
            payload = self.verify_token(token)
            
            # Blacklist old token
            self.blacklisted_tokens.add(token)
            
            # Create new token with same claims but extended expiration
            device_id = payload["sub"]
            device_type = payload.get("device_type", "device")
            
            # Remove standard JWT claims before using as custom claims
            custom_claims = {k: v for k, v in payload.items() 
                           if k not in ["sub", "iat", "exp", "iss", "aud"]}
            
            new_token = self.create_token(
                device_id=device_id,
                device_type=device_type,
                custom_claims=custom_claims
            )
            
            self.logger.info(f"Refreshed token for device {device_id}")
            return new_token
            
        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}")
            raise
    
    def revoke_token(self, token: str):
        """Revoke a token (add to blacklist)"""
        try:
            # Verify token is valid before revoking
            payload = self.verify_token(token)
            device_id = payload["sub"]
            
            # Add to blacklist
            self.blacklisted_tokens.add(token)
            
            self.logger.info(f"Revoked token for device {device_id}")
            
        except Exception as e:
            self.logger.error(f"Token revocation failed: {e}")
            raise
    
    def create_refresh_token(self, device_id: str, 
                           expires_in: int = 7 * 24 * 3600) -> str:  # 7 days
        """Create long-lived refresh token"""
        payload = {
            "sub": device_id,
            "token_type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iss": "qshield-server",
            "aud": "qshield-devices"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_refresh_token(self, refresh_token: str) -> str:
        """Validate refresh token and create new access token"""
        try:
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience="qshield-devices",
                issuer="qshield-server"
            )
            
            if payload.get("token_type") != "refresh":
                raise jwt.InvalidTokenError("Not a refresh token")
            
            device_id = payload["sub"]
            
            # Create new access token
            access_token = self.create_token(device_id)
            
            self.logger.info(f"Created access token from refresh token for device {device_id}")
            return access_token
            
        except Exception as e:
            self.logger.error(f"Refresh token validation failed: {e}")
            raise
    
    def get_token_info(self, token: str) -> Dict[str, Any]:
        """Get token information without verification (for debugging)"""
        try:
            # Decode without verification to get claims
            payload = jwt.decode(token, options={"verify_signature": False})
            
            return {
                "device_id": payload.get("sub"),
                "device_type": payload.get("device_type"),
                "token_type": payload.get("token_type"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "issuer": payload.get("iss"),
                "audience": payload.get("aud"),
                "is_blacklisted": token in self.blacklisted_tokens
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get token info: {e}")
            return {}
    
    def cleanup_blacklist(self):
        """Clean up expired tokens from blacklist"""
        current_time = int(time.time())
        tokens_to_remove = []
        
        for token in self.blacklisted_tokens:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                if payload.get("exp", 0) < current_time:
                    tokens_to_remove.append(token)
            except:
                # If we can't decode, remove it
                tokens_to_remove.append(token)
        
        for token in tokens_to_remove:
            self.blacklisted_tokens.discard(token)
        
        if tokens_to_remove:
            self.logger.info(f"Cleaned up {len(tokens_to_remove)} expired tokens from blacklist")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        return {
            "algorithm": self.algorithm,
            "default_expiration": self.default_expiration,
            "blacklisted_tokens": len(self.blacklisted_tokens),
            "secret_key_length": len(self.secret_key)
        }
