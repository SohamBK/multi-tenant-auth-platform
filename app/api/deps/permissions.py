from fastapi import Depends, HTTPException, status
from app.api.deps.auth import get_current_user
from app.security.permissions import has_permission

class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(self, current_user=Depends(get_current_user)) -> None:
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned role",
            )

        permissions = [p.slug for p in current_user.role.permissions]

        if not has_permission(permissions, self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {self.required_permission}",
            )
