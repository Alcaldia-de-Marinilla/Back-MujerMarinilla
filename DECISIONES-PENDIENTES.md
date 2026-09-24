# Decisiones pendientes (NO tomarlas sin confirmar con la Alcaldía / equipo de frontend)

Este documento existe porque la revisión técnica del 27 de agosto de 2026
identificó 4 decisiones que el equipo de practicantes **no debe tomar solo**.
El código ya tiene un comportamiento por defecto para poder seguir
desarrollando, pero está señalado con comentarios `DECISIÓN ABIERTA` en
cada archivo relevante. **No cambiar el comportamiento por defecto sin
que alguien confirme la respuesta correcta.**

---

## 1. ¿`referrals` puede aplicar a varios tipos de violencia?

**Pregunta:** ¿Un mismo referral puede aplicar a varios `violenceTypes`?
En los datos actuales hay uno llamado *"Violencia Moral y Psicológica"*
con un único `idTipoViolencia`.

**Estado actual del código:** modelado como **1:N** (`referrals.violence_type_id`
es una sola llave foránea obligatoria). El caso "Violencia Moral y
Psicológica" hoy solo puede apuntar a uno de los dos tipos.

**Dónde está señalado:** `app/models/content.py`, docstring de la clase `Referral`.

**Si la respuesta es "sí, puede aplicar a varios":** hay que crear una tabla
puente `referral_violence_types` (igual patrón que `equipment_violence_types`),
migrar `referrals.violence_type_id` a la nueva tabla, y actualizar
`app/schemas/referral.py` + `app/routers/referrals.py` para aceptar
`violenceTypeIds: list[int]` en vez de `violenceTypeId: int`.

---

## 2. ¿Qué significan las fechas de `equipment_working_dates`?

**Pregunta:** ¿Son fechas en que la unidad SÍ abre (excepción al horario
normal) o fechas en que CIERRA?

**Estado actual del código:** la tabla solo guarda la fecha, sin
interpretar su significado. **No se ha construido ninguna lógica de
"¿está abierto ahora?"** que dependa de esto (esa lógica también debe
combinarse con `holidays`, según el propio documento de requisitos).

**Dónde está señalado:** `app/models/equipment.py`, docstring de la clase
`EquipmentWorkingDate`.

**Importante:** ninguna unidad de los datos sembrados (`equipments.json`)
trae `workingDates`, así que el seed no se ve afectado por esta decisión
todavía. Pero **antes de programar el cálculo de disponibilidad en tiempo
real**, hay que confirmar el significado.

---

## 3. ¿`referrals.text` es texto plano, Markdown o HTML?

**Pregunta:** el campo `text` de la ruta de atención, ¿viene como texto
plano, Markdown o HTML desde el panel de administración?

**Estado actual del código:** modelado como `Text` (texto plano), sin
ningún sanitizado especial. Los 12 registros sembrados desde
`encaminhamento.ts` son texto plano.

**Dónde está señalado:** `app/models/content.py`, docstring de la clase `Referral`.

**Si la respuesta es HTML:** hay que sanitizar el contenido al guardarlo
(por ejemplo con `bleach` o similar) antes de persistirlo, porque vendría
de un formulario de administración y podría ser un vector de XSS para las
usuarias que después leen ese contenido en el frontend.

**Si la respuesta es Markdown:** no requiere sanitizado en el backend,
pero el frontend necesita una librería de renderizado (ej. `react-markdown`).

---

## 4. ¿La API devuelve el `slug` o el `label` de la categoría?

**Pregunta:** ¿el frontend debe recibir `salud` (slug, para lógica interna)
o `"Unidad de Salud"` (label, el texto que ve la usuaria)?

**Estado actual del código:** para no bloquear el desarrollo, la API
**expone ambos** en cada unidad:
- `equipmentType`: el label (`"Unidad de Salud"`, `"Servicios especializados
  para la Mujer"`, `"Estación de Policía"`) — mantiene compatibilidad con
  el frontend actual, que ya usaba este texto en el enum `FilterTag`.
- `equipmentCategorySlug`: el slug (`salud`, `servicios-mujer`, `policia`).

**Dónde está señalado:** `app/models/catalogs.py`, docstring de la clase
`EquipmentCategory`.

**Esta decisión es la de menor riesgo de las 4** (exponer ambos campos no
rompe nada), pero igual debe confirmarse cuál es el campo "oficial" que
usará el frontend en su lógica de filtros, para no mantener duplicidad
innecesaria a largo plazo.

---

## Resumen para la reunión con la Alcaldía / frontend

| # | Decisión | Riesgo de no resolverla ahora | Bloquea a corto plazo |
|---|---|---|---|
| 1 | referrals 1:N vs N:M con violence_types | Medio (ya hay un caso real en los datos) | No bloquea Sprint 1-2 |
| 2 | Significado de equipment_working_dates | Bajo (sin datos sembrados todavía) | Sí, antes de HU de "abierto ahora" |
| 3 | Formato de referrals.text (plano/MD/HTML) | Medio (seguridad si es HTML) | No bloquea Sprint 1-2 |
| 4 | slug vs label en categorías | Bajo (ya se exponen ambos) | No bloquea nada |
