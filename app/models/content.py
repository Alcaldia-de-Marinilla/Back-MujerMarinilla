"""
Tipo de violencia, Ruta de atencion, Linea telefonica y Festivo.

examples[] de ViolenceType SI se deja como columna JSON (a diferencia de
phones/workingDates de Equipment): son textos cortos sin necesidad de
consultarse individualmente ni de relacionarse con otras tablas, asi
que una tabla aparte seria sobre-ingenieria. Se documenta la asimetria
a proposito en HU-01.

D1 (revision del 16 de sept, "bloquea la integracion"): phones,
referrals y violence_types ahora tienen una columna `code` (texto
unico, NO editable tras crearse). El frontend hoy busca estos
registros por id fijo (190, 192, 201-206...) o por posicion en una
lista, y la API asigna ids nuevos en cada seed -> el boton de
emergencia quedaba sin telefonos. `code` es el identificador ESTABLE
que el frontend debe usar en su lugar (ver DATA-MAPPING.md).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class ViolenceType(Base):
    __tablename__ = "violence_types"

    id = Column(Integer, primary_key=True)
    # D1: mismo valor que el "id" original de violenceTypes.ts (0..6),
    # guardado como texto estable.
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    examples = Column(JSON, nullable=True)  # lista de strings
    image = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)

    referrals = relationship("Referral", back_populates="violence_type")
    equipments = relationship(
        "Equipment", secondary="equipment_violence_types", back_populates="violence_types"
    )


class Referral(Base):
    """
    Ruta de atencion (encaminhamento).

    DECISION ABIERTA (punto 04 de la revision del 27 de agosto, "no nos
    corresponde tomarla solos"): hoy esta relacion es 1:N (un referral
    -> un solo violence_type_id). En los datos reales del frontend ya
    hay un caso limite: el referral "Violencia Moral y Psicologica"
    solo puede apuntar a UNO de los dos tipos con este modelo. Si la
    Alcaldia / equipo de frontend confirma que un referral puede
    aplicar a varios tipos de violencia, esto debe migrar a una tabla
    puente N:M (referral_violence_types), igual que se hizo con
    equipment_violence_types. NO se cambia unilateralmente: se deja
    como 1:N hasta que llegue esa confirmacion.

    DECISION ABIERTA #2: el campo `text` se modela como texto plano
    (Text). Si la respuesta es que viene en Markdown o HTML desde el
    panel de administracion, hay que sanitizarlo al guardar (HTML) o
    renderizarlo en el frontend (Markdown). No se asume ninguna opcion.
    """
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True)
    # D1: mismo valor que el "id" original de encaminhamento.ts (1-6 y
    # 201-206), guardado como texto estable.
    code = Column(String(50), unique=True, nullable=False, index=True)
    header = Column(String(200), nullable=False)
    text = Column(Text, nullable=False)  # ver decision abierta #2 arriba
    image = Column(String(255), nullable=True)
    name = Column(String(150), nullable=True)
    # RESTRICT: no se puede borrar un tipo de violencia mientras tenga referrals asociados
    violence_type_id = Column(Integer, ForeignKey("violence_types.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)

    violence_type = relationship("ViolenceType", back_populates="referrals")


class Phone(Base):
    """Linea telefonica de ayuda (independiente de las de Equipment)."""
    __tablename__ = "phones"

    id = Column(Integer, primary_key=True)
    # D1: identificador estable, ej. "policia", "emergencias-medicas".
    code = Column(String(50), unique=True, nullable=False, index=True)
    number = Column(String(30), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True)
    name = Column(String(150), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
