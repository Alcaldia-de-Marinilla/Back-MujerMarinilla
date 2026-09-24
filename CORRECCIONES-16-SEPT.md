# Correcciones aplicadas — Revisión técnica del 16 de septiembre de 2026

Este documento resume, punto por punto, qué se corrigió a partir del
segundo informe de revisión (seguridad + bugs confirmados + contrato de
API + guía de integración frontend-backend). Sirve como bitácora para el
equipo de la Alcaldía y para quien retome el proyecto más adelante.

## 1. Seguridad

| Punto | Problema | Corrección |
|---|---|---|
| **C1** | `JWT_SECRET_KEY` tenía un valor por defecto (`"changeme"` / clave de ejemplo) en `app/core/config.py`, así que si alguien olvidaba configurar `.env` la app arrancaba igual con una clave predecible. | El campo ya no tiene default: es obligatorio en `.env`. Además se valida que **no** sea el valor de ejemplo del `.env.example` y que tenga **mínimo 32 caracteres**. Si no se cumple, la app **no arranca** (falla rápido, en vez de arrancar insegura). |
| **C2** | El `.dockerignore` no existía / estaba incompleto, por lo que una imagen Docker podía terminar incluyendo `.env`, la base de datos SQLite local, `venv/`, `.git/`, etc. | Se creó `.dockerignore` completo (excluye `.git/`, `venv/`, `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.env`, `.env.*`, `*.db`, `tests/`). |
| **C3** | Uvicorn en el `Dockerfile` registraba en sus logs de acceso la IP de cada visitante — dato sensible en una app de acompañamiento a víctimas de violencia. | Se agregó `--no-access-log` al `CMD` del `Dockerfile`. |
| **CVE** | `python-jose` tiene dos CVEs conocidos (CVE-2024-33663, CVE-2024-33664) relacionados con el manejo de JWT/JWK. | Se migró todo el flujo de firma/verificación de tokens de `python-jose` a **PyJWT** (`app/core/security.py`, `requirements.txt`). |

## 2. Bugs confirmados (respondían 500 en vez de 422/409)

Todos estos casos antes producían un `IntegrityError` de SQLAlchemy sin
capturar, que FastAPI convertía en un `500 Internal Server Error` genérico
(el peor caso posible: el cliente no sabe qué corregir). Ahora responden
con el código HTTP correcto y un mensaje explicando qué está mal.

| Caso | Antes | Ahora |
|---|---|---|
| `PATCH` mandando `null` explícito en un campo obligatorio (ej. `{"title": null}` en un teléfono) | 500 | **422**, con mensaje `"'title' no puede ser null"` |
| `PUT` con el recurso incompleto (le faltan campos obligatorios) | Se aceptaba parcialmente o 500 | **422** — `PUT` ahora reutiliza el mismo schema que `POST`, así que exige el recurso completo |
| Mandar teléfonos o fechas de atención duplicados dentro de la misma lista (`phones: ["190", "190"]`) | 500 (violaba una `UniqueConstraint`) | Se deduplican automáticamente antes de guardar (se conserva el orden) |
| Borrar un tipo de violencia que todavía tiene rutas de atención (`referrals`) apuntándole | 500 | **409**, con mensaje `"No se puede borrar: hay rutas de atención (referrals) que dependen de este tipo de violencia"` |
| Borrar una categoría de equipamiento que todavía tiene unidades (`equipments`) | 500 | **409**, mensaje equivalente |
| Nombre vacío (`""`) o coordenadas fuera de rango (`latitude: 200`) | Se guardaba sin validar o 500 | **422** (se valida `min_length=1` en textos y `-90 ≤ latitude ≤ 90` / `-180 ≤ longitude ≤ 180`) |

## 3. Contrato de API (puntos D1–D5 del informe)

| Punto | Pedido | Estado |
|---|---|---|
| **D1** | El frontend necesita un identificador **estable** para teléfonos, tipos de violencia y rutas de atención, porque el `id` autoincrement de la base de datos cambia cada vez que se re-siembra (`seed`). | Se agregó una columna `code` (string, única, no nula, indexada) a `phones`, `violence_types` y `referrals`. El frontend puede filtrar por `?code=policia` en vez de depender del `id` numérico. |
| **D2** | Bug en el script de siembra: dos equipamientos con el mismo `name` pero distinta `address` se trataban como duplicados y solo se cargaba uno. | Se corrigió la clave de deduplicación de `filter_by(name=...)` a `filter_by(name=..., address=...)`. Verificado: el seed ahora carga 322 unidades (antes 321). |
| **D3** | Faltaba poder filtrar unidades por tipo (`?type=`) además de por categoría. | Se agregó `type: str | None` (alias `type`) en `GET /api/v1/equipments`, que filtra por la abreviatura de `unit_types` sin excluir unidades que no tienen `unit_type` asignado (se usa `outerjoin`). |
| **D4** | (Cubierto junto con los bugs de la sección 2: validaciones de rango/longitud). | Ver tabla anterior. |
| **D5** | Faltaba CRUD para `equipment_categories` (la Alcaldía puede necesitar renombrar o agregar categorías sin tocar código). | Se agregó `app/routers/equipment_categories.py` con el CRUD completo, protegido igual que las demás entidades administrables. |

## 4. Calidad de las pruebas automatizadas

- El test de borrado en cascada (`test_on_delete_cascade_actually_works_at_db_level`)
  antes borraba usando el ORM de SQLAlchemy (`db.delete(equipment)`), lo cual
  dispara el `cascade="all, delete-orphan"` de **Python**, no el `ON DELETE
  CASCADE` de la base de datos. Es decir: el test podía pasar aunque la
  base de datos real no tuviera el cascade bien configurado. Se reescribió
  para insertar y borrar con SQL crudo (`sqlalchemy.text(...)`), sin pasar
  por el ORM, para probar de verdad el comportamiento a nivel de base de
  datos (incluyendo que `PRAGMA foreign_keys=ON` esté activo en SQLite).
- Se agregaron pruebas para cada uno de los bugs de la sección 2 (12 casos
  nuevos), llevando el total de 7 a **17 pruebas**, todas en verde.
- Se agregó `pytest.ini` con `pythonpath = .`: sin este archivo, `pytest`
  (invocado "a secas", como lo hace GitHub Actions) no encontraba el
  paquete `app` — solo funcionaba con `python -m pytest`.

## 5. Integración con CI (GitHub Actions)

Se agregó `.github/workflows/tests.yml`: en cada `push` y `pull request`
se instala Python 3.12, se instalan las dependencias, se corren las
migraciones (`alembic upgrade head`), se verifica que no falten
migraciones (`alembic check`) y se corren las pruebas (`pytest -v`). Este
flujo se simuló localmente en un entorno limpio antes de publicarlo, y
pasó de punta a punta.

## 6. Guía de integración frontend-backend

Ver `INTEGRACION-BACKEND.md` (en el proyecto del frontend) para el
detalle de cómo el frontend Next.js debe consumir esta API en vez de sus
archivos estáticos `src/data/*.ts`.
