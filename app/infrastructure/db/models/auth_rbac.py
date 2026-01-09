from uuid import UUID
from sqlalchemy import String, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.db.base import Base
from app.infrastructure.db.mixins import IDMixin, TimestampMixin, TenantMixin

class Permission(Base, IDMixin, TimestampMixin):
    """
    Defines unique system actions. 
    Examples: 'users:view', 'users:edit', 'billing:manage'
    """
    __tablename__ = "permissions"

    # The 'slug' is the unique identifier used in code checks
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )

    __table_args__ = (
        Index("ix_permissions_slug", "slug"),
    )

class Role(Base, IDMixin, TimestampMixin, TenantMixin):
    """
    Groups permissions together. 
    tenant_id is NULL for Global Roles (System Admin) 
    and set for Tenant-specific roles.
    """
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(default=False)

    # Relationships
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary="role_permissions", back_populates="roles"
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="role")

    __table_args__ = (
        UniqueConstraint("name", "tenant_id", name="uq_role_name_per_tenant"),
    )

class RolePermission(Base):
    """Association table for Many-to-Many Role <-> Permission relationship."""
    __tablename__ = "role_permissions"

    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[UUID] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)