import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import INET

from app.infrastructure.db.base import Base
from app.infrastructure.db.mixins import IDMixin, TimestampMixin, TenantMixin

class LoginAttempt(Base, IDMixin, TimestampMixin, TenantMixin):
    """
    Audit log for tracking authentication attempts.
    Used for security monitoring and rate limiting.
    """
    __tablename__ = "login_attempts"

    # We use the raw email because the attempt might be for a user that doesn't exist
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Track the outcome
    is_successful: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Which method was tried?
    auth_method: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., 'password', 'google'

    # Request metadata for identifying attackers
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # If successful, link to the user
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<LoginAttempt(email={self.email}, success={self.is_successful})>"