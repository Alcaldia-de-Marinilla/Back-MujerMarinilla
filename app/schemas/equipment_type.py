from datetime import datetime
from typing import ClassVar

from pydantic import Field

from app.schemas.base import CamelModel, PartialUpdateModel


class EquipmentTypeBase(CamelModel):
    abbreviation: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1)
    description: str | None = None


class EquipmentTypeCreate(EquipmentTypeBase):
    """Body esperado en POST y PUT (recurso completo)."""
    pass


class EquipmentTypeUpdate(PartialUpdateModel):
    non_nullable_fields: ClassVar[set[str]] = {"abbreviation", "name"}

    abbreviation: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None


class EquipmentTypeOut(EquipmentTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
