from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict


class AuditLogCreate(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    payload: Optional[Dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
