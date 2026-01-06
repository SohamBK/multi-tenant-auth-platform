from enum import Enum

class AuthMethodType(str, Enum):
    PASSWORD = "password"
    OAUTH_GOOGLE = "google"
    OAUTH_GITHUB = "github"
    OTP = "otp"
    MAGIC_LINK = "magic_link"

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"

class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"