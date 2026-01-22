from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional

from app.domains.rbac.permissions.schemas import PermissionSchema


class RoleSchema(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    tenant_id: Optional[UUID]
    is_system_role: bool
    is_active: Optional[bool]
    permissions: List[PermissionSchema]

    class Config:
        from_attributes = True

class RoleCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = None

    tenant_id: Optional[UUID] = None  # only super admin can set
    permission_ids: List[UUID]

class RoleUpdateSchema(BaseModel):
    name: Optional[str] = Field(min_length=2, max_length=100)
    description: Optional[str] = None

class RolePermissionAttachSchema(BaseModel):
    permission_ids: List[UUID]