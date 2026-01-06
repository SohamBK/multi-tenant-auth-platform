import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from app.core.config import settings

# JWT Best Practices:
# 1. Short-lived Access Tokens (security)
# 2. Longer-lived Refresh Tokens (UX)
# 3. RS256 Algorithm (Asymmetric security)

def create_jwt_token(
    subject: str,
    tenant_id: Optional[uuid.UUID],
    is_superuser: bool,
    expires_delta: timedelta,
    token_type: str = "access"
) -> str:
    """
    Generates a signed RS256 JWT.
    Bakes the tenant context and identity into the claims.
    """
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    payload = {
        "sub": str(subject),          # User ID
        "tenant_id": str(tenant_id) if tenant_id else None,
        "is_superuser": is_superuser,
        "type": token_type,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),     # Unique token ID to prevent replay
    }
    
    # settings.PRIVATE_KEY must be the multi-line PEM string
    encoded_jwt = jwt.encode(
        payload, 
        settings.PRIVATE_KEY, 
        algorithm="RS256"
    )
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a token using the Public Key.
    """
    return jwt.decode(
        token, 
        settings.PUBLIC_KEY, 
        algorithms=["RS256"]
    )