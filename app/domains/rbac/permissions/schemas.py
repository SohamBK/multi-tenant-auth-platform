from pydantic import BaseModel
from uuid import UUID


class PermissionSchema(BaseModel):
    id: UUID
    slug: str
    description: str | None = None

    class Config:
        from_attributes = True
