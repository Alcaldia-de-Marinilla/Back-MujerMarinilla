"""
Importa todos los modelos en un solo lugar.

Esto es importante para Alembic: al hacer autogenerate necesita que
TODAS las clases estén registradas contra Base.metadata antes de
comparar el esquema. Si Alembic "no ve" una tabla nueva, casi siempre
es porque falta importarla aquí.
"""
from app.models.catalogs import EquipmentCategory, UnitType
from app.models.equipment import (
    Equipment, EquipmentPhone, EquipmentWorkingDate, EquipmentViolenceType,
)
from app.models.content import ViolenceType, Referral, Phone, Holiday
from app.models.admin import AdminUser

__all__ = [
    "EquipmentCategory", "UnitType",
    "Equipment", "EquipmentPhone", "EquipmentWorkingDate", "EquipmentViolenceType",
    "ViolenceType", "Referral", "Phone", "Holiday",
    "AdminUser",
]
