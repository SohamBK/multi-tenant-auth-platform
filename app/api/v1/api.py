from fastapi import APIRouter
from app.api.v1.health.routes import router as health_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.users.routes import router as users_router
from app.api.v1.tenants.routes import router as tenants_router
from app.api.v1.rbac.permissions.routes import router as permissions_router
from app.api.v1.rbac.roles.routes import router as roles_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(tenants_router)
api_router.include_router(permissions_router)
api_router.include_router(roles_router)