from uuid import UUID
from sqlalchemy.dialects import postgresql
from sqlalchemy import String, ForeignKey, Text, JSON, Index
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base
from app.infrastructure.db.mixins import IDMixin, TimestampMixin, TenantMixin

class AuditLog(Base, IDMixin, TimestampMixin, TenantMixin):
    """
    Centralized audit trail for all significant system changes.
    """
    __tablename__ = "audit_logs"

    # Who performed the action
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # What was done (e.g., 'user:update', 'role:delete', 'otp:request')
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # What resource was affected
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Metadata for forensic analysis
    ip_address: Mapped[str] = mapped_column(postgresql.INET, nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    
    # The 'Before' and 'After' states or general metadata
    # Use JSONB for fast searching in PostgreSQL
    payload: Mapped[dict] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_audit_logs_actor_id", "actor_id"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_action", "action"),
    )