import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base
from app.infrastructure.db.mixins import IDMixin, TimestampMixin
from app.infrastructure.db.enums import TenantStatus

# Prevents circular imports at runtime
if TYPE_CHECKING:
    from .user import User

class Tenant(Base, IDMixin, TimestampMixin):
    """
    Represents a SaaS organization. 
    The root level of data isolation in the system.
    """
    __tablename__ = "tenants"

    # Table arguments for performance and integrity
    __table_args__ = (
        UniqueConstraint("name", name="uq_tenant_name"),
        Index("ix_tenants_is_active", "tenant_status"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_status: Mapped[TenantStatus] = mapped_column(String(50), default=TenantStatus.ACTIVE.value, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", 
        back_populates="tenant",
        passive_deletes=True 
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"