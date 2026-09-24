"""
CRUD de Phone: patron completo, con las correcciones de la revision
del 16 de sept:
  - PUT usa PhoneCreate (recurso completo, code+number+title obligatorios)
  - PATCH usa PhoneUpdate (parcial, rechaza null explicito en campos NOT NULL)
  - IntegrityError (code o unique violado) -> 409, no 500
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import AdminUser
from app.models.content import Phone
from app.schemas.phone import PhoneOut, PhoneCreate, PhoneUpdate

router = APIRouter(prefix="/api/v1/phones", tags=["phones"])


@router.get("", response_model=list[PhoneOut])
def list_phones(code: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Phone)
    if code:
        query = query.filter(Phone.code == code)
    return query.order_by(Phone.id).all()


@router.get("/{phone_id}", response_model=PhoneOut)
def get_phone(phone_id: int, db: Session = Depends(get_db)):
    phone = db.get(Phone, phone_id)
    if not phone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teléfono no encontrado")
    return phone


@router.post("", response_model=PhoneOut, status_code=status.HTTP_201_CREATED)
def create_phone(
    data: PhoneCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    phone = Phone(**data.model_dump(), updated_by_admin_id=current_admin.id)
    db.add(phone)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un teléfono con ese code o number")
    db.refresh(phone)
    return phone


@router.put("/{phone_id}", response_model=PhoneOut)
def replace_phone(
    phone_id: int,
    data: PhoneCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """PUT: reemplaza el recurso completo. Exige todos los campos obligatorios."""
    phone = db.get(Phone, phone_id)
    if not phone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teléfono no encontrado")

    for field, value in data.model_dump().items():
        setattr(phone, field, value)
    phone.updated_by_admin_id = current_admin.id

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un teléfono con ese code o number")
    db.refresh(phone)
    return phone


@router.patch("/{phone_id}", response_model=PhoneOut)
def update_phone(
    phone_id: int,
    data: PhoneUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """PATCH: actualización parcial. Solo toca los campos enviados."""
    phone = db.get(Phone, phone_id)
    if not phone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teléfono no encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(phone, field, value)
    phone.updated_by_admin_id = current_admin.id

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un teléfono con ese number")
    db.refresh(phone)
    return phone


@router.delete("/{phone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_phone(
    phone_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    phone = db.get(Phone, phone_id)
    if not phone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teléfono no encontrado")
    db.delete(phone)
    db.commit()
