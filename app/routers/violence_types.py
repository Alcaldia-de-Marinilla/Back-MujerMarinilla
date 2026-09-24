from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import AdminUser
from app.models.content import ViolenceType
from app.schemas.violence_type import ViolenceTypeOut, ViolenceTypeCreate, ViolenceTypeUpdate

router = APIRouter(prefix="/api/v1/violence-types", tags=["violence-types"])


@router.get("", response_model=list[ViolenceTypeOut])
def list_violence_types(code: str | None = None, db: Session = Depends(get_db)):
    query = db.query(ViolenceType)
    if code:
        query = query.filter(ViolenceType.code == code)
    return query.order_by(ViolenceType.id).all()


@router.get("/{violence_type_id}", response_model=ViolenceTypeOut)
def get_violence_type(violence_type_id: int, db: Session = Depends(get_db)):
    obj = db.get(ViolenceType, violence_type_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de violencia no encontrado")
    return obj


@router.post("", response_model=ViolenceTypeOut, status_code=status.HTTP_201_CREATED)
def create_violence_type(
    data: ViolenceTypeCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = ViolenceType(**data.model_dump(), updated_by_admin_id=current_admin.id)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un tipo de violencia con ese code")
    db.refresh(obj)
    return obj


@router.put("/{violence_type_id}", response_model=ViolenceTypeOut)
def replace_violence_type(
    violence_type_id: int,
    data: ViolenceTypeCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(ViolenceType, violence_type_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de violencia no encontrado")
    for field, value in data.model_dump().items():
        setattr(obj, field, value)
    obj.updated_by_admin_id = current_admin.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un tipo de violencia con ese code")
    db.refresh(obj)
    return obj


@router.patch("/{violence_type_id}", response_model=ViolenceTypeOut)
def update_violence_type(
    violence_type_id: int,
    data: ViolenceTypeUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(ViolenceType, violence_type_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de violencia no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    obj.updated_by_admin_id = current_admin.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al actualizar el tipo de violencia")
    db.refresh(obj)
    return obj


@router.delete("/{violence_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_violence_type(
    violence_type_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    obj = db.get(ViolenceType, violence_type_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de violencia no encontrado")
    db.delete(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede borrar: hay rutas de atención (referrals) que dependen de este tipo de violencia",
        )
