from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

# Generate Migration: docker-compose exec api alembic revision --autogenerate -m "add_new_field in roles as is_active"

# Apply Migration: docker-compose exec api alembic upgrade head