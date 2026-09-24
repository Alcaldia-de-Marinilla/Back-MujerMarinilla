from datetime import datetime
from typing import ClassVar

from pydantic import Field

from app.schemas.base import CamelModel, PartialUpdateModel


class ReferralBase(CamelModel):
    code: str = Field(min_length=1, max_length=50)
    header: str = Field(min_length=1)
    text: str = Field(min_length=1)
    image: str | None = None
    name: str | None = None
    violence_type_id: int


class ReferralCreate(ReferralBase):
    """Body esperado en POST y PUT (recurso completo)."""
    pass


class ReferralUpdate(PartialUpdateModel):
    """PATCH: actualizacion parcial. `code` no se puede editar (D1)."""
    non_nullable_fields: ClassVar[set[str]] = {"header", "text", "violence_type_id"}

    header: str | None = Field(default=None, min_length=1)
    text: str | None = Field(default=None, min_length=1)
    image: str | None = None
    name: str | None = None
    violence_type_id: int | None = None


class ReferralOut(ReferralBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
