"""
HU-08: carga inicial de datos (seed) a partir del contenido actual del
frontend (src/data/*.ts), más los festivos de Colombia 2026.

Uso:
    python -m app.scripts.seed

Es IDEMPOTENTE: si lo corres varias veces, no duplica registros.

Notas de las decisiones tomadas al migrar los datos de src/data/*.ts:

1. equipments.json (322 unidades) es el inventario ACTUAL de Río de
   Janeiro. El seed solo reproduce lo que hoy existe en el frontend
   para probar que el pipeline BD -> API -> frontend funciona de
   punta a punta.

2. El campo `violenceTypes` de cada unidad en equipments.ts es TEXTO
   LIBRE, no una lista de ids. No alimenta la relación N:M
   `equipment_violence_types`; se conserva el texto original al final
   de `notes`.

3. `unit_types`: se crean también los tipos no documentados en
   equipmentsTypes.ts, con descripción placeholder.

4. Festivos: se cargan los 18 festivos oficiales de Colombia para 2026.

5. D1 (revisión del 16 de sept): phones, referrals y violence_types
   ahora se siembran con un `code` estable, para que el frontend pueda
   buscarlos sin depender de los ids autoincrement de la BD.

6. D2 (revisión del 16 de sept): el seed anterior identificaba unidades
   duplicadas SOLO por `name`, y hay dos unidades con el mismo nombre
   pero direcciones distintas. Ahora se identifica por (name, address).
"""
import json
from pathlib import Path
from datetime import datetime, date

from app.database import SessionLocal
from app.models.catalogs import EquipmentCategory, UnitType
from app.models.equipment import Equipment, EquipmentPhone
from app.models.content import ViolenceType, Referral, Phone, Holiday

SEED_DIR = Path(__file__).parent / "seed_data"

CATEGORY_SLUGS = {
    "Unidad de Salud": "salud",
    "Servicios especializados para la Mujer": "servicios-mujer",
    "Estación de Policía": "policia",
}

# D1: códigos estables para las líneas telefónicas, mapeados por el
# "number" original de phones.ts (única clave disponible en la fuente).
PHONE_CODES = {
    "190": "policia",
    "192": "emergencias-medicas",
    "197": "policia-denuncias",
    "180": "linea-orientacion-mujer",
    "(21) 2253-1177": "linea-denuncia-anonima",
    "1746": "linea-atencion-municipio",
}


def load_json(filename: str):
    with open(SEED_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def parse_time(value: str | None):
    """Acepta 'HH:MM' o 'HH:MM:SS'; devuelve datetime.time o None."""
    if not value:
        return None
    value = value.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


def seed_categories(db) -> dict[str, EquipmentCategory]:
    print("Sembrando equipment_categories...")
    result = {}
    for order, (label, slug) in enumerate(CATEGORY_SLUGS.items()):
        existing = db.query(EquipmentCategory).filter_by(slug=slug).first()
        if not existing:
            existing = EquipmentCategory(slug=slug, label=label, display_order=order)
            db.add(existing)
            db.flush()
        result[label] = existing
    db.commit()
    return result


def seed_unit_types(db) -> dict[str, UnitType]:
    print("Sembrando unit_types...")
    result = {}

    documented = load_json("equipmentTypes.json")
    for item in documented:
        existing = db.query(UnitType).filter_by(abbreviation=item["abbreviation"]).first()
        if not existing:
            existing = UnitType(
                abbreviation=item["abbreviation"],
                name=item["name"],
                description=item.get("description"),
            )
            db.add(existing)
            db.flush()
        result[item["abbreviation"]] = existing

    equipments = load_json("equipments.json")
    used_abbrevs = {e["type"] for e in equipments if e.get("type")}
    for abbrev in used_abbrevs - result.keys():
        existing = db.query(UnitType).filter_by(abbreviation=abbrev).first()
        if not existing:
            existing = UnitType(
                abbreviation=abbrev,
                name=abbrev,
                description=(
                    "Tipo importado desde el inventario de Río de Janeiro. "
                    "Pendiente de documentar/adaptar para Marinilla."
                ),
            )
            db.add(existing)
            db.flush()
        result[abbrev] = existing

    db.commit()
    return result


def seed_violence_types(db) -> dict[int, ViolenceType]:
    print("Sembrando violence_types...")
    source_id_to_row = {}
    for item in load_json("violenceTypes.json"):
        code = str(item["id"])  # D1: code estable = id original de violenceTypes.ts
        existing = db.query(ViolenceType).filter_by(code=code).first()
        if not existing:
            existing = ViolenceType(
                code=code,
                name=item["name"],
                description=item.get("description"),
                examples=item.get("examples"),
                image=item.get("image"),
            )
            db.add(existing)
            db.flush()
        source_id_to_row[item["id"]] = existing
    db.commit()
    return source_id_to_row


def seed_referrals(db, violence_type_map: dict[int, ViolenceType]):
    print("Sembrando referrals...")
    for item in load_json("referrals.json"):
        code = str(item["id"])  # D1: code estable = id original de encaminhamento.ts
        existing = db.query(Referral).filter_by(code=code).first()
        if existing:
            continue
        vt = violence_type_map.get(item["idTipoViolencia"])
        if vt is None:
            print(f"  [aviso] referral '{item['header'][:40]}...' referencia "
                  f"idTipoViolencia={item['idTipoViolencia']} sin violence_type asociado; se omite.")
            continue
        db.add(Referral(
            code=code,
            header=item["header"],
            text=item["text"],
            image=item.get("image"),
            name=item.get("name"),
            violence_type_id=vt.id,
        ))
    db.commit()


def seed_phones(db):
    print("Sembrando phones (líneas de ayuda)...")
    for item in load_json("phones.json"):
        code = PHONE_CODES.get(item["number"])
        if code is None:
            print(f"  [aviso] no hay code mapeado para el teléfono {item['number']!r}; se omite.")
            continue
        existing = db.query(Phone).filter_by(code=code).first()
        if not existing:
            db.add(Phone(code=code, number=item["number"], title=item["title"], description=item.get("description")))
    db.commit()


def seed_holidays(db):
    print("Sembrando holidays (Colombia 2026)...")
    for item in load_json("holidays_co_2026.json"):
        holiday_date = date.fromisoformat(item["date"])
        existing = db.query(Holiday).filter_by(date=holiday_date).first()
        if not existing:
            db.add(Holiday(date=holiday_date, name=item["name"]))
    db.commit()


def seed_equipments(db, category_map: dict[str, EquipmentCategory], unit_type_map: dict[str, UnitType]):
    print("Sembrando equipments (322 unidades del frontend actual)...")
    created, skipped = 0, 0
    for item in load_json("equipments.json"):
        # D2: identificar por (name, address), no solo por name.
        existing = db.query(Equipment).filter_by(name=item["name"], address=item.get("address")).first()
        if existing:
            skipped += 1
            continue

        category = category_map.get(item["equipmentType"])
        if category is None:
            print(f"  [aviso] equipmentType desconocido: {item['equipmentType']!r}; se omite unidad {item['name']!r}")
            continue
        unit_type = unit_type_map.get(item.get("type")) if item.get("type") else None

        notes = item.get("notes") or ""
        if item.get("violenceTypes"):
            extra = f"[Tipos de violencia atendidos, texto original]: {item['violenceTypes']}"
            notes = f"{notes}\n{extra}".strip()

        equipment = Equipment(
            category_id=category.id,
            unit_type_id=unit_type.id if unit_type else None,
            name=item["name"],
            abbreviation=item.get("abbreviation"),
            description=item.get("description"),
            function=item.get("function"),
            address=item.get("address"),
            neighborhood=item.get("neighborhood"),
            notes=notes or None,
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
            opening_time=parse_time(item.get("openingTime")),
            closing_time=parse_time(item.get("closingTime")),
            opening_time_saturday=parse_time(item.get("openingTimeSaturday")),
            closing_time_saturday=parse_time(item.get("closingTimeSaturday")),
            opening_time_sunday=parse_time(item.get("openingTimeSunday")),
            closing_time_sunday=parse_time(item.get("closingTimeSunday")),
            open_24h=bool(item.get("open_24")),
            is_active=True,
        )
        db.add(equipment)
        db.flush()

        seen_numbers = set()
        for phone_number in item.get("phones") or []:
            phone_number = phone_number.strip()
            if phone_number and phone_number not in seen_numbers:
                seen_numbers.add(phone_number)
                db.add(EquipmentPhone(equipment_id=equipment.id, phone_number=phone_number))

        created += 1

    db.commit()
    print(f"  equipments creados: {created}, ya existentes (omitidos): {skipped}")


def main():
    db = SessionLocal()
    try:
        category_map = seed_categories(db)
        unit_type_map = seed_unit_types(db)
        violence_type_map = seed_violence_types(db)
        seed_referrals(db, violence_type_map)
        seed_phones(db)
        seed_holidays(db)
        seed_equipments(db, category_map, unit_type_map)
        print("Seed completado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
