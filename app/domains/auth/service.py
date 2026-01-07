import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from app.security.hashing import verify_password
from app.security.tokens import create_jwt_token
from app.domains.users.repository import UserRepository
from app.domains.auth.otp_repository import OTPRepository
from app.infrastructure.db.models.refresh_token import RefreshToken
from app.infrastructure.db.models.login_attempt import LoginAttempt
from app.core.config import settings
from app.core.exceptions import AuthenticationError, InvalidCredentials
from sqlalchemy import select, update

from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

class AuthService:
    def __init__(self, user_repo: UserRepository, otp_repo: OTPRepository):
            self.user_repo = user_repo
            self.otp_repo = otp_repo

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
    
    async def refresh_access_token(
        self, 
        refresh_token_str: str
    ) -> Tuple[str, str]:
        """
        Validates a refresh token and issues a new pair (Access + Refresh).
        Implements token rotation and replay detection.
        """
        # 1. Find the token in the database
        # In production, you would hash the incoming string before querying
        query = select(RefreshToken).where(RefreshToken.token_hash == refresh_token_str)
        result = await self.user_repo.session.execute(query)
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise InvalidCredentials("Invalid refresh token")

        # 2. Security Check: Replay Detection
        if db_token.revoked_at or db_token.replaced_by:
            # Potential attack: Revoke ALL tokens for this user for safety
            await self._revoke_all_user_tokens(db_token.user_id)
            raise AuthenticationError("Security alert: Refresh token has already been used")

        if db_token.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token has expired")

        # 3. Fetch the user (ensure they are still active)
        user = await self.user_repo.get_by_id(db_token.user_id)
        if not user or user.user_status != "active":
            raise AuthenticationError("User is inactive or not found")

        # 4. Generate New Tokens
        new_access_token = create_jwt_token(
            subject=user.id,
            tenant_id=user.tenant_id,
            is_superuser=user.is_superuser,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # 5. Rotate: Issue new refresh token and link the old one
        new_refresh_str = await self._issue_refresh_token(user)
        
        # Update old token metadata
        db_token.revoked_at = datetime.now(timezone.utc)
        # Note: You'll need the ID of the new token to set replaced_by
        # This requires looking up the token we just created in _issue_refresh_token
        
        await self.user_repo.session.commit()

        return new_access_token, new_refresh_str
    
    async def logout(self, refresh_token_str: str):
        """
        Revokes a specific refresh token to end a session.
        """
        # 1. Find the token
        query = select(RefreshToken).where(RefreshToken.token_hash == refresh_token_str)
        result = await self.user_repo.session.execute(query)
        db_token = result.scalar_one_or_none()

        if not db_token:
            return

        db_token.revoked_at = datetime.now(timezone.utc)
        await self.user_repo.session.commit()

    async def _revoke_all_user_tokens(self, user_id: uuid.UUID):
        """Safety mechanism for suspected breaches."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.user_repo.session.execute(stmt)
        await self.user_repo.session.commit()

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

    async def revoke_refresh_token(self, refresh_token_str: str):
        """
        Revokes a specific refresh token to end a session.
        Matches the call in the API route.
        """
        # 1. Find the token
        query = select(RefreshToken).where(RefreshToken.token_hash == refresh_token_str)
        result = await self.user_repo.session.execute(query)
        db_token = result.scalar_one_or_none()

        if not db_token:
            # If the token doesn't exist, the session is already invalid
            return

        # 2. Mark as revoked
        db_token.revoked_at = datetime.now(timezone.utc)
        
        # 3. Commit the change
        await self.user_repo.session.commit()

    async def request_otp(self, email: str) -> None:
        """Generates, stores, and logs an OTP."""
        # 1. Check if user exists (Standard security: still 'succeed' if user doesn't exist)
        user = await self.user_repo.get_by_email(email)
        
        # 2. Generate a secure 6-digit OTP
        otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # 3. Store in Redis
        await self.otp_repo.store_otp(email, otp)
        
        # 4. Console Logging (Instead of Email/SMS)
        print(f"\n[SECURITY] OTP for {email}: {otp} (Expires in 5m)\n")
        logger.info(f"OTP generated for {email}")

    async def verify_otp_login(self, email: str, otp: str) -> Tuple[str, str]:
        """Verifies OTP and returns JWT tokens with full payload."""
        # 1. Fetch OTP from Redis
        stored_otp = await self.otp_repo.get_otp(email)
        
        if not stored_otp or stored_otp != otp:
            raise InvalidCredentials("Invalid or expired OTP")

        # 2. OTP is valid, fetch user
        user = await self.user_repo.get_by_email(email)
        if not user or user.user_status != "active":
            raise AuthenticationError("User not found or inactive")

        # 3. Consume OTP (Delete so it can't be used twice)
        await self.otp_repo.delete_otp(email)

        # 4. Standard Token Issuance
        # ✅ FIX: Pass is_superuser and expires_delta
        access_token = create_jwt_token(
            subject=user.id, 
            tenant_id=user.tenant_id,
            is_superuser=user.is_superuser,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = await self._issue_refresh_token(user)

        return access_token, refresh_token