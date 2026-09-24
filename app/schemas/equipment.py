"""
Equipment es la entidad mas compleja del dominio.

PUT vs PATCH (corrige un error confirmado: "PUT hoy funciona igual que
PATCH"): EquipmentCreate se usa para POST *y* PUT -> un PUT exige todos
los campos obligatorios del recurso completo (categoryId, name), y falla
con 422 si falta alguno. EquipmentUpdate es solo para PATCH: todos los
campos son opcionales, pero si un campo obligatorio en la BD llega
explicitamente como null, se rechaza con 422.

phones/workingDates/violenceTypeIds duplicados se deduplican
automaticamente en vez de fallar con un error de base de datos.
"""
from datetime import date, datetime, time
from typing import ClassVar

from pydantic import Field, field_validator

from app.schemas.base import CamelModel, PartialUpdateModel


def _dedupe(values: list | None) -> list | None:
    """Quita duplicados preservando el orden (corrige 500 por UNIQUE constraint)."""
    if values is None:
        return None
    seen = set()
    result = []
    for v in values:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


class EquipmentOut(CamelModel):
    id: int
    equipment_type: str
    equipment_category_slug: str | None = None
    type: str | None = None
    name: str
    abbreviation: str | None = None
    opening_time: time | None = None
    closing_time: time | None = None
    phones: list[str] = []
    description: str | None = None
    function: str | None = None
    violence_types: list[str] = []
    address: str | None = None
    neighborhood: str | None = None
    notes: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    opening_time_saturday: time | None = None
    closing_time_saturday: time | None = None
    opening_time_sunday: time | None = None
    closing_time_sunday: time | None = None
    working_dates: list[date] = []
    open_24h: bool = Field(alias="open24")
    created_at: datetime
    updated_at: datetime | None = None


class EquipmentCreate(CamelModel):
    """Body esperado en POST y PUT (recurso completo: exige categoryId y name)."""
    category_id: int
    unit_type_id: int | None = None
    name: str = Field(min_length=1)
    abbreviation: str | None = None
    description: str | None = None
    function: str | None = None
    address: str | None = None
    neighborhood: str | None = None
    notes: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    opening_time: time | None = None
    closing_time: time | None = None
    opening_time_saturday: time | None = None
    closing_time_saturday: time | None = None
    opening_time_sunday: time | None = None
    closing_time_sunday: time | None = None
    open_24h: bool = Field(default=False, alias="open24")
    phones: list[str] = []
    working_dates: list[date] = []
    violence_type_ids: list[int] = []

    @field_validator("phones", "working_dates", "violence_type_ids")
    @classmethod
    def dedupe_lists(cls, value):
        return _dedupe(value) or []


class EquipmentUpdate(PartialUpdateModel):
    """Body esperado en PATCH (actualización parcial)."""
    non_nullable_fields: ClassVar[set[str]] = {"category_id", "name", "open_24h"}

    category_id: int | None = None
    unit_type_id: int | None = None
    name: str | None = Field(default=None, min_length=1)
    abbreviation: str | None = None
    description: str | None = None
    function: str | None = None
    address: str | None = None
    neighborhood: str | None = None
    notes: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    opening_time: time | None = None
    closing_time: time | None = None
    opening_time_saturday: time | None = None
    closing_time_saturday: time | None = None
    opening_time_sunday: time | None = None
    closing_time_sunday: time | None = None
    open_24h: bool | None = Field(default=None, alias="open24")
    phones: list[str] | None = None
    working_dates: list[date] | None = None
    violence_type_ids: list[int] | None = None

    @field_validator("phones", "working_dates", "violence_type_ids")
    @classmethod
    def dedupe_lists(cls, value):
        return _dedupe(value)
