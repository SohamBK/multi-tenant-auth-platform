import uuid
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import String, ForeignKey, Enum, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base
from app.infrastructure.db.mixins import IDMixin, TimestampMixin
from app.infrastructure.db.enums import AuthMethodType

class UserAuthMethod(Base, IDMixin, TimestampMixin):
    """
    Stores various ways a user can authenticate.
    Supports Passwords, OAuth, and MFA/OTP.
    """
    __tablename__ = "user_auth_methods"

    __table_args__ = (
        UniqueConstraint("user_id", "auth_type", name="uq_user_auth_type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    auth_type: Mapped[AuthMethodType] = mapped_column(
        Enum(AuthMethodType), 
        nullable=False,
        index=True
    )

    # --- PASSWORD FIELD ---
    # Nullable because OAuth users won't have a password initially
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- OAUTH FIELDS ---
    # Stores the unique ID from the provider (e.g., Google Sub ID)
    provider_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # --- EXTENSIBLE DATA ---
    # Stores extra metadata (e.g., OAuth scopes, OTP secret, or profile picture URL)
    auth_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="auth_methods")

    def __repr__(self) -> str:
        return f"<UserAuthMethod(user_id={self.user_id}, type={self.auth_type})>"