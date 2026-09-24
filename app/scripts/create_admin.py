"""
HU-11: crear el primer administrador por consola.

Uso:
    python -m app.scripts.create_admin admin@marinilla.gov.co "unaClaveSegura123"

No existe ningún endpoint público de registro: esta es la única forma
de crear administradores.
"""
import sys

from app.database import SessionLocal
from app.core.security import hash_password
from app.models.admin import AdminUser


def main():
    if len(sys.argv) != 3:
        print("Uso: python -m app.scripts.create_admin <email> <password>")
        sys.exit(1)

    email, password = sys.argv[1], sys.argv[2]
    db = SessionLocal()
    try:
        if db.query(AdminUser).filter(AdminUser.email == email).first():
            print(f"Ya existe un administrador con el correo {email}")
            sys.exit(1)

        admin = AdminUser(email=email, hashed_password=hash_password(password), is_active=True)
        db.add(admin)
        db.commit()
        print(f"Administrador creado: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
