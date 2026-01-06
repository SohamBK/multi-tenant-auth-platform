from typing import Generic, TypeVar, Type, Optional, Sequence, Any
from uuid import UUID
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID, tenant_id: Optional[UUID] = None) -> Optional[ModelType]:
        """Fetch a single record by ID with strict tenant isolation."""
        query = select(self.model).where(self.model.id == id)
        
        # Enforce tenant isolation if the model has a tenant_id field
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
            
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> ModelType:
        """Create a new record."""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush() # flush ensures the ID is generated without committing
        return instance

    async def list(self, tenant_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """List records with pagination and tenant isolation."""
        query = select(self.model).offset(skip).limit(limit)
        
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
            
        result = await self.session.execute(query)
        return result.scalars().all()