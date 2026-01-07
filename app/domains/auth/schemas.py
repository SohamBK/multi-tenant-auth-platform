from pydantic import BaseModel, EmailStr, Field
class LoginRequest(BaseModel):
    """Schema for user login request."""
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., min_length=8, example="strong_password_123")

class TokenResponse(BaseModel):
    """Schema for successful authentication response."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

class RefreshRequest(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")