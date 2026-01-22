from uuid import UUID
from datetime import datetime

from app.domains.audit.repository import AuditLogRepository
from app.domains.audit.schemas import AuditLogCreate


def _json_safe(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    return value

class AuditService:
    def __init__(self, audit_repo: AuditLogRepository):
        self.audit_repo = audit_repo

    async def log_action(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID | None,
        data: AuditLogCreate,
    ) -> None:
        
        payload = _json_safe(data.payload) if data.payload else None

        await self.audit_repo.create(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=data.action,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            payload=payload,
        )
