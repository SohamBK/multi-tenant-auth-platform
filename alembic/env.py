import sys
from pathlib import Path
from logging.config import fileConfig
import asyncio

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

from app.core.config import settings

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.tenant import Tenant
from app.infrastructure.db.models.refresh_token import RefreshToken
from app.infrastructure.db.models.user_auth_method import UserAuthMethod
from app.infrastructure.db.models.login_attempt import LoginAttempt

# --- Ensure project root on PYTHONPATH ---
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.core.config import settings
from app.infrastructure.db.base import Base

# Alembic Config
config = context.config

# 2. Dynamically set the sqlalchemy.url from your .env/settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    async def run_async_migrations():
        engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=pool.NullPool,
        )

        async with engine.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await engine.dispose()

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
