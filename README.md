# Backend Mujer Marinilla — Guía de instalación y stack tecnológico

Este proyecto ya está probado end-to-end (login JWT + CRUD protegido +
migraciones + tests) y sigue el modelo de datos de tu diagrama ER
(`equipment_categories`, `unit_types`, `equipments`, `equipment_phones`,
`equipment_working_dates`, `equipment_violence_types`, `violence_types`,
`referrals`, `phones`, `holidays`, `admin_users`).

## 0. Documentos de este proyecto

- **`DATA-MAPPING.md`**: tabla de equivalencias TypeScript ↔ columna BD ↔ campo API (pedida en la revisión técnica del 27 de agosto de 2026).
- **`DECISIONES-PENDIENTES.md`**: las 4 decisiones que la revisión técnica identificó como "no le corresponde al equipo de practicantes tomarlas solo" (referrals 1:N vs N:M, significado de `equipment_working_dates`, formato de `referrals.text`, slug vs label de categorías). El código ya tiene un comportamiento por defecto para poder seguir desarrollando, señalado con comentarios `DECISIÓN ABIERTA` en cada modelo afectado — **no cambiarlo sin confirmar con la Alcaldía / equipo de frontend**.
- **`CORRECCIONES-16-SEPT.md`**: qué se corrigió a partir de la segunda revisión técnica (seguridad, bugs de error 500, contrato de API D1-D5, calidad de pruebas y CI). Léelo antes de tocar autenticación, validaciones o el script de siembra.

## 1. ¿Qué es cada tecnología y hay que "descargarla"?

Nada de esto se descarga como un programa aparte (no es como instalar
Postgres o Docker Desktop). **Son librerías de Python que se instalan
con `pip`** dentro de un entorno virtual del proyecto. Ya están todas
listadas en `requirements.txt`.

| Tecnología | Qué es | Se usa así |
|---|---|---|
| **FastAPI** | El framework: define tus rutas (`@router.get(...)`), valida datos con Pydantic y genera la documentación OpenAPI sola. No es un servidor. | `from fastapi import FastAPI` |
| **Uvicorn** | El servidor ASGI: el proceso que de verdad escucha en un puerto TCP y ejecuta tu código FastAPI ante cada petición HTTP. Sin Uvicorn (u otro servidor ASGI), FastAPI es solo código, no atiende peticiones. | `uvicorn app.main:app --reload` |
| **SQLAlchemy** | El ORM: mapea tus clases Python (`app/models/*.py`) a tablas SQL, para no escribir SQL a mano. | `db.query(Phone).all()` |
| **Alembic** | El versionador del esquema de BD: genera archivos de "migración" que crean/alteran tablas, y lleva el historial (como Git pero para el esquema de la BD). | `alembic revision --autogenerate`, `alembic upgrade head` |
| **python-jose** | Genera y valida los tokens JWT (el "pase" que el admin recibe al hacer login). | `app/core/security.py` |
| **passlib[bcrypt]** | Convierte la contraseña del admin en un hash irreversible antes de guardarla. Nunca se guarda la contraseña en texto plano. | `app/core/security.py` |
| **Pydantic** | Valida y da forma a los datos de entrada/salida de la API (y hace la conversión snake_case ↔ camelCase). | `app/schemas/*.py` |
| **pytest + httpx** | Framework de pruebas automatizadas. | `pytest` |

## 2. Instalación paso a paso (en tu máquina)

Requisito previo: tener Python 3.11+ instalado (`python3 --version`).

```bash
# 1. Entra a la carpeta del proyecto
cd backend

# 2. Crea un entorno virtual (aísla las librerías de este proyecto)
python3 -m venv venv

# 3. Actívalo
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows

# 4. Instala TODAS las dependencias de una vez
pip install -r requirements.txt

# 5. Copia el archivo de variables de entorno de ejemplo
cp .env.example .env
# Abre .env y cambia al menos JWT_SECRET_KEY por algo largo y aleatorio
```

Con eso ya tienes FastAPI, Uvicorn, Alembic, SQLAlchemy, python-jose y
passlib instalados dentro de `venv/`. No hay nada más que "descargar".

## 3. Crear la base de datos con Alembic

```bash
# Aplica las migraciones (crea todas las tablas en SQLite o Postgres,
# según lo que tengas en DATABASE_URL dentro de .env)
alembic upgrade head
```

Ya está incluida la primera migración (`alembic/versions/..._modelo_inicial...py`)
generada automáticamente a partir de tus modelos SQLAlchemy, que a su
vez reflejan tu diagrama ER. Si más adelante cambias un modelo (agregas
una columna, etc.), el flujo es:

```bash
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head
```

## 4. Cargar los datos iniciales (seed, HU-08)

Reproduce los datos que hoy están escritos directamente en el frontend
(`src/data/*.ts`), ya extraídos a JSON dentro de `app/scripts/seed_data/`:

```bash
python -m app.scripts.seed
```

Es **idempotente**: correrlo varias veces no duplica registros. Carga:
- 3 categorías de equipamiento, 14 tipos de unidad, 7 tipos de violencia,
  12 rutas de atención, 6 teléfonos de ayuda, 18 festivos de Colombia 2026,
  y 322 unidades (el inventario actual del frontend, que sigue siendo el
  de Río de Janeiro — ver el aviso al inicio de `app/scripts/seed.py`
  sobre por qué no se tradujo/reemplazó automáticamente por datos de
  Marinilla).

Lee los comentarios al inicio de `app/scripts/seed.py`: ahí se explican
las decisiones tomadas al migrar cada archivo (por qué `violenceTypes`
de cada unidad no alimenta la relación N:M, cómo se resolvieron los
tipos de unidad no documentados, etc.).

## 5. Crear el primer administrador (HU-11)

No hay endpoint público de registro, a propósito (seguridad). Se crea
por consola:

```bash
python -m app.scripts.create_admin admin@marinilla.gov.co "unaClaveSegura123"
```

## 6. Levantar el servidor

```bash
uvicorn app.main:app --reload
```

- `app.main:app` = "en el módulo `app/main.py`, usa la variable `app`".
- `--reload` reinicia el servidor solo cuando guardas cambios (úsalo solo en desarrollo, nunca en producción).

Ahora puedes abrir:
- `http://127.0.0.1:8000/health` → `{"status":"ok"}`
- `http://127.0.0.1:8000/docs` → Swagger interactivo (ahí puedes hacer clic en "Authorize", pegar tu token y probar los endpoints protegidos)

## 7. Probar el login

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -d "username=admin@marinilla.gov.co&password=unaClaveSegura123"
```

Te devuelve `{"accessToken": "...", "tokenType": "bearer"}`. Ese token
se envía en cada petición protegida como header:
`Authorization: Bearer <token>`.

## 8. Correr las pruebas

```bash
pytest
```

Incluye 17 pruebas: `/health`, login correcto e incorrecto, `/auth/me`,
el CRUD completo de `phones` verificando que las escrituras sin token
responden 401 (RNF-08), el flujo completo de `equipments` con sus
relaciones, cascadas de borrado a nivel de base de datos, y todos los
casos de error 422/409 corregidos en `CORRECCIONES-16-SEPT.md`.

Estas mismas pruebas corren automáticamente en GitHub Actions en cada
`push`/`pull request` (ver `.github/workflows/tests.yml`).

## 9. Estructura del proyecto (por capas, RNF-04)

```
app/
  core/
    config.py     -> variables de entorno (Settings)
    security.py   -> hash de password + JWT
    deps.py       -> get_current_admin (protección de rutas)
  models/         -> tablas SQLAlchemy (una por archivo, agrupadas por dominio)
  schemas/        -> validación/forma de datos con Pydantic (camelCase)
  routers/        -> endpoints HTTP (auth, phones, health...)
  scripts/
    create_admin.py
  main.py         -> arma la app, CORS, incluye los routers
alembic/          -> migraciones versionadas
tests/            -> pruebas automatizadas
```

## 10. Estado del CRUD de las 6 entidades (HU-06)

Ya está implementado el patrón completo (lectura pública, escritura
protegida) para las 6 entidades, más `equipments` con sus relaciones:

| Entidad | Endpoint | Router |
|---|---|---|
| Teléfonos | `/api/v1/phones` | `app/routers/phones.py` |
| Tipos de violencia | `/api/v1/violence-types` | `app/routers/violence_types.py` |
| Tipos de unidad (catálogo fino) | `/api/v1/equipment-types` | `app/routers/equipment_types.py` |
| Rutas de atención | `/api/v1/referrals` | `app/routers/referrals.py` |
| Festivos | `/api/v1/holidays` | `app/routers/holidays.py` |
| Unidades de atención | `/api/v1/equipments` | `app/routers/equipments.py` |

`app/routers/phones.py` sigue siendo el ejemplo más simple para
entender el patrón antes de leer `equipments.py` (que además maneja
listas hijas `phones[]`/`workingDates[]` y la relación N:M
`violenceTypes`).

`equipment_categories` (la taxonomía gruesa, FilterTag) **ya tiene** su
propio router CRUD (`app/routers/equipment_categories.py`, agregado en la
revisión del 16 de septiembre — punto D5), protegido igual que las demás
entidades administrables, en `/api/v1/equipment-categories`.

## 11. Antes de escribir más código: privacidad (sección 4 del documento)

- Ningún endpoint debe recibir datos del formulario de onboarding.
- No se guarda IP, geolocalización individual ni identificadores de
  dispositivo de las usuarias.
- El único dato "personal" del sistema es `admin_users`, con la
  contraseña siempre hasheada (ya implementado).

## 12. Despliegue con Docker (HU-13)

```bash
docker build -t mujer-marinilla-backend .
docker run -p 8000:8000 --env-file .env mujer-marinilla-backend
```

Antes de arrancar en producción, corre las migraciones apuntando a la
`DATABASE_URL` de producción: `alembic upgrade head`.
