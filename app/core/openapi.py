from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI) -> dict:
    """
    Custom OpenAPI schema for the application.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Multi-Tenant Auth & Authorization Platform",
        version="1.0.0",
        description=(
            "Production-grade Authentication and Authorization service.\n\n"
            "Features:\n"
            "- Multi-tenant isolation\n"
            "- JWT-based authentication\n"
            "- RBAC authorization\n"
            "- Token rotation & revocation\n"
        ),
        routes=app.routes,
    )

    # ✅ Ensure components exists
    openapi_schema.setdefault("components", {})
    openapi_schema["components"].setdefault("securitySchemes", {})

    # ✅ Add JWT security scheme
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    # ✅ Apply globally
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema
