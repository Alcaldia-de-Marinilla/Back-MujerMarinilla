"""
D5 (revision del 16 de sept): antes equipment_categories no tenia
endpoints propios. Mismo patron que equipment_types.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import AdminUser
from app.models.catalogs import EquipmentCategory
from app.schemas.equipment_category import (
    EquipmentCategoryOut, EquipmentCategoryCreate, EquipmentCategoryUpdate,
)

router = APIRouter(prefix="/api/v1/equipment-categories", tags=["equipment-categories"])


@router.get("", response_model=list[EquipmentCategoryOut])
def list_equipment_categories(db: Session = Depends(get_db)):
    return db.query(EquipmentCategory).order_by(EquipmentCategory.display_order, EquipmentCategory.id).all()


@router.get("/{category_id}", response_model=EquipmentCategoryOut)
def get_equipment_category(category_id: int, db: Session = Depends(get_db)):
    obj = db.get(EquipmentCategory, category_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    return obj


@router.post("", response_model=EquipmentCategoryOut, status_code=status.HTTP_201_CREATED)
def create_equipment_category(
    data: EquipmentCategoryCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = EquipmentCategory(**data.model_dump(), updated_by_admin_id=current_admin.id)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe una categoría con ese slug")
    db.refresh(obj)
    return obj


@router.put("/{category_id}", response_model=EquipmentCategoryOut)
def replace_equipment_category(
    category_id: int,
    data: EquipmentCategoryCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(EquipmentCategory, category_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    for field, value in data.model_dump().items():
        setattr(obj, field, value)
    obj.updated_by_admin_id = current_admin.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe una categoría con ese slug")
    db.refresh(obj)
    return obj


@router.patch("/{category_id}", response_model=EquipmentCategoryOut)
def update_equipment_category(
    category_id: int,
    data: EquipmentCategoryUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(EquipmentCategory, category_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    obj.updated_by_admin_id = current_admin.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe una categoría con ese slug")
    db.refresh(obj)
    return obj


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(EquipmentCategory, category_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    db.delete(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede borrar: hay unidades (equipments) que dependen de esta categoría",
        )
