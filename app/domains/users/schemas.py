from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from app.infrastructure.db.enums import UserStatus

class UserSchema(BaseModel):
    """Standard public representation of a User."""
    id: UUID
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    tenant_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)

class UserCreateSchema(BaseModel):
    """Schema for creating a new User."""
    email: EmailStr
    first_name: str
    last_name: str
    role_id: UUID
    tenant_id: Optional[UUID] = None

class UserUpdateSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_id: Optional[UUID] = None
    user_status: Optional[UserStatus] = None

class UserFilterParams(BaseModel):
    email: Optional[str] = None
    user_status: Optional[UserStatus] = None
    role_id: Optional[UUID] = None

class UserRoleAssignSchema(BaseModel):
    role_id: UUID


class UserMeSchema(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]

    tenant_id: Optional[UUID]
    tenant_name: Optional[str]

    role_id: UUID
    role_name: str

    permissions: List[str]

    class Config:
        from_attributes = True