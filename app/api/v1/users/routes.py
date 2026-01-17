from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db
from app.api.deps.auth import get_current_user
from app.infrastructure.db.models.user import User
from app.api.deps.permissions import PermissionChecker

from app.domains.users.schemas import UserCreateSchema, UserSchema
from app.domains.users.repository import UserRepository
from app.domains.users.service import UserService

from app.domains.audit.repository import AuditLogRepository
from app.domains.audit.service import AuditService
from app.domains.audit.schemas import AuditLogCreate

from app.core.responses import SuccessResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=SuccessResponse[UserSchema])
async def read_user_me(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the profile of the currently authenticated user.
    Uses UserSchema for secure, automated serialization.
    """
    return SuccessResponse(
        data=UserSchema.model_validate(current_user),
        message="User profile retrieved"
    )

@router.post(
    "/",
    response_model=SuccessResponse[UserSchema],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("users:create"))],
)
async def create_user(
    payload: UserCreateSchema,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = UserService(UserRepository(session))
    user = await service.create_user(
        data=payload,
        actor=current_user,
    )

    # Audit
    audit = AuditService(AuditLogRepository(session))
    await audit.log_action(
        tenant_id=user.tenant_id or current_user.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="users.create",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload={
                "email": user.email,
                "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            },
        ),
    )

    return SuccessResponse(
        data=UserSchema.model_validate(user),
        message="User created successfully",
    )
