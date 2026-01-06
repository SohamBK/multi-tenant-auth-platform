import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base
from app.infrastructure.db.mixins import IDMixin, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from .user import User

class RefreshToken(Base, IDMixin, TimestampMixin, TenantMixin):
    """
    Manages long-lived sessions and supports token rotation.
    Includes tenant_id for high-speed tenant-wide revocation.
    """
    __tablename__ = "refresh_tokens"

    # Table arguments for performance and lookup
    __table_args__ = (
        Index("ix_refresh_tokens_token_hash", "token_hash"),
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_tenant_id", "tenant_id"),
    )

    # --- Identity & Ownership ---
    # CASCADE: If a user is deleted, all their sessions are automatically invalidated.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # --- Token Data ---
    # Store a SHA-256 hash of the refresh token. Never store raw tokens in the DB.
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # --- Lifecycle & Security ---
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # --- Token Rotation (Replay Detection) ---
    # When a token is refreshed, the old token's ID is linked to the new token's ID.
    # If a token with a 'replaced_by' value is ever used again, it's a security alert.
    replaced_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"), 
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(user_id={self.user_id}, active={self.revoked_at is None})>"