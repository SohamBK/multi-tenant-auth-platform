from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.shared.repository import BaseRepository
from app.infrastructure.db.models.audit import AuditLog
from uuid import UUID


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def create(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
        payload: dict | None,
    ) -> AuditLog:
        audit_log = AuditLog(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            payload=payload,
        )

        self.session.add(audit_log)
        await self.session.flush()  # 🔴 NO commit here
        return audit_log
