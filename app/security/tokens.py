import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt

from app.core.config import settings


def create_jwt_token(
    subject: str,
    tenant_id: Optional[uuid.UUID],
    expires_delta: timedelta,
    token_type: str = "access",
) -> str:
    """
    Generates a signed RS256 JWT.
    Encodes identity and tenant scope.
    Authority is resolved dynamically via RBAC.
    """
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(subject),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "type": token_type,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }

    return jwt.encode(
        payload,
        settings.PRIVATE_KEY,
        algorithm="RS256",
    )


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT using the public key.
    Raises jwt exceptions if invalid or expired.
    """
    return jwt.decode(
        token,
        settings.PUBLIC_KEY,
        algorithms=["RS256"],
    )
