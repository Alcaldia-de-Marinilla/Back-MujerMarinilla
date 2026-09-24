"""
Seguridad: hash de contraseñas (passlib/bcrypt) y tokens JWT.

Revision del 16 de sept, punto 1.5: python-jose 3.3.0 tiene CVEs
publicados (CVE-2024-33663, CVE-2024-33664). Se migro a PyJWT, que es
la libreria que recomienda la propia documentacion de FastAPI.
"""
from datetime import datetime, timedelta, timezone

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """subject suele ser el email o id del admin autenticado."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Devuelve el 'sub' (email del admin) si el token es válido, o None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except PyJWTError:
        return None
