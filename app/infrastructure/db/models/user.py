import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base
from app.infrastructure.db.mixins import IDMixin, TimestampMixin, TenantMixin
from app.infrastructure.db.enums import UserStatus

# Prevents circular imports for Type Hinting
if TYPE_CHECKING:
    from .tenant import Tenant
    from .user_credentials import UserCredentials
    from .refresh_token import RefreshToken

class User(Base, IDMixin, TimestampMixin, TenantMixin):
    """
    Represents a user identity.
    Email is unique globally, not just per tenant.
    """
    __tablename__ = "users"

    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_is_active", "user_status"),
    )

    # Global Email Uniqueness: No two users in the entire system can have the same email.
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # user status
    user_status: Mapped[UserStatus] = mapped_column(String(50), default=UserStatus.ACTIVE.value, nullable=False)
    
    # Super Admin Provision: 
    # If True, this user can bypass tenant filters in the repository/service layer.
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    tenant: Mapped[Optional["Tenant"]] = relationship(
        "Tenant", 
        back_populates="users"
    )

    # Credential management (Sensitive data separated)
    # ondelete="CASCADE" is handled in the child model
    credentials: Mapped["UserCredentials"] = relationship(
        "UserCredentials", 
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan" # If User is deleted, delete their password hash
    )

    # Session management
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", 
        back_populates="user",
        cascade="all, delete-orphan" # If User is deleted, revoke all sessions
    )

    def __repr__(self) -> str:
        return f"<User(email={self.email}, is_superuser={self.is_superuser})>"