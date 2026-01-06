from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db
from app.domains.auth.schemas import LoginRequest, TokenResponse
from app.domains.auth.service import AuthService
from app.domains.users.repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency provider for AuthService."""
    user_repo = UserRepository(session)
    return AuthService(user_repo)

@router.post("/login", response_model=TokenResponse)
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

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )