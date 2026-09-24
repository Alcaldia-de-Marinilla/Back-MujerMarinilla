from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import AdminUser
from app.models.catalogs import UnitType
from app.schemas.equipment_type import EquipmentTypeOut, EquipmentTypeCreate, EquipmentTypeUpdate

router = APIRouter(prefix="/api/v1/equipment-types", tags=["equipment-types"])


@router.get("", response_model=list[EquipmentTypeOut])
def list_equipment_types(db: Session = Depends(get_db)):
    return db.query(UnitType).order_by(UnitType.id).all()


@router.get("/{unit_type_id}", response_model=EquipmentTypeOut)
def get_equipment_type(unit_type_id: int, db: Session = Depends(get_db)):
    obj = db.get(UnitType, unit_type_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de unidad no encontrado")
    return obj


@router.post("", response_model=EquipmentTypeOut, status_code=status.HTTP_201_CREATED)
def create_equipment_type(
    data: EquipmentTypeCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = UnitType(**data.model_dump(), updated_by_admin_id=current_admin.id)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al crear el tipo de unidad")
    db.refresh(obj)
    return obj


@router.put("/{unit_type_id}", response_model=EquipmentTypeOut)
def replace_equipment_type(
    unit_type_id: int,
    data: EquipmentTypeCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(UnitType, unit_type_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de unidad no encontrado")
    for field, value in data.model_dump().items():
        setattr(obj, field, value)
    obj.updated_by_admin_id = current_admin.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al actualizar el tipo de unidad")
    db.refresh(obj)
    return obj


@router.patch("/{unit_type_id}", response_model=EquipmentTypeOut)
def update_equipment_type(
    unit_type_id: int,
    data: EquipmentTypeUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(UnitType, unit_type_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de unidad no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    obj.updated_by_admin_id = current_admin.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al actualizar el tipo de unidad")
    db.refresh(obj)
    return obj


@router.delete("/{unit_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment_type(
    unit_type_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(UnitType, unit_type_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de unidad no encontrado")
    db.delete(obj)
    db.commit()  # ON DELETE SET NULL en equipments.unit_type_id: nunca falla por integridad
