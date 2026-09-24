"""
Catálogos de clasificación de unidades (equipment_categories, unit_types).

En tu ER: equipment_categories reemplaza el enum fijo "Salud | Servicios
para la Mujer | Estación de Policía" del frontend por una tabla
configurable (así lo pide la sección 8 del documento: catálogo editable
en vez de valores fijos en código). unit_types es la taxonomía de tipo
de unidad (CEAM, NEAM... a adaptar a Marinilla), también editable.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class EquipmentCategory(Base):
    """
    Taxonomía gruesa (= FilterTag del frontend: Salud / Servicios para
    la Mujer / Estación de Policía). Antes vivía como ENUM fijo en el
    código; ahora es tabla catálogo editable por la Alcaldía (punto
    2.1 de la revisión).

    DECISIÓN ABIERTA (punto 04 de la revisión): ¿la API debe devolver
    `slug` (ej. "salud") o `label` (ej. "Unidad de Salud", el texto que
    ve la usuaria)? Por eso el catálogo tiene AMBOS campos. Mientras no
    se confirme, el router de equipments expone los dos
    (`equipmentType` = label, `equipmentCategorySlug` = slug) para no
    bloquear al frontend.
    """
    __tablename__ = "equipment_categories"

    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, nullable=False)
    label = Column(String(150), nullable=False)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)

    equipments = relationship("Equipment", back_populates="category")


class UnitType(Base):
    __tablename__ = "unit_types"

    id = Column(Integer, primary_key=True)
    abbreviation = Column(String(20), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)

    equipments = relationship("Equipment", back_populates="unit_type")
