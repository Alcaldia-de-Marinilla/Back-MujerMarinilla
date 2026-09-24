from datetime import datetime
from typing import ClassVar

from pydantic import Field

from app.schemas.base import CamelModel, PartialUpdateModel


class PhoneBase(CamelModel):
    code: str = Field(min_length=1, max_length=50)
    number: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None


class PhoneCreate(PhoneBase):
    """Body esperado en POST y PUT /api/v1/phones (recurso completo)."""
    pass


class PhoneUpdate(PartialUpdateModel):
    """
    Body esperado en PATCH (actualizacion parcial).
    `code` NO se puede editar (D1); si hace falta cambiarlo, se borra y se crea de nuevo.
    """
    non_nullable_fields: ClassVar[set[str]] = {"number", "title"}

    number: str | None = Field(default=None, min_length=1)
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None


class PhoneOut(PhoneBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
