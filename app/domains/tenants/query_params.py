from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.domains.shared.schemas.pagination import PaginationParams

class TenantListParams(PaginationParams):
    status: Optional[Literal["active", "inactive"]] = None
    sort_by: Literal["created_at", "name"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
