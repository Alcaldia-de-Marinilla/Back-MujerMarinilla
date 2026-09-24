"""
Conexión a la base de datos con SQLAlchemy 2.0.

connect_args con check_same_thread solo aplica a SQLite (necesario porque
FastAPI puede usar la conexión desde distintos hilos). PostgreSQL lo ignora.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)

if settings.database_url.startswith("sqlite"):
    # SQLite ignora ON DELETE CASCADE/RESTRICT/SET NULL a menos que se
    # active este pragma en cada conexión. PostgreSQL los respeta siempre.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependencia inyectable (HU-03): una sesión de BD por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
