"""
HU-09: login de administrador.

OAuth2PasswordRequestForm espera un form-urlencoded con campos
'username' y 'password' (así funciona el estándar OAuth2 Password
Flow, aunque nosotros lo usamos con el email en 'username'). Es
justo el formato que espera el botón "Authorize" de Swagger.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_admin
from app.models.admin import AdminUser
from app.schemas.auth import Token, AdminOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.email == form_data.username).first()

    # Mensaje genérico a propósito: no revelamos si falló el email o la contraseña.
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Correo o contraseña incorrectos",
    )

    if not admin or not admin.is_active:
        raise invalid_credentials
    if not verify_password(form_data.password, admin.hashed_password):
        raise invalid_credentials

    token = create_access_token(subject=admin.email)
    return Token(access_token=token)


@router.get("/me", response_model=AdminOut)
def read_me(current_admin: AdminUser = Depends(get_current_admin)):
    return current_admin
