"""
Router de Equipment: CRUD completo + filtros.

Correcciones de la revision del 16 de sept aplicadas aqui:
  - D3: se agrega el filtro ?type= (abreviatura del tipo de unidad).
  - PUT vs PATCH: PUT usa EquipmentCreate (recurso completo, exige
    categoryId y name) y PATCH usa EquipmentUpdate (parcial, rechaza
    null explicito en campos obligatorios).
  - IntegrityError capturado -> 409 en vez de 500.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import AdminUser
from app.models.catalogs import EquipmentCategory, UnitType
from app.models.equipment import Equipment, EquipmentPhone, EquipmentWorkingDate
from app.models.content import ViolenceType
from app.schemas.equipment import EquipmentOut, EquipmentCreate, EquipmentUpdate

router = APIRouter(prefix="/api/v1/equipments", tags=["equipments"])


def _to_out(equipment: Equipment) -> EquipmentOut:
    return EquipmentOut(
        id=equipment.id,
        equipment_type=equipment.category.label if equipment.category else None,
        equipment_category_slug=equipment.category.slug if equipment.category else None,
        type=equipment.unit_type.abbreviation if equipment.unit_type else None,
        name=equipment.name,
        abbreviation=equipment.abbreviation,
        opening_time=equipment.opening_time,
        closing_time=equipment.closing_time,
        phones=[p.phone_number for p in equipment.phones],
        description=equipment.description,
        function=equipment.function,
        violence_types=[vt.name for vt in equipment.violence_types],
        address=equipment.address,
        neighborhood=equipment.neighborhood,
        notes=equipment.notes,
        latitude=float(equipment.latitude) if equipment.latitude is not None else None,
        longitude=float(equipment.longitude) if equipment.longitude is not None else None,
        opening_time_saturday=equipment.opening_time_saturday,
        closing_time_saturday=equipment.closing_time_saturday,
        opening_time_sunday=equipment.opening_time_sunday,
        closing_time_sunday=equipment.closing_time_sunday,
        working_dates=[w.work_date for w in equipment.working_dates],
        open_24h=equipment.open_24h,
        created_at=equipment.created_at,
        updated_at=equipment.updated_at,
    )


def _with_relations(query):
    return query.options(
        selectinload(Equipment.category),
        selectinload(Equipment.unit_type),
        selectinload(Equipment.phones),
        selectinload(Equipment.working_dates),
        selectinload(Equipment.violence_types),
    )


def _get_equipment_or_404(db: Session, equipment_id: int) -> Equipment:
    equipment = _with_relations(db.query(Equipment)).filter(
        Equipment.id == equipment_id, Equipment.is_active.is_(True)
    ).first()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad no encontrada")
    return equipment


def _sync_children(db: Session, equipment: Equipment, data: dict):
    if "phones" in data and data["phones"] is not None:
        db.query(EquipmentPhone).filter(EquipmentPhone.equipment_id == equipment.id).delete()
        for number in data["phones"]:
            if number and number.strip():
                db.add(EquipmentPhone(equipment_id=equipment.id, phone_number=number.strip()))

    if "working_dates" in data and data["working_dates"] is not None:
        db.query(EquipmentWorkingDate).filter(EquipmentWorkingDate.equipment_id == equipment.id).delete()
        for work_date in data["working_dates"]:
            db.add(EquipmentWorkingDate(equipment_id=equipment.id, work_date=work_date))

    if "violence_type_ids" in data and data["violence_type_ids"] is not None:
        ids = data["violence_type_ids"]
        found = db.query(ViolenceType).filter(ViolenceType.id.in_(ids)).all()
        if len(found) != len(set(ids)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Uno o más violenceTypeIds no existen",
            )
        equipment.violence_types = found


@router.get("", response_model=list[EquipmentOut])
def list_equipments(
    equipment_type: str | None = Query(default=None, alias="equipmentType", description="Nombre de la categoría, p. ej. 'Unidad de Salud'"),
    type: str | None = Query(default=None, description="Abreviatura del tipo de unidad, p. ej. 'CEAM'"),
    bbox: str | None = Query(default=None, description="minLng,minLat,maxLng,maxLat"),
    db: Session = Depends(get_db),
):
    query = (
        _with_relations(db.query(Equipment))
        .join(EquipmentCategory)
        .outerjoin(UnitType, Equipment.unit_type_id == UnitType.id)
        .filter(Equipment.is_active.is_(True))
    )

    if equipment_type:
        query = query.filter(EquipmentCategory.label == equipment_type)

    if type:
        query = query.filter(UnitType.abbreviation == type)

    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = (float(x) for x in bbox.split(","))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="bbox debe tener el formato minLng,minLat,maxLng,maxLat",
            )
        query = query.filter(
            Equipment.longitude.between(min_lng, max_lng),
            Equipment.latitude.between(min_lat, max_lat),
        )

    equipments = query.order_by(Equipment.id).all()
    return [_to_out(e) for e in equipments]


@router.get("/{equipment_id}", response_model=EquipmentOut)
def get_equipment(equipment_id: int, db: Session = Depends(get_db)):
    return _to_out(_get_equipment_or_404(db, equipment_id))


def _validate_catalogs(db: Session, category_id: int | None, unit_type_id: int | None):
    if category_id is not None and not db.get(EquipmentCategory, category_id):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="categoryId no existe")
    if unit_type_id is not None and not db.get(UnitType, unit_type_id):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="unitTypeId no existe")


@router.post("", response_model=EquipmentOut, status_code=status.HTTP_201_CREATED)
def create_equipment(
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    _validate_catalogs(db, data.category_id, data.unit_type_id)

    payload = data.model_dump(exclude={"phones", "working_dates", "violence_type_ids"})
    equipment = Equipment(**payload, updated_by_admin_id=current_admin.id)
    db.add(equipment)
    db.flush()

    _sync_children(db, equipment, data.model_dump())

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al crear la unidad")
    return _to_out(_get_equipment_or_404(db, equipment.id))


@router.put("/{equipment_id}", response_model=EquipmentOut)
def replace_equipment(
    equipment_id: int,
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """PUT: reemplaza el recurso completo. Exige categoryId y name."""
    equipment = _get_equipment_or_404(db, equipment_id)
    _validate_catalogs(db, data.category_id, data.unit_type_id)

    scalar_fields = data.model_dump(exclude={"phones", "working_dates", "violence_type_ids"})
    for field, value in scalar_fields.items():
        setattr(equipment, field, value)
    equipment.updated_by_admin_id = current_admin.id

    _sync_children(db, equipment, data.model_dump())

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al reemplazar la unidad")
    return _to_out(_get_equipment_or_404(db, equipment.id))


@router.patch("/{equipment_id}", response_model=EquipmentOut)
def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """PATCH: actualización parcial. Solo toca los campos enviados."""
    equipment = _get_equipment_or_404(db, equipment_id)
    payload = data.model_dump(exclude_unset=True)

    _validate_catalogs(db, payload.get("category_id"), payload.get("unit_type_id"))

    scalar_fields = {
        k: v for k, v in payload.items()
        if k not in {"phones", "working_dates", "violence_type_ids"}
    }
    for field, value in scalar_fields.items():
        setattr(equipment, field, value)
    equipment.updated_by_admin_id = current_admin.id

    _sync_children(db, equipment, payload)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al actualizar la unidad")
    return _to_out(_get_equipment_or_404(db, equipment.id))


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Soft delete: is_active=False, para no perder historial."""
    equipment = _get_equipment_or_404(db, equipment_id)
    equipment.is_active = False
    equipment.updated_by_admin_id = current_admin.id
    db.commit()
