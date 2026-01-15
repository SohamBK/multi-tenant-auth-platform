import uuid
from datetime import datetime
import uuid_utils
from sqlalchemy import DateTime, ForeignKey, func, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr

def uuid7_uuid() -> uuid.UUID:
    """
    Generate a UUIDv7 but return a standard uuid.UUID instance
    for compatibility with Pydantic and typing.
    """
    return uuid.UUID(str(uuid_utils.uuid7()))

class IDMixin:
    """Mixin to add a UUIDv7 primary key."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7_uuid,
        unique=True,
        nullable=False,
    )

class TimestampMixin:
    """Mixin for record lifecycle tracking using UTC."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

class TenantMixin:
    """Mixin for multi-tenant isolation."""
    @declared_attr
    def tenant_id(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(
            UUID(as_uuid=True), 
            # We use RESTRICT to prevent deleting a tenant with active data
            ForeignKey("tenants.id", ondelete="RESTRICT"), 
            nullable=True, 
            index=True
        )