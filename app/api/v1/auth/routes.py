from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db
from app.domains.auth.schemas import LoginRequest, TokenResponse, RefreshRequest
from app.core.responses import SuccessResponse
from app.domains.auth.service import AuthService
from app.domains.users.repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency provider for AuthService."""
    user_repo = UserRepository(session)
    return AuthService(user_repo)

@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Standard Login Endpoint.
    Handles authentication, audit logging, and token issuance.
    """
    # Extract metadata for audit logging
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    access_token, refresh_token = await auth_service.authenticate_user(
        email=login_data.email,
        password=login_data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return SuccessResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        ),
        message="Login successful"
    )

@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh_token(
    refresh_data: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Exchanges a Refresh Token for a new Access/Refresh pair.
    """
    access_token, refresh_token = await auth_service.refresh_access_token(
        refresh_token_str=refresh_data.refresh_token
    )

    return SuccessResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        ),
        message="Token refreshed successfully"
    )

@router.post("/logout", response_model=SuccessResponse[None])
async def logout(
    refresh_data: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logs out a user by revoking the provided Refresh Token.
    """
    await auth_service.revoke_refresh_token(
        refresh_token_str=refresh_data.refresh_token
    )

    return SuccessResponse(
        data=None,
        message="Logout successful"
    )