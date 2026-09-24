"""
Dependencias reutilizables de FastAPI.

get_current_admin se inyecta en cada endpoint de escritura
(POST/PUT/PATCH/DELETE). Si no hay token o es inválido, FastAPI
responde 401 automáticamente ANTES de ejecutar la lógica del endpoint
(cumple HU-10).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.models.admin import AdminUser

# tokenUrl apunta al endpoint de login; Swagger usa esto para el botón "Authorize"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    admin = db.query(AdminUser).filter(AdminUser.email == email).first()
    if admin is None or not admin.is_active:
        raise credentials_exception
    return admin
