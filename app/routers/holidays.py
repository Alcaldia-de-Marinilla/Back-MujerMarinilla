from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import AdminUser
from app.models.content import Holiday
from app.schemas.holiday import HolidayOut, HolidayCreate, HolidayUpdate

router = APIRouter(prefix="/api/v1/holidays", tags=["holidays"])


@router.get("", response_model=list[HolidayOut])
def list_holidays(db: Session = Depends(get_db)):
    return db.query(Holiday).order_by(Holiday.date).all()


@router.get("/{holiday_id}", response_model=HolidayOut)
def get_holiday(holiday_id: int, db: Session = Depends(get_db)):
    obj = db.get(Holiday, holiday_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Festivo no encontrado")
    return obj


@router.post("", response_model=HolidayOut, status_code=status.HTTP_201_CREATED)
def create_holiday(
    data: HolidayCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = Holiday(**data.model_dump(), updated_by_admin_id=current_admin.id)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un festivo en esa fecha")
    db.refresh(obj)
    return obj


@router.put("/{holiday_id}", response_model=HolidayOut)
def replace_holiday(
    holiday_id: int,
    data: HolidayCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(Holiday, holiday_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Festivo no encontrado")
    for field, value in data.model_dump().items():
        setattr(obj, field, value)
    obj.updated_by_admin_id = current_admin.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un festivo en esa fecha")
    db.refresh(obj)
    return obj


@router.patch("/{holiday_id}", response_model=HolidayOut)
def update_holiday(
    holiday_id: int,
    data: HolidayUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(Holiday, holiday_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Festivo no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    obj.updated_by_admin_id = current_admin.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un festivo en esa fecha")
    db.refresh(obj)
    return obj


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(Holiday, holiday_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Festivo no encontrado")
    db.delete(obj)
    db.commit()
