from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps.db import get_db
from app.api.deps.auth import get_current_user
from app.api.deps.permissions import PermissionChecker
from app.core.exceptions import ResourceNotFound

from app.domains.rbac.permissions.repository import PermissionRepository
from app.domains.rbac.permissions.service import PermissionService
from app.domains.rbac.permissions.schemas import PermissionSchema

from app.core.responses import SuccessResponse

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get(
    "/",
    response_model=SuccessResponse[list[PermissionSchema]],
    dependencies=[Depends(PermissionChecker("roles:*"))],  # super admin only
)
async def list_permissions(
    session: AsyncSession = Depends(get_db),
):
    service = PermissionService(PermissionRepository(session))
    permissions = await service.list_permissions()

    return SuccessResponse(
        data=[PermissionSchema.model_validate(p) for p in permissions],
        message="Permissions retrieved successfully",
    )


@router.get(
    "/{permission_id}",
    response_model=SuccessResponse[PermissionSchema],
    dependencies=[Depends(PermissionChecker("roles:*"))],
)
async def get_permission(
    permission_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    service = PermissionService(PermissionRepository(session))
    permission = await service.get_permission(permission_id)

    if not permission:
        raise ResourceNotFound("Permission not found")

    return SuccessResponse(
        data=PermissionSchema.model_validate(permission),
        message="Permission retrieved successfully",
    )
