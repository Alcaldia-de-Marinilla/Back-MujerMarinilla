"""
RNF-08: al menos un CRUD completo + flujo de auth con pruebas automatizadas.
Corre con: pytest
Usa una BD SQLite separada solo para pruebas (no toca mujer_marinilla.db).

Revision del 16 de sept, punto 1.5, correcciones aplicadas aqui:
  - teardown_module ahora llama engine.dispose() ANTES de borrar test.db,
    para no fallar con PermissionError en Windows.
  - test_on_delete_cascade_actually_works se reescribio: el anterior no
    probaba lo que decia, porque SQLAlchemy ya borra los hijos por su
    cuenta a nivel de ORM (cascade="all, delete-orphan") antes de que la
    base de datos aplique el ON DELETE CASCADE. Ahora se borra con SQL
    crudo, sin pasar por el ORM.
  - Se agrego un test por cada fila de la tabla "errores confirmados".
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "solo-para-tests-no-usar-en-ningun-entorno-real-0123456789"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.main import app  # noqa: E402
from app.database import Base, engine, SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.admin import AdminUser  # noqa: E402
from app.models.catalogs import EquipmentCategory  # noqa: E402
from app.models.content import ViolenceType, Referral, Phone  # noqa: E402

client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(AdminUser(email="test@admin.com", hashed_password=hash_password("test1234"), is_active=True))
    db.commit()
    db.close()


def teardown_module():
    Base.metadata.drop_all(bind=engine)
    engine.dispose()  # cierra todas las conexiones abiertas antes de borrar el archivo
    if os.path.exists("test.db"):
        os.remove("test.db")


def get_token():
    resp = client.post("/api/v1/auth/login", data={"username": "test@admin.com", "password": "test1234"})
    assert resp.status_code == 200
    return resp.json()["accessToken"]


def auth_headers():
    return {"Authorization": f"Bearer {get_token()}"}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_login_wrong_password():
    resp = client.post("/api/v1/auth/login", data={"username": "test@admin.com", "password": "mala"})
    assert resp.status_code == 401


def test_login_ok_and_me():
    headers = auth_headers()
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@admin.com"


def test_phone_crud_requires_auth_for_writes():
    headers = auth_headers()

    resp = client.get("/api/v1/phones")
    assert resp.status_code == 200

    resp = client.post("/api/v1/phones", json={"code": "test-1", "number": "123", "title": "Linea"})
    assert resp.status_code == 401

    resp = client.post("/api/v1/phones", json={"code": "test-155", "number": "155", "title": "Linea 155"}, headers=headers)
    assert resp.status_code == 201
    phone_id = resp.json()["id"]
    assert resp.json()["code"] == "test-155"

    resp = client.patch(f"/api/v1/phones/{phone_id}", json={"title": "Linea 155 actualizada"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Linea 155 actualizada"

    resp = client.delete(f"/api/v1/phones/{phone_id}")
    assert resp.status_code == 401

    resp = client.delete(f"/api/v1/phones/{phone_id}", headers=headers)
    assert resp.status_code == 204

    resp = client.get(f"/api/v1/phones/{phone_id}")
    assert resp.status_code == 404


def _create_test_category(slug="salud-test"):
    db = SessionLocal()
    category = db.query(EquipmentCategory).filter_by(slug=slug).first()
    if not category:
        category = EquipmentCategory(slug=slug, label="Salud Test", display_order=0)
        db.add(category)
        db.commit()
        db.refresh(category)
    category_id = category.id
    db.close()
    return category_id


def test_equipment_full_flow_with_relations():
    headers = auth_headers()

    cat_resp = client.post(
        "/api/v1/equipment-types",
        json={"abbreviation": "TST", "name": "Tipo de prueba"},
        headers=headers,
    )
    assert cat_resp.status_code == 201
    unit_type_id = cat_resp.json()["id"]

    vt_resp = client.post(
        "/api/v1/violence-types",
        json={"code": "vt-test-1", "name": "Violencia de prueba", "description": "desc"},
        headers=headers,
    )
    violence_type_id = vt_resp.json()["id"]

    category_id = _create_test_category()

    resp = client.post(
        "/api/v1/equipments",
        json={
            "categoryId": category_id,
            "unitTypeId": unit_type_id,
            "name": "Unidad de prueba",
            "phones": ["3000000000"],
            "open24": True,
            "violenceTypeIds": [violence_type_id],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["equipmentType"] == "Salud Test"
    assert body["type"] == "TST"
    assert body["phones"] == ["3000000000"]
    assert body["open24"] is True
    assert body["violenceTypes"] == ["Violencia de prueba"]
    equipment_id = body["id"]

    resp = client.get(f"/api/v1/equipments/{equipment_id}")
    assert resp.status_code == 200

    resp = client.get("/api/v1/equipments", params={"equipmentType": "Salud Test"})
    assert resp.status_code == 200
    assert any(e["id"] == equipment_id for e in resp.json())

    resp = client.patch(
        f"/api/v1/equipments/{equipment_id}",
        json={"phones": ["3111111111", "3222222222"]},
        headers=headers,
    )
    assert resp.status_code == 200
    assert sorted(resp.json()["phones"]) == ["3111111111", "3222222222"]

    resp = client.delete(f"/api/v1/equipments/{equipment_id}", headers=headers)
    assert resp.status_code == 204
    resp = client.get(f"/api/v1/equipments/{equipment_id}")
    assert resp.status_code == 404


def test_holiday_unique_date():
    headers = auth_headers()

    resp = client.post("/api/v1/holidays", json={"date": "2026-01-01", "name": "Año Nuevo"}, headers=headers)
    assert resp.status_code == 201

    resp = client.post("/api/v1/holidays", json={"date": "2026-01-01", "name": "Duplicado"}, headers=headers)
    assert resp.status_code == 409


def test_on_delete_cascade_actually_works_at_db_level():
    """
    Borra la unidad con SQL crudo (bypassa el ORM por completo). Si esto
    deja huérfanos, es porque el ON DELETE CASCADE de la base de datos
    (y el PRAGMA foreign_keys=ON de SQLite) no está funcionando de verdad.
    """
    category_id = _create_test_category(slug="salud-cascade-test")

    db = SessionLocal()
    violence_type = ViolenceType(code="vt-cascade-test", name="Violencia Cascade Test")
    db.add(violence_type)
    db.commit()
    db.refresh(violence_type)

    db.execute(text(
        "INSERT INTO equipments (category_id, name, open_24h, is_active) "
        "VALUES (:category_id, 'Unidad para probar cascade', 0, 1)"
    ), {"category_id": category_id})
    db.commit()
    equipment_id = db.execute(text(
        "SELECT id FROM equipments WHERE name = 'Unidad para probar cascade'"
    )).scalar_one()

    db.execute(text(
        "INSERT INTO equipment_phones (equipment_id, phone_number) VALUES (:eid, '3009998888')"
    ), {"eid": equipment_id})
    db.execute(text(
        "INSERT INTO equipment_working_dates (equipment_id, work_date) VALUES (:eid, '2026-12-25')"
    ), {"eid": equipment_id})
    db.execute(text(
        "INSERT INTO equipment_violence_types (equipment_id, violence_type_id) VALUES (:eid, :vtid)"
    ), {"eid": equipment_id, "vtid": violence_type.id})
    db.commit()

    def counts():
        phones = db.execute(text("SELECT COUNT(*) FROM equipment_phones WHERE equipment_id = :eid"), {"eid": equipment_id}).scalar_one()
        dates = db.execute(text("SELECT COUNT(*) FROM equipment_working_dates WHERE equipment_id = :eid"), {"eid": equipment_id}).scalar_one()
        rels = db.execute(text("SELECT COUNT(*) FROM equipment_violence_types WHERE equipment_id = :eid"), {"eid": equipment_id}).scalar_one()
        return phones, dates, rels

    assert counts() == (1, 1, 1)

    db.execute(text("DELETE FROM equipments WHERE id = :eid"), {"eid": equipment_id})
    db.commit()

    assert counts() == (0, 0, 0)
    db.close()


def test_patch_equipment_null_on_required_field_is_422():
    headers = auth_headers()
    category_id = _create_test_category()
    resp = client.post("/api/v1/equipments", json={"categoryId": category_id, "name": "Unidad null-test"}, headers=headers)
    equipment_id = resp.json()["id"]

    resp = client.patch(f"/api/v1/equipments/{equipment_id}", json={"name": None}, headers=headers)
    assert resp.status_code == 422

    resp = client.patch(f"/api/v1/equipments/{equipment_id}", json={"open24": None}, headers=headers)
    assert resp.status_code == 422


def test_patch_phone_null_title_is_422():
    headers = auth_headers()
    resp = client.post("/api/v1/phones", json={"code": "null-test", "number": "999", "title": "Original"}, headers=headers)
    phone_id = resp.json()["id"]

    resp = client.patch(f"/api/v1/phones/{phone_id}", json={"title": None}, headers=headers)
    assert resp.status_code == 422


def test_duplicate_phones_and_working_dates_are_deduped_not_500():
    headers = auth_headers()
    category_id = _create_test_category()
    resp = client.post(
        "/api/v1/equipments",
        json={
            "categoryId": category_id,
            "name": "Unidad dedupe-test",
            "phones": ["3001111111", "3001111111", "3002222222"],
            "workingDates": ["2026-12-25", "2026-12-25"],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert sorted(body["phones"]) == ["3001111111", "3002222222"]
    assert body["workingDates"] == ["2026-12-25"]


def test_delete_violence_type_with_referrals_is_409():
    headers = auth_headers()
    vt_resp = client.post("/api/v1/violence-types", json={"code": "vt-409-test", "name": "Violencia 409"}, headers=headers)
    violence_type_id = vt_resp.json()["id"]

    ref_resp = client.post(
        "/api/v1/referrals",
        json={"code": "ref-409-test", "header": "h", "text": "t", "violenceTypeId": violence_type_id},
        headers=headers,
    )
    assert ref_resp.status_code == 201

    resp = client.delete(f"/api/v1/violence-types/{violence_type_id}", headers=headers)
    assert resp.status_code == 409


def test_put_equipment_incomplete_is_422():
    headers = auth_headers()
    category_id = _create_test_category()
    resp = client.post("/api/v1/equipments", json={"categoryId": category_id, "name": "Unidad PUT-test"}, headers=headers)
    equipment_id = resp.json()["id"]

    resp = client.put(f"/api/v1/equipments/{equipment_id}", json={"name": "Solo nombre"}, headers=headers)
    assert resp.status_code == 422

    resp = client.put(
        f"/api/v1/equipments/{equipment_id}",
        json={"categoryId": category_id, "name": "Nombre completo", "open24": False},
        headers=headers,
    )
    assert resp.status_code == 200


def test_empty_name_and_invalid_latitude_are_422():
    headers = auth_headers()
    category_id = _create_test_category()

    resp = client.post("/api/v1/equipments", json={"categoryId": category_id, "name": ""}, headers=headers)
    assert resp.status_code == 422

    resp = client.post("/api/v1/equipments", json={"categoryId": category_id, "name": "Unidad lat-test"}, headers=headers)
    equipment_id = resp.json()["id"]

    resp = client.patch(f"/api/v1/equipments/{equipment_id}", json={"latitude": 999}, headers=headers)
    assert resp.status_code == 422

    resp = client.patch(f"/api/v1/equipments/{equipment_id}", json={"longitude": -999}, headers=headers)
    assert resp.status_code == 422


def test_equipments_type_filter():
    headers = auth_headers()
    category_id = _create_test_category()
    ut_resp = client.post("/api/v1/equipment-types", json={"abbreviation": "FLT", "name": "Filtro test"}, headers=headers)
    unit_type_id = ut_resp.json()["id"]

    resp = client.post(
        "/api/v1/equipments",
        json={"categoryId": category_id, "unitTypeId": unit_type_id, "name": "Unidad filtro-test"},
        headers=headers,
    )
    equipment_id = resp.json()["id"]

    resp = client.get("/api/v1/equipments", params={"type": "FLT"})
    assert resp.status_code == 200
    assert any(e["id"] == equipment_id for e in resp.json())

    resp = client.get("/api/v1/equipments", params={"type": "NO-EXISTE"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_referrals_violence_type_id_filter_is_camelcase():
    headers = auth_headers()
    vt_resp = client.post("/api/v1/violence-types", json={"code": "vt-filter-test", "name": "Violencia filtro"}, headers=headers)
    violence_type_id = vt_resp.json()["id"]
    client.post(
        "/api/v1/referrals",
        json={"code": "ref-filter-test", "header": "h", "text": "t", "violenceTypeId": violence_type_id},
        headers=headers,
    )

    resp = client.get("/api/v1/referrals", params={"violenceTypeId": violence_type_id})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert all(r["violenceTypeId"] == violence_type_id for r in resp.json())


def test_equipment_categories_crud():
    headers = auth_headers()

    resp = client.post(
        "/api/v1/equipment-categories",
        json={"slug": "categoria-test", "label": "Categoría Test", "displayOrder": 9},
        headers=headers,
    )
    assert resp.status_code == 201
    category_id = resp.json()["id"]

    resp = client.get("/api/v1/equipment-categories")
    assert resp.status_code == 200
    assert any(c["id"] == category_id for c in resp.json())

    resp = client.patch(
        f"/api/v1/equipment-categories/{category_id}",
        json={"label": "Categoría Test Editada"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["label"] == "Categoría Test Editada"

    resp = client.delete(f"/api/v1/equipment-categories/{category_id}", headers=headers)
    assert resp.status_code == 204


def test_delete_equipment_category_with_equipments_is_409():
    headers = auth_headers()
    category_id = _create_test_category(slug="categoria-con-unidades-test")
    client.post("/api/v1/equipments", json={"categoryId": category_id, "name": "Unidad ancla"}, headers=headers)

    resp = client.delete(f"/api/v1/equipment-categories/{category_id}", headers=headers)
    assert resp.status_code == 409
