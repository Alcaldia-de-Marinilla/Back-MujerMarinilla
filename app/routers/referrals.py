"""
D3 (revision del 16 de sept): el filtro de violence_type_id se exponia
en snake_case; ahora se expone como ?violenceTypeId=... via Query(alias=...).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import AdminUser
from app.models.content import Referral, ViolenceType
from app.schemas.referral import ReferralOut, ReferralCreate, ReferralUpdate

router = APIRouter(prefix="/api/v1/referrals", tags=["referrals"])


def _check_violence_type_exists(db: Session, violence_type_id: int):
    if not db.get(ViolenceType, violence_type_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"violenceTypeId {violence_type_id} no existe",
        )


@router.get("", response_model=list[ReferralOut])
def list_referrals(
    violence_type_id: int | None = Query(default=None, alias="violenceTypeId"),
    code: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Referral)
    if violence_type_id is not None:
        query = query.filter(Referral.violence_type_id == violence_type_id)
    if code:
        query = query.filter(Referral.code == code)
    return query.order_by(Referral.id).all()


@router.get("/{referral_id}", response_model=ReferralOut)
def get_referral(referral_id: int, db: Session = Depends(get_db)):
    obj = db.get(Referral, referral_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta de atención no encontrada")
    return obj


@router.post("", response_model=ReferralOut, status_code=status.HTTP_201_CREATED)
def create_referral(
    data: ReferralCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    _check_violence_type_exists(db, data.violence_type_id)
    obj = Referral(**data.model_dump(), updated_by_admin_id=current_admin.id)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un referral con ese code")
    db.refresh(obj)
    return obj


@router.put("/{referral_id}", response_model=ReferralOut)
def replace_referral(
    referral_id: int,
    data: ReferralCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(Referral, referral_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta de atención no encontrada")
    _check_violence_type_exists(db, data.violence_type_id)
    for field, value in data.model_dump().items():
        setattr(obj, field, value)
    obj.updated_by_admin_id = current_admin.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un referral con ese code")
    db.refresh(obj)
    return obj


@router.patch("/{referral_id}", response_model=ReferralOut)
def update_referral(
    referral_id: int,
    data: ReferralUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(Referral, referral_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta de atención no encontrada")

    payload = data.model_dump(exclude_unset=True)
    if "violence_type_id" in payload:
        _check_violence_type_exists(db, payload["violence_type_id"])

    for field, value in payload.items():
        setattr(obj, field, value)
    obj.updated_by_admin_id = current_admin.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al actualizar el referral")
    db.refresh(obj)
    return obj


@router.delete("/{referral_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_referral(
    referral_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(Referral, referral_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta de atención no encontrada")
    db.delete(obj)
    db.commit()
