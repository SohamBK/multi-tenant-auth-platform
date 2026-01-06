import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from app.security.hashing import verify_password
from app.security.tokens import create_jwt_token
from app.domains.users.repository import UserRepository
from app.infrastructure.db.models.refresh_token import RefreshToken
from app.infrastructure.db.models.login_attempt import LoginAttempt
from app.core.config import settings
from app.core.exceptions import AuthenticationError, InvalidCredentials

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate_user(
        self, 
        email: str, 
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        The core login flow.
        1. Find user by email.
        2. Verify password.
        3. Check account/tenant status.
        4. Log the attempt.
        5. Return Access and Refresh tokens.
        """
        user = await self.user_repo.get_by_email(email)
        
        # 1. & 2. Verify existence and password
        # We use a single check to prevent 'User Enumeration' attacks
        is_valid = False
        if user and user.auth_methods:
            # Find the password auth method
            pwd_method = next((m for m in user.auth_methods if m.auth_type == "password"), None)
            if pwd_method and pwd_method.password_hash:
                is_valid = verify_password(password, pwd_method.password_hash)

        # 3. Security Audit Logging
        await self._create_login_attempt(
            email=email,
            is_successful=is_valid and user is not None,
            tenant_id=user.tenant_id if user else None,
            user_id=user.id if user else None,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not is_valid or not user:
            raise InvalidCredentials()

        # 4. Status Checks
        if not user.user_status == "active" or (user.tenant and not user.tenant.tenant_status == "active"):
            raise AuthenticationError("Account or Organization is inactive")

        # 5. Token Generation
        access_token = create_jwt_token(
            subject=user.id,
            tenant_id=user.tenant_id,
            is_superuser=user.is_superuser,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = await self._issue_refresh_token(user)

        return access_token, refresh_token

    async def _issue_refresh_token(self, user) -> str:
        """Creates and stores a rotating refresh token."""
        # Note: In a real app, you'd hash the token before storing
        token_str = str(uuid.uuid4())
        
        new_token = RefreshToken(
            user_id=user.id,
            tenant_id=user.tenant_id,
            token_hash=token_str, # Simplification: use a hash in production
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        self.user_repo.session.add(new_token)
        await self.user_repo.session.flush()
        
        return token_str

    async def _create_login_attempt(self, **kwargs):
        """Internal helper to log all attempts."""
        attempt = LoginAttempt(auth_method="password", **kwargs)
        self.user_repo.session.add(attempt)
        await self.user_repo.session.flush()