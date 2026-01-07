from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict

class UserSchema(BaseModel):
    """Standard public representation of a User."""
    id: UUID
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    is_superuser: bool
    tenant_id: UUID | None = None

    # This allows Pydantic to read data directly from the SQLAlchemy model
    model_config = ConfigDict(from_attributes=True)