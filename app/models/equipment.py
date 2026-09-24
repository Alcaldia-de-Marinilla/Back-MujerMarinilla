"""
Unidad / Equipamiento y sus campos de lista.

Decisión de modelado (tal como pide HU-01): los campos de lista del
frontend (phones[], workingDates[]) se llevan a TABLAS RELACIONADAS
(equipment_phones, equipment_working_dates) en vez de columnas JSON.
Se justifica así:
  - phones: cada unidad puede tener 0..N teléfonos, sin estructura
    interna adicional -> una tabla hija 1:N es más consultable y
    normalizada que un array JSON (permite indexar, validar, contar).
  - workingDates: fechas puntuales de atención -> mismo razonamiento,
    y facilita filtrar "unidades abiertas en fecha X" con SQL normal.
  - violenceTypes: es una relación N:M real con la tabla violence_types
    (una unidad atiende varios tipos de violencia y un tipo de violencia
    lo atienden varias unidades) -> tabla puente equipment_violence_types.

Esto cumple RNF-04 (modelo normalizado y documentado).
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Time,
    Numeric, ForeignKey, UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Equipment(Base):
    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True)
    # RESTRICT: no se puede borrar una categoría mientras tenga unidades asociadas
    # (evita huérfanos "sin categoría", que rompería el filtro equipmentType).
    category_id = Column(Integer, ForeignKey("equipment_categories.id", ondelete="RESTRICT"), nullable=False)
    # SET NULL: el tipo de unidad es opcional (nullable=True), así que si se borra
    # el catálogo la unidad simplemente queda sin tipo fino, no se bloquea el borrado.
    unit_type_id = Column(Integer, ForeignKey("unit_types.id", ondelete="SET NULL"), nullable=True)

    name = Column(String(200), nullable=False)
    abbreviation = Column(String(30), nullable=True)
    description = Column(Text, nullable=True)
    function = Column(Text, nullable=True)
    address = Column(String(255), nullable=True)
    neighborhood = Column(String(120), nullable=True)
    notes = Column(Text, nullable=True)

    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)

    opening_time = Column(Time, nullable=True)
    closing_time = Column(Time, nullable=True)
    opening_time_saturday = Column(Time, nullable=True)
    closing_time_saturday = Column(Time, nullable=True)
    opening_time_sunday = Column(Time, nullable=True)
    closing_time_sunday = Column(Time, nullable=True)
    open_24h = Column(Boolean, nullable=False, default=False)

    is_active = Column(Boolean, nullable=False, default=True)  # soft delete (HU-05: DELETE)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)

    category = relationship("EquipmentCategory", back_populates="equipments")
    unit_type = relationship("UnitType", back_populates="equipments")
    phones = relationship("EquipmentPhone", back_populates="equipment", cascade="all, delete-orphan")
    working_dates = relationship("EquipmentWorkingDate", back_populates="equipment", cascade="all, delete-orphan")
    violence_types = relationship(
        "ViolenceType", secondary="equipment_violence_types", back_populates="equipments"
    )


class EquipmentPhone(Base):
    __tablename__ = "equipment_phones"
    __table_args__ = (
        UniqueConstraint("equipment_id", "phone_number", name="uq_equipment_phone"),
    )

    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id", ondelete="CASCADE"), nullable=False)
    phone_number = Column(String(30), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    equipment = relationship("Equipment", back_populates="phones")


class EquipmentWorkingDate(Base):
    """
    DECISIÓN ABIERTA (punto 04 de la revisión, "no nos corresponde
    tomarla solos"): estas fechas, ¿son EXCEPCIONES en que la unidad
    SÍ abre fuera de su horario normal, o fechas en que CIERRA?
    El frontend original (workingDates?[]) no lo aclara. NO se asume
    ninguna de las dos hasta que se confirme, porque de eso depende el
    cálculo de "abierto ahora" (HU futura, junto con holidays).
    Por ahora la tabla solo registra la fecha; el significado se
    decide antes de programar esa lógica.
    """
    __tablename__ = "equipment_working_dates"
    __table_args__ = (
        UniqueConstraint("equipment_id", "work_date", name="uq_equipment_working_date"),
    )

    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id", ondelete="CASCADE"), nullable=False)
    work_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    equipment = relationship("Equipment", back_populates="working_dates")


class EquipmentViolenceType(Base):
    """
    Tabla puente N:M entre equipments y violence_types.

    DECISIÓN YA TOMADA (punto 2.4 de la revisión, "elegir una opción y
    dejarla escrita"): se implementó la OPCIÓN B (relación N:M contra
    el glosario educativo) en vez de la opción A (columna de texto
    libre). Motivo: es mejor modelo relacional y permite filtrar/unir
    unidades por tipo de violencia atendido.

    ⚠ PENDIENTE: esto cambia el contrato con el frontend (el campo
    `violenceTypes` en la unidad deja de ser un string libre y pasa a
    ser una lista). Falta avisar al equipo de Next.js. Mientras tanto,
    el texto libre original de equipments.ts NO se descarta: el seed
    lo conserva dentro de `notes` (ver app/scripts/seed.py) y esta
    tabla N:M queda vacía hasta que un admin la cure manualmente o se
    defina una regla de conversión automática del texto libre.
    """
    __tablename__ = "equipment_violence_types"

    equipment_id = Column(Integer, ForeignKey("equipments.id", ondelete="CASCADE"), primary_key=True)
    violence_type_id = Column(Integer, ForeignKey("violence_types.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
