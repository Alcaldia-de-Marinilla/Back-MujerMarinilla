from datetime import datetime
from typing import ClassVar

from pydantic import Field

from app.schemas.base import CamelModel, PartialUpdateModel


class ViolenceTypeBase(CamelModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1)
    description: str | None = None
    examples: list[str] | None = None
    image: str | None = None


class ViolenceTypeCreate(ViolenceTypeBase):
    """Body esperado en POST y PUT (recurso completo)."""
    pass


class ViolenceTypeUpdate(PartialUpdateModel):
    """PATCH: actualizacion parcial. `code` no se puede editar (D1)."""
    non_nullable_fields: ClassVar[set[str]] = {"name"}

    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    examples: list[str] | None = None
    image: str | None = None


class ViolenceTypeOut(ViolenceTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
