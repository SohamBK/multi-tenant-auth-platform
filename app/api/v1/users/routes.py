from app.api.deps.auth import get_current_user
from app.domains.users.schemas import UserSchema
from app.core.responses import SuccessResponse

from fastapi import APIRouter, Depends
from app.infrastructure.db.models.user import User

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