from pydantic import BaseModel, Field
from typing import Generic, List, TypeVar
from math import ceil

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Query parameters:
        ?page=1&page_size=10
    """
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def create(cls, *, page: int, page_size: int, total_items: int) -> "PaginationMeta":
        total_pages = ceil(total_items / page_size) if page_size else 0

        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )


class PaginatedData(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationMeta
