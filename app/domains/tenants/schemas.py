from pydantic import BaseModel, Field
from uuid import UUID
from pydantic import ConfigDict

class TenantCreateSchema(BaseModel):
    name: str = Field(..., min_length=5, max_length=255)

class TenantResponseSchema(BaseModel):
    id: UUID
    name: str
    tenant_status: str

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )
