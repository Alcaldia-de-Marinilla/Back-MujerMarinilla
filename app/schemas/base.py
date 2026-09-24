"""
CamelModel: todos los schemas heredan de aqui.

RF11 pide que la API responda en camelCase igual que las interfaces
TypeScript del frontend, mientras que en la BD usamos snake_case (mas
idiomatico en SQL/Postgres). alias_generator hace la conversion
automatica en ambos sentidos sin duplicar nombres de campo a mano.
"""
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,   # acepta tanto snake_case como camelCase de entrada
        from_attributes=True,    # permite construir el schema desde el modelo SQLAlchemy
    )


class PartialUpdateModel(CamelModel):
    """
    Base para los schemas de PATCH (actualizacion parcial).

    Corrige el error confirmado en la revision del 16 de sept: antes,
    mandar {"name": null} en un campo NOT NULL de la BD pasaba la
    validacion de Pydantic (el tipo era `str | None`), llegaba hasta
    SQLAlchemy, y la base de datos rechazaba el UPDATE con un
    IntegrityError sin capturar -> 500. Ahora se distingue entre
    "el campo no vino en el body" (permitido, se ignora) y "el campo
    vino explicitamente como null" (rechazado con 422 si ese campo es
    obligatorio en la BD).

    Cada subclase declara `non_nullable_fields`: el conjunto de nombres
    de campo (en snake_case, el nombre Python del atributo) que son
    NOT NULL en la base de datos.
    """
    non_nullable_fields: ClassVar[set[str]] = set()

    @model_validator(mode="after")
    def _reject_explicit_nulls_on_required_fields(self):
        for field_name in self.non_nullable_fields:
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                camel = self.model_config.get("alias_generator")
                api_name = camel(field_name) if camel else field_name
                raise ValueError(f"'{api_name}' no puede ser null")
        return self
