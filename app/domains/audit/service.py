from uuid import UUID
from app.domains.audit.repository import AuditLogRepository
from app.domains.audit.schemas import AuditLogCreate


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
        await self.audit_repo.create(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=data.action,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            payload=data.payload,
        )
