# Tabla de equivalencias: TypeScript ↔ Base de datos ↔ API

Pedida en el punto 06 de la revisión técnica ("próximo entregable").
Cubre las 7 entidades del dominio (sección 8 del brief).

## Equipment / Unidad

| Campo TypeScript (frontend) | Columna BD | Tabla | Campo API (JSON) |
|---|---|---|---|
| `id` | `id` | equipments | `id` |
| `equipmentType` (enum fijo) | `category_id` (FK) | equipments → equipment_categories | `equipmentType` (label) + `equipmentCategorySlug` (slug) — **ver decisión abierta #4** |
| `type` (enum fijo) | `unit_type_id` (FK, nullable) | equipments → unit_types | `type` (abreviatura) |
| `name` | `name` | equipments | `name` |
| `abbreviation` | `abbreviation` | equipments | `abbreviation` |
| `openingTime` (string) | `opening_time` (Time) | equipments | `openingTime` (HH:MM:SS) |
| `closingTime` (string) | `closing_time` (Time) | equipments | `closingTime` |
| `phones[]` (string[]) | tabla hija | equipment_phones | `phones` (string[]) |
| `description` | `description` | equipments | `description` |
| `function` | `function` | equipments | `function` |
| `violenceTypes` (string libre) | relación N:M | equipment_violence_types → violence_types | `violenceTypes` (string[] de nombres) — **ver decisión abierta #1** |
| `address` | `address` | equipments | `address` |
| `neighborhood` | `neighborhood` | equipments | `neighborhood` |
| `notes` | `notes` | equipments | `notes` |
| `latitude` (number) | `latitude` (Numeric 9,6) | equipments | `latitude` (float) |
| `longitude` (number) | `longitude` (Numeric 9,6) | equipments | `longitude` (float) |
| `openingTimeSaturday` | `opening_time_saturday` | equipments | `openingTimeSaturday` |
| `closingTimeSaturday` | `closing_time_saturday` | equipments | `closingTimeSaturday` |
| `openingTimeSunday` | `opening_time_sunday` | equipments | `openingTimeSunday` |
| `closingTimeSunday` | `closing_time_sunday` | equipments | `closingTimeSunday` |
| `workingDates[]` (string[]) | tabla hija | equipment_working_dates | `workingDates` (date[], formato YYYY-MM-DD) — **ver decisión abierta #2** |
| `open_24` (0 \| 1) | `open_24h` (Boolean) | equipments | `open24` (true/false) — alias explícito, no el default de Pydantic |
| *(no existía)* | `is_active` (Boolean) | equipments | *(no se expone; controla el soft-delete)* |

## ViolenceType / Tipo de violencia

| TypeScript | Columna BD | Campo API |
|---|---|---|
| `id` | `id` (autoincrement, **no** se reutiliza el `id: 0` del frontend) | `id` |
| *(no existía)* | `code` (string único, no nulo, indexado) | `code` — **identificador estable, agregado en la revisión del 16-sept (D1)**: usar este campo para filtrar (`?code=`) en vez del `id`, que cambia al re-sembrar |
| `name` | `name` | `name` |
| `description` | `description` | `description` |
| `examples?: string[]` | `examples` (JSON) | `examples` |
| `image?` | `image` | `image` |

## Referral / Ruta de atención

| TypeScript | Columna BD | Campo API |
|---|---|---|
| `id` | `id` | `id` |
| *(no existía)* | `code` (string único, no nulo, indexado) | `code` — **identificador estable (D1)**, ver nota de ViolenceType arriba |
| `header` | `header` | `header` |
| `text` (ReactNode, en la práctica string) | `text` (Text, texto plano) | `text` — **ver decisión abierta #3** |
| `image?` | `image` | `image` |
| `name?` | `name` | `name` |
| `idTipoViolencia` | `violence_type_id` (FK, 1:N) | `violenceTypeId` — **ver decisión abierta #1**. Filtrable también por `?violenceTypeId=` en `GET /api/v1/referrals` |

## Phone / Línea telefónica (global)

| TypeScript | Columna BD | Campo API |
|---|---|---|
| `id` (= el número, ej. `190`) | `id` (autoincrement, **no** se reutiliza el número como id) | `id` |
| *(no existía)* | `code` (string único, no nulo, indexado) | `code` — **identificador estable (D1)**, ver nota de ViolenceType arriba (ej. `"policia"`, `"linea-orientacion-mujer"`) |
| `number` | `number` | `number` |
| `title` | `title` | `title` |
| `description` | `description` | `description` |

## EquipmentType (frontend) → unit_types (BD)

| TypeScript | Columna BD | Campo API |
|---|---|---|
| `id` | `id` | `id` |
| `abbreviation` | `abbreviation` | `abbreviation` |
| `name` | `name` | `name` |
| `description` | `description` | `description` |

## Holiday / Festivo

| TypeScript (no existía como entidad, era función `isHoliday()`) | Columna BD | Campo API |
|---|---|---|
| — | `date` (Date, unique) | `date` |
| — | `name` | `name` |

## Filtros agregados en la revisión del 16-sept (D3)

`GET /api/v1/equipments` ahora acepta, además de `equipmentType` y `bbox`:

- `type` (string): filtra por la **abreviatura** del tipo de unidad
  (`unit_types.abbreviation`), sin excluir unidades que no tienen tipo
  asignado.

## Notas generales de la tabla

- **Todas** las respuestas usan camelCase (`alias_generator=to_camel` en `app/schemas/base.py::CamelModel`), aunque la BD sea snake_case (RF11).
- Los **ids no se reutilizan** de los datos originales del frontend (ni el `id: 190` de phones ni el `id: 0` de violenceTypes): son autoincrement de la BD. El seed (`app/scripts/seed.py`) mapea el id viejo al nuevo internamente para resolver las relaciones (ej. `referrals.idTipoViolencia` → `violence_type_id`), pero el cliente/frontend debe consumir los ids que devuelve la API, no los que tenía el archivo `.ts` original.
- `updated_by_admin_id` existe en **todas** las tablas editables por admin (equipment_categories, unit_types, equipments, violence_types, referrals, phones, holidays), no solo en equipments, atendiendo el punto 05 de la revisión.
