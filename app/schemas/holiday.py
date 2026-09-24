"""
Nota tecnica: el campo se llama igual que su tipo (`date: date`), lo
cual choca con como Pydantic v2 resuelve las anotaciones de tipo. Por
eso importamos el modulo completo como `dt` y usamos `dt.date`.
"""
import datetime as dt
from typing import ClassVar

from pydantic import Field

from app.schemas.base import CamelModel, PartialUpdateModel


class HolidayBase(CamelModel):
    date: dt.date
    name: str = Field(min_length=1)


class HolidayCreate(HolidayBase):
    """Body esperado en POST y PUT (recurso completo)."""
    pass


class HolidayUpdate(PartialUpdateModel):
    non_nullable_fields: ClassVar[set[str]] = {"date", "name"}

    date: dt.date | None = None
    name: str | None = Field(default=None, min_length=1)


class HolidayOut(HolidayBase):
    id: int
    created_at: dt.datetime
    updated_at: dt.datetime | None = None
