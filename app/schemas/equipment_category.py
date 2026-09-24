"""
D5 (revision del 16 de sept): antes equipment_categories no tenia
endpoints propios. Mismo patron que equipment_type.py.
"""
from datetime import datetime
from typing import ClassVar

from pydantic import Field

from app.schemas.base import CamelModel, PartialUpdateModel


class EquipmentCategoryBase(CamelModel):
    slug: str = Field(min_length=1, max_length=50)
    label: str = Field(min_length=1)
    display_order: int = 0


class EquipmentCategoryCreate(EquipmentCategoryBase):
    """Body esperado en POST y PUT (recurso completo)."""
    pass


class EquipmentCategoryUpdate(PartialUpdateModel):
    non_nullable_fields: ClassVar[set[str]] = {"slug", "label", "display_order"}

    slug: str | None = Field(default=None, min_length=1, max_length=50)
    label: str | None = Field(default=None, min_length=1)
    display_order: int | None = None


class EquipmentCategoryOut(EquipmentCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
